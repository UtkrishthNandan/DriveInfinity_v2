import io
import math
import asyncio
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends, Query, Security
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client
from pyrogram.errors import FloodWait
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

# --- CONFIGURATION ---
# Now we use os.getenv() to pull the secrets securely
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017") # Provides a fallback
CHUNK_SIZE = 20 * 1024 * 1024     

# --- SECURITY CONFIGURATION ---
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "default_insecure_password")
# We expect the password to be sent in the 'Authorization' header
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def verify_password(auth_header: str = Security(api_key_header)):
    """The Bouncer: Checks if the incoming request has the correct password."""
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing password")
    
    # Strip 'Bearer ' if the frontend sends it that way
    token = auth_header.replace("Bearer ", "")
    
    if token != MASTER_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid password")
    return True

# --- INITIALIZATION ---
app = FastAPI(title="DriveInfinity Backend")

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to ["https://driveinfinity.us.kg"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Telegram Client (Pyrogram)
tg_client = Client(
    "driveinfinity_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize MongoDB
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["driveinfinity"]
files_collection = db["files"]
chunks_collection = db["chunks"]

# --- LIFECYCLE EVENTS ---
@app.on_event("startup")
async def startup_event():
    await tg_client.start()

@app.on_event("shutdown")
async def shutdown_event():
    await tg_client.stop()

# --- FRONTEND ROUTING ---
# Tell FastAPI where the static folder is
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the index.html file when users visit the root domain
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

# --- ENDPOINTS ---

@app.post("/api/upload", dependencies=[Depends(verify_password)])
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Handles incoming file, chunks it, pushes to Telegram, and handles cancellation."""
    
    file_id = str(ObjectId())
    total_size = 0
    chunk_index = 0
    uploaded_message_ids = [] # Track what we upload in case we need to delete it
    
    try:
        # Read the incoming stream in 20MiB chunks
        while True:
            # 1. Check if the user clicked 'Cancel' or closed the tab
            if await request.is_disconnected():
                raise Exception("Client disconnected mid-upload.")
                
            chunk_bytes = await file.read(CHUNK_SIZE)
            if not chunk_bytes:
                break # End of file reached
                
            chunk_size = len(chunk_bytes)
            total_size += chunk_size
            
            byte_stream = io.BytesIO(chunk_bytes)
            byte_stream.name = f"chunk_{chunk_index}.bin" 
            
            success = False
            while not success:
                try:
                    msg = await tg_client.send_document(
                        chat_id=CHANNEL_ID,
                        document=byte_stream,
                        file_name=byte_stream.name
                    )
                    
                    # Track for potential cleanup
                    uploaded_message_ids.append(msg.id)
                    
                    await chunks_collection.insert_one({
                        "file_id": file_id,
                        "chunk_index": chunk_index,
                        "telegram_message_id": msg.id
                    })
                    
                    success = True
                    chunk_index += 1
                    
                except FloodWait as e:
                    print(f"Rate limited. Sleeping for {e.value} seconds...")
                    await asyncio.sleep(e.value)

        # 2. If we reach here, upload finished successfully
        await files_collection.insert_one({
            "_id": file_id,
            "filename": file.filename,
            "total_size": total_size,
            "total_chunks": chunk_index,
            "upload_date": datetime.utcnow()
        })
        
        return {"message": "Upload successful", "file_id": file_id, "filename": file.filename}

    except Exception as e:
        # 3. THE CLEANUP ROUTINE
        print(f"Upload aborted/failed: {e}. Initiating cleanup...")
        if uploaded_message_ids:
            try:
                await tg_client.delete_messages(chat_id=CHANNEL_ID, message_ids=uploaded_message_ids)
            except Exception as cleanup_err:
                print(f"Failed to clean up Telegram chunks: {cleanup_err}")
                
        await chunks_collection.delete_many({"file_id": file_id})
        raise HTTPException(status_code=400, detail="Upload cancelled and cleaned up.")

@app.get("/api/files", dependencies=[Depends(verify_password)])
async def list_files():
    """Returns all uploaded files."""
    files = await files_collection.find().to_list(100)
    # Format ObjectId to string for JSON serialization
    for f in files:
        f["_id"] = str(f["_id"])
    return files


@app.get("/api/download/{file_id}")
async def download_file(file_id: str, pwd: str = Query(None)):
    """Streams the file. Secured via query parameter for browser compatibility."""
    if pwd != MASTER_PASSWORD:
        raise HTTPException(status_code=403, detail="Unauthorized download attempt")
    
    # Verify file exists
    file_record = await files_collection.find_one({"_id": file_id})
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    # Get chunks sorted by index
    cursor = chunks_collection.find({"file_id": file_id}).sort("chunk_index", 1)
    chunks = await cursor.to_list(length=None)
    
    async def file_generator():
        for chunk in chunks:
            msg_id = chunk["telegram_message_id"]
            
            try:
                # 1. Fetch the actual Message object from Telegram using the ID
                msg = await tg_client.get_messages(
                    chat_id=CHANNEL_ID, 
                    message_ids=msg_id
                )
                
                # 2. Pass the full Message object to the streamer
                async for chunk_data in tg_client.stream_media(message=msg):
                    yield chunk_data
                    
            except FloodWait as e:
                # If streaming triggers a floodwait, yield control and wait
                print(f"Rate limited during download. Sleeping for {e.value} seconds...")
                await asyncio.sleep(e.value)
            except Exception as e:
                print(f"Server error during streaming: {e}")
                break # Stop the generator if a critical error occurs
    
    return StreamingResponse(
        file_generator(), 
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_record["filename"]}"'}
    )

@app.delete("/api/delete/{file_id}", dependencies=[Depends(verify_password)])
async def delete_file(file_id: str):
    """Deletes a file from MongoDB and its corresponding chunks from Telegram."""
    
    # 1. Find the file to make sure it exists
    file_record = await files_collection.find_one({"_id": file_id})
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    # 2. Get all chunk records associated with this file
    cursor = chunks_collection.find({"file_id": file_id})
    chunks = await cursor.to_list(length=None)
    
    # Extract all the Telegram message IDs
    message_ids = [chunk["telegram_message_id"] for chunk in chunks]
    
    # 3. Delete the blocks from the Telegram Channel
    if message_ids:
        try:
            # Pyrogram allows deleting multiple messages at once by passing a list
            await tg_client.delete_messages(
                chat_id=CHANNEL_ID,
                message_ids=message_ids
            )
        except FloodWait as e:
            print(f"Rate limited during deletion. Sleeping for {e.value} seconds...")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Failed to delete chunks from Telegram: {e}")
            # We continue anyway to clear out our database state
            
    # 4. Wipe the metadata records from MongoDB
    await chunks_collection.delete_many({"file_id": file_id})
    await files_collection.delete_one({"_id": file_id})
    
    return {"message": f"File '{file_record['filename']}' successfully deleted everywhere."}