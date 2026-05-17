# **DriveInfinity**

DriveInfinity is a secure, single-tenant, cost-optimized personal cloud storage vault designed to leverage alternative cloud infrastructure for theoretically infinite data storage. By using a headless messaging platform (Telegram) as a high-density binary object store and coordinating it via a non-blocking FastAPI backend and a MongoDB Atlas metadata ledger, DriveInfinity bypasses standard cloud storage tier fees while maintaining strict access controls.

## **1\. System Overview & Core Philosophy**

Traditional cloud storage (e.g., AWS S3, Google Cloud Storage) charges recurring fees based on data volume. DriveInfinity shifts this paradigm by decoupling the **Storage Layer** from the **Metadata Layer**.

* **Object Storage Layer (Telegram MTProto):** Large binary assets are programmatically fragmented, dispatched, and reconstructed using Telegram’s secure, high-bandwidth CDN network.  
* **Metadata Layer (MongoDB Atlas):** An asynchronous NoSQL database tracks individual file schemas, piece sequences, hashes, and upload timestamps, keeping the server itself stateless and lightweight.

### **Target Features**

* **Zero-Cost Storage Pool:** Direct integration with private Telegram channels, converting raw messaging lines into an unthrottled object storage drive.  
* **Cryptographic Vault Door:** API-level bearer tokens and secure URL queries prevent any unauthorized public traffic from querying your server or writing payloads.  
* **Non-Blocking Streaming Pipe:** Files are streamed dynamically. Downloading a file live-pipes chunks straight from Telegram's servers through the VPS memory buffers to the client, preserving server disk lifespan and preventing SSD degradation.  
* **Precision Client Dashboard:** A modern, single-page UI utilizing raw XMLHttpRequest callbacks to enable true progress percentages, precise upload speed calculations, dynamic ETA readouts, and immediate upload cancellation.  
* **Timezone Localization:** Native sync with Indian Standard Time (IST) for accurate database transaction history.

## **2\. Core Technology Stack & Engineering Rationales**

| Component | Selected Technology | Engineering Justification |
| :---- | :---- | :---- |
| **Frontend** | Vanilla HTML5 / Tailwind CSS / ES6 JavaScript | Eliminates the bundle and compilation overhead of heavy reactive frameworks (React/Vue). Vanilla JS grants unabstracted control over binary streams and native browser network buffers. |
| **Backend** | FastAPI / Uvicorn (Python 3.12+) | ASGI compliance ensures a fully non-blocking architecture, permitting high-throughput multi-gigabyte uploads and live-streams without thread starvation. |
| **Database** | MongoDB Atlas (Motor Driver) | Stores file-to-chunk schemas dynamically. BSON document stores easily map variable list structures without the cost of complex relational joins. |
| **Hosting** | Vultr Cloud Compute (Ubuntu 24.04 LTS) | Low-latency compute instances positioned close to regional entry points to optimize streaming performance. |
| **Web Server** | Nginx Reverse Proxy | Handles secure SSL/TLS termination, automated HTTP-to-HTTPS upgrades, and overrides default HTTP payload limits. |

## **3\. System Architecture & High-Level Data Flows**

The system architecture cleanly separates public requests from internal processing streams:

┌────────────────────────────────────────────────────────┐  
│                      FRONTEND                          │  
│        Vanilla HTML5 / Tailwind CSS / ES6 JS           │  
└──────────────────────────┬─────────────────────────────┘  
                           │ HTTPS (Port 443\)  
                           ▼  
┌────────────────────────────────────────────────────────┐  
│                     WEB SERVER                         │  
│             Nginx Reverse Proxy / SSL                  │  
└──────────────────────────┬─────────────────────────────┘  
                           │ Local Socket (Port 8000\)  
                           ▼  
┌────────────────────────────────────────────────────────┐  
│                   BACKEND ENGINE                       │  
│           FastAPI / ASGI / Uvicorn Server              │  
└──────────────────────────┬─────────────────────────────┘  
                           │  
             ┌─────────────┴─────────────┐  
             ▼                           ▼  
┌─────────────────────────┐ ┌─────────────────────────┐  
│     METADATA LEDGER     │ │     OBJECT STORAGE      │  
│   MongoDB Atlas / Motor │ │  Telegram MTProto API   │  
└─────────────────────────┘ └─────────────────────────┘

### **Mathematical Segmentation Model**

To bypass Telegram MTProto's file limits, files are programmatically split into ![][image1] sequentially indexed chunks (![][image2]). A given file ![][image3] is defined as the ordered union of its parts:

![][image4]The number of chunks ![][image1] is calculated based on the total file size ![][image5] and the target chunk payload size ![][image6] (![][image7] depending on MTProto configurations):

![][image8]Each chunk ![][image2] yields an MTProto storage identifier ![][image9] and a message sequence ID ![][image10]. This mapping is saved as an array of JSON objects inside the database schema to facilitate reassembly.

## **4\. Directory Structure Diagram**

Below is the directory structure representing the finalized production workspace of your Vultr deployment:

/opt/driveinfinity/                      \# Production Root: The primary deployment environment for the DriveInfinity application.  
├── .env                                 \# Configuration: Environment secrets including API credentials, MongoDB URIs, and the Master Password.  
├── main.py                              \# Backend Controller: ASGI FastAPI script handling authorization, metadata ledgers, and MTProto streams.  
├── static/                              \# Public Directory: Contains front-end assets served directly to client browsers.  
│   └── index.html                       \# Frontend View: Single-page application controlling UI logic, local timezone parsing, and upload states.  
└── venv/                                \# Isolated Environment: System-segregated virtual workspace housing runtime dependencies.  
    ├── bin/                             \# Executable Binaries: Binary runners tied strictly to the isolated virtual space.  
    │   ├── activate                     \# Context Switcher: Script to activate the virtual environment within an active shell session.  
    │   ├── pip                          \# Dependency Installer: Locally scoped package manager routing installations into the venv path.  
    │   ├── python3                      \# Local Interpreter: Python runtime linked specifically to virtual environment libraries.  
    │   └── uvicorn                      \# Web Server Runner: Server binary executing FastAPI on port 8000\.  
    └── lib/python3.12/site-packages/    \# Third-Party Libraries: Compiled modules (Pyrogram, Motor, FastAPI) utilized by the application.

/etc/                                    \# System Configurations: Operating system directories managing external services.  
├── nginx/                               \# Web Server Management: Configuration tree for routing internet traffic.  
│   ├── sites-available/  
│   │   └── driveinfinity                \# Reverse Proxy Blueprint: Server block defining port routing, SSL/TLS, and payload limits.  
│   └── sites-enabled/  
│       └── driveinfinity                \# Active Symlink: Symbolic shortcut confirming the reverse proxy configuration is active.  
│  
└── systemd/system/                      \# Daemon Manager: Linux init configurations controlling persistent execution.  
    └── driveinfinity.service            \# Systemd Service Block: Script instructing the OS to run Uvicorn 24/7 and auto-recover on failure.

## **5\. Database Schema & API Specifications**

### **MongoDB Schema (files collection)**

{  
  "\_id": { "$oid": "664723da8a9d123456789abc" },  
  "filename": "backup\_archive.zip",  
  "size": 524288000,  
  "mime\_type": "application/zip",  
  "upload\_date": "2026-05-17T09:54:02Z",  
  "chunks": \[  
    {  
      "chunk\_index": 0,  
      "tg\_message\_id": 1421,  
      "tg\_file\_id": "BQACAgIAAx0C...rest\_of\_telegram\_file\_id...",  
      "size": 52428800  
    }  
  \]  
}

### **API Endpoint Matrix**

| Method | Endpoint | Authorization | Request Payload | Response (200 OK) |
| :---- | :---- | :---- | :---- | :---- |
| **POST** | /api/verify | None (Credentials Check) | **JSON:** { "password": "..." } | { "success": true } |
| **GET** | /api/files | Bearer Token | None | **JSON Array of File Metadata Documents** |
| **POST** | /api/upload | Bearer Token | **Multipart Form:** file (Binary Stream) | { "success": true, "file\_id": "..." } |
| **GET** | /api/download/{id} | Query String (?pwd=) | None | **Binary Stream (application/octet-stream)** |
| **DELETE** | /api/files/{id} | Bearer Token | None | { "success": true } |

## **6\. Setup & Deployment Guide**

### **Local Development Quickstart**

1. **Verify Prerequisites:** Ensure Python 3.12+ and MongoDB are installed on your workstation.  
2. **Clone the Directory Structure:**  
   mkdir DriveInfinity && cd DriveInfinity

3. **Build Virtual Environment & Install Dependencies:**  
   python3 \-m venv venv  
   source venv/bin/activate  
   pip install fastapi uvicorn pyrogram motor python-multipart tgcrypto python-dotenv

4. **Configure Environment:** Create a .env file in the root folder with your Telegram credentials (API\_ID, API\_HASH, BOT\_TOKEN, TG\_CHANNEL\_ID), your MONGO\_URI, and your MASTER\_PASSWORD.  
5. **Start Dev Server:**  
   uvicorn main:app \--reload \--host 127.0.0.1 \--port 8000

### **Production Deployment to Vultr VPS**

#### **Step 1: Firewall Configuration**

Connect via SSH and configure UFW to secure the instance while whitelisting web traffic:

ufw allow OpenSSH  
ufw allow 80/tcp  
ufw allow 443/tcp  
ufw enable

#### **Step 2: Establish Virtual Environment**

To bypass Ubuntu 24.04 PEP 668 limits, construct your localized virtual workspace inside /opt/driveinfinity/:

cd /opt/driveinfinity  
python3 \-m venv venv  
source venv/bin/activate  
pip install fastapi uvicorn pyrogram motor python-multipart tgcrypto python-dotenv

#### **Step 3: Setup Systemd Service Daemon**

1. Create a service configuration file:  
   nano /etc/systemd/system/driveinfinity.service

2. Paste the following daemon settings:  
   \[Unit\]  
   Description=DriveInfinity FastAPI Backend  
   After=network.target

   \[Service\]  
   User=root  
   WorkingDirectory=/opt/driveinfinity  
   ExecStart=/opt/driveinfinity/venv/bin/uvicorn main:app \--host 127.0.0.1 \--port 8000  
   Restart=always

   \[Install\]  
   WantedBy=multi-user.target

3. Initialize and enable the daemon:  
   systemctl daemon-reload  
   systemctl start driveinfinity  
   systemctl enable driveinfinity

#### **Step 4: Configure Nginx Reverse Proxy**

1. Install Nginx:  
   apt update && apt install nginx \-y

2. Create a server block at /etc/nginx/sites-available/driveinfinity:  
   server {  
       listen 80;  
       server\_name driveinfinity.us.kg www.driveinfinity.us.kg;

       client\_max\_body\_size 2000M; 

       location / {  
           proxy\_pass \[http://127.0.0.1:8000\](http://127.0.0.1:8000);  
           proxy\_set\_header Host $host;  
           proxy\_set\_header X-Real-IP $remote\_addr;  
           proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;  
           proxy\_set\_header X-Forwarded-Proto $scheme;  
       }  
   }

3. Enable and restart the reverse proxy:  
   ln \-s /etc/nginx/sites-available/driveinfinity /etc/nginx/sites-enabled/  
   nginx \-t  
   systemctl restart nginx

#### **Step 5: Install HTTPS SSL Certificates via Certbot**

1. Install Certbot and its Nginx integration engine:  
   apt install certbot python3-certbot-nginx \-y

2. Provison a Let's Encrypt certificate:  
   certbot \--nginx \-d driveinfinity.us.kg \-d www.driveinfinity.us.kg

   *Follow the terminal prompts and opt to automatically redirect all HTTP traffic to HTTPS.*

## **7\. AI-Driven Development Log & Changelog**

### **Phase 1: The Initial Proof of Concept**

* **Milestone:** Created a rudimentary pipeline showing that binary segments could be streamed to and from Telegram chats on local host networks using simple endpoints.  
* **Limitations:** The interface remained entirely insecure; the database lacked structuring coordinates; and any file transfer over 1 Megabyte would crash the network block.

### **Phase 2: Major Hurdles & Resolution Strategies**

#### **1\. Security Risk on Public Ports**

* **Hurdle:** Deploying the basic PoC to the public web exposed full upload/delete operations to automated scan scripts.  
* **The Fix:** Transitioned to a "Personal Vault" architecture. Implemented authorization checks on every backend route, forcing standard REST actions to carry custom bearer header values. Downloads now construct short-lived, encrypted, tokenized URL parameters.

#### **2\. Timezone Offset Mismatch (IST vs. UTC)**

* **Hurdle:** Date entries written natively to MongoDB Atlas displayed differently depending on the client location, leading to skewed timestamps for users in India.  
* **The Fix:** Structured the frontend ingestion engine to append a strict "Z" ISO UTC suffix to incoming timestamp strings. We then invoked .toLocaleString("en-IN", { timeZone: "Asia/Kolkata" }) to format all listings cleanly in IST.

#### **3\. DNS Routing Barriers on DigitalPlat**

* **Hurdle:** The registrar offered no configuration portal to configure standard A Records or assign IPs directly.  
* **The Fix:** Delegated DNS authority downstream to Vultr by setting the domain nameservers directly to ns1.vultr.com and ns2.vultr.com. We then constructed the necessary zone files within Vultr's administrative dashboards to route global traffic directly to our static server IP.

#### **4\. PEP 668 & Directory Structure Conflicts**

* **Hurdle:** The background runner repeatedly exited with status=203/EXEC and status=1/FAILURE codes. Furthermore, trying to install Python packages globally triggered Ubuntu 24.04’s new PEP 668 protection shield.  
* **The Fix:** Discovered that SCP operations had nested the project code inside /opt/driveinfinity/DriveInfinity\_v2. We flattened the directory structure to place main.py directly under /opt/driveinfinity. We then constructed a clean virtual environment using python3 \-m venv venv to cleanly isolate dependencies away from core OS modules, resolving the daemon failure.

## **8\. Technical Limits, Trade-offs & Operational Risks**

*An honest assessment of system limits to ensure stable administration.*

1. **Telegram TOS Dependency:** Utilizing a free messaging channel as a headless storage disk exists in a legal grey area. Generating excessive network traffic or hosting copyrighted materials may trigger automated sweeps, resulting in channel termination. This project is strictly intended for **personal, non-commercial backups**.  
2. **API Rate-Limiting Constraints:** Telegram MTProto endpoints enforce strict limits on repeated uploads or downloads. Generating intense request spikes will trigger FloodWait exceptions. To prevent execution timeouts, ensure file uploads are paced sequentially.  
3. **RAM Limitations:** File chunks pass directly through the Vultr VPS's RAM buffers. Since this is a single-tenant environment designed for one active user, resource usage remains minimal. However, opening multiple massive streams concurrently on a 1GB RAM instance may trigger Linux out-of-memory (OOM) process termination.

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAYCAYAAADOMhxqAAAA2UlEQVR4XmNgGAWDCigrK4sBKWYYX0FBQQBdDAyUlJT45eXlt8jJyfkC6f9AfAaIl4HkpKWlhYHsc0B8Fa4BqNAFKLAcaGI6VMMekCEgOVFRUR4g/wAQP4RrAHI8oXgNEP8DavRAMkwJKPYcxQYYAAr+BuKtQA0cUCEWkM3ohsAByDlAE8uR+IpA/ASIrysqKooD5WJUVFTYYfIg034DBW1gAkh+aoUaMBlIMYIlgQqNgXg+XAAIgKbqAxW9BuL9QHwRJg4DzMbGxqzogiD/ABVLIvlrFNAGAAAdLzNIUwIiSwAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAYCAYAAAD6S912AAABbUlEQVR4Xu2Tv0vDQBiGG1RQUEQ0/miSJk2CQRCX/AkuTiLiIOjuJG4OzvoPiC7iLoibCE5SdNNVcHIUcdBurvp89ALpF7U2cx94oXfvd2/uvt5VKj00tm0P+74/k6bpQH5ejztCyD56QV/oA33WarVd13WH6vU6Q39OrykQBME0upUQWah9x3HG8e/F114B89VHKZadaD8Df+9fgRRdmuOd/9Uf/FX0rucLmLCm53nz2stjAht6vg36si6BhC1rrxSEHaJXehdqr2vY3SBhV+guSZIR7XfAYt0GG1lsm2XyVPoil7jNyBGG4SgLr1GqvQKmh09cnSntZchVouaYn/3aKxBF0aT8KSza1F6GtEV2mRsfoBt08dMjkCPNZq8ANdGJWfDGh7Z1fbVancA7Q0cMLe1nWEGLFULW/NZ77dNFAp48rWdql7RXCoK2CHyI49im9wva7xrpqfRRXhan2dF+GSyCxiq/tKRHeb4BFpFR45+7WOgAAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAaCAYAAABozQZiAAABCElEQVR4XmNgGOFAXl7eE4hnEcIKCgoTgVgBRbOMjIyunJxcCFB8I1DRfyB+COLDMJAfDZRbCaS/AvnGKJphACg5CaQZqGA+uhwIgAwFYkl0cQagBkGgxGmozdHo8iAAFN8NUocuDpKIhmo8DVMgJSUlAvKKoqKiOFRND6ouKIA5GYjnwMSAGj2A/OVAJguSUlSA7GQgewY0kGqA+COQXY6uHgUAFWkC8Vuozc+AGh4B6S9A/BvItkFXjwLksfhXVlbWFMi/AIxGaXT1KADmZJAhMDGQJlD8I6vDCoCaPsnjSwD4ALqTiQZKSkr8UM3rgPHKhS6PFQAVWwLxT6hGdOyJrn4UjDwAAGCMV/mWSANUAAAAAElFTkSuQmCC>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAABXCAYAAAC5txliAAAFAklEQVR4Xu3dT8gUZRwH8JVXw8gSzUV8/8zOrJKoYMJSYLxEB5EuXsRDUacudurQoUI61KG7lF3Ci4QE0k2sIBAhqYMgESgRCL7RSZAuGVGk/R7fWVkf1tU3dt53rc8Hfswzz++Z2fe9fZndmWm1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABgpKqq9pdluSefBwBgAuzcufORTqdzoyiKA3kPAIAJIbABADQswtYbUfNRb8Xuqghg3y0lgAlsAAANi8C1oyzLw+12e129vxABbF8MV8X20LCK3tTA8QIbAECTpqenN0XoulTvro7xse3btz9+16IRBDYAgIalq2sRus6lcbrKFvtHY/9ItmyoWPtDrL0V9Vt9VQ4AgHHr9Xpr0t2e/f0IXhtis2pgCQAAAAAAAAAAAAAA8H9W3+25kM/fTzquLMsT+TwAAGMmsAEATDiBDQBgwglsAAAjbNu27YkIPr9E/Z2qKIqfUw3MpTD1Sn7cODUd2Or/Mf0v16qqeja2W6LOxrEvx/aPfD0AwMSZnZ2dieBydVgwi7nLEeB6+fw4NRnYYs2vUTfy+aT+3DP5PADAxIlANh/B5a+oHXkv5r6NfjefH6emAltVVZ20Jv7+V/NeEr3rUR/k8wAAEydCy+cp2PT3U0Cbnp7eVPf2xmb1ncUNaCKwRe9g1M3ov5j3+qL/fdNhFABgLDqLX4f2A9tUjN9tLeNL2JsIbBHEvkr9bre7Pu8BADx06sD0Y4ScQ7E9G/V7vmaYzuKP90fWzMzMk637hL/688ca2Opz3rlqCADw0IrAs7YON8fTfrrBIMbn83VNajCwDb3ZoDbVGgiSVVXt7vV6awb6AACTIQLavs7ij+9v33CQAly73V6XrxumM+SKWl4rfIXtnoEteh/lcwAAEymCy5GoCxHcNuS9UVKw6z+zbVTFuS92u92n8uMHNRTYrqZ+Pt8XvdP5HADARElf/9UPkb0Woeed2G5Zqa8Emwhs6WaD6H8ZdTI9OLc/Xy4+LPdifz/GVf34jyv9OQAAMhGWbkZdz+dH2bx582N10Psw7w1KwS0C2f4Iau9HvZD3kzjHZ1HH8nkAAGoprKXQls+PUr+dIV1hO5z3lirOs1AUxXycc2PeAwCgdftryvdS+IrQtCvv3UusP52etRYh69G8t1RxrvPxNxzN5wEAqEVgSj8iSy+bP/Wgv6Orvw49mM//G+mu2HQTRT4PAMCAFNTqEHZr8CaBXPRfi/ozAtZPeQ8AgIZFEPu0Dm0LQ654pVdmPdcPdZ0hL6oHAGCZRBg7NRDM7qqqqp5v3edBvAAALIOiKA5EQPu4fvjulXQ36NatW+fydQAAAAAAAAAAAAAAwH9cVVW7l/DQ3C1RnzzoegAAllH9GquTaRzby1F78zUAAKygCGjfRB2pxxei3szXAAAwRhG4qtBJz1pL+zF+OsbnhtTXc3Nzz8R2oSiKt+tjz5VleeLuMwIAMFYRuPZEvRTh61LeG0ZgAwBYAXUIm5+dnd34AFfYzkQd7x+X3oCQnw8AgDGL4HUhwtpMt9tdn/dyEdBej/VfpHG6KhdBb1e+BgCAMWu32+siiK3N50eYqqpqfz4JAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMBD6R8N104xj+UXDAAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA0AAAAZCAYAAADqrKTxAAABMElEQVR4Xu2Su0oDQRSGZ4mFIEK6RfZOiiW22pjGKtHGRuxs0qQLBHwCH0FSio2IENL7BEIai/TBJmBloVUsBC/fWXfJ7IlpBSE//Mzuf5k5s6wx/xdRFG3FcVwt3tM03WRxrMgcnuf5FIbwCb7AR8r7rLfYazpvgiDYxXwmdJFLDs8HosEzO5sB8xxjFobhjvbQjnzf90qizEvhXkaS8Uqm+SkZPZpcGk7hFye2jbowet1+z0BwHeNOSjnH3K+GVdHZBTDGNhxQerc2+EBr6uxvcAj2KMzy4pUOZONpTUC4KyX8a+0VX2cBoucn9UuGfO5lJcKn8JOTDrVxDF9hQ+k3hCdJkkS2Xph9TuqwvsEHeCl3YB2xxjovqGDuyYPruhvs2pKR2OTELPujV/hrfAP1JkbfuGiROQAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAaCAYAAABozQZiAAABCklEQVR4XmNgGOFAXl7eE4hnAfFcIL4gJyf3CMoGiYExUCwfXR8YACU1gZIhQHopEP8H4ocgPgwD+ZOA+BcQe6PrhQOoIpDmOehyCgoKHkDx28rKyrLocgyioqI8QMkDUM3R6PJAFxhD5TzR5RhkZWX9oJKngQoF0aQZgeJTgLafkpaWFkaTAzu5FZeTZWRkVIDiz4CG+qLL4XMyM9BFtkCx60D8EUkcAYAmKgEln0M1v4JG1RMg/gvET4H8MhUVFT50fWCA5N+rUlJSIujyeAHMycAASUeXIwigTv4GdIEpuhxBQLaTgU7lgGreBgp1dHmsQFFRUR+o4RNUIzLeIy4uzo2ufhSMPAAAMJNU8oVwC0sAAAAASUVORK5CYII=>

[image7]: <data:image/png;base64,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>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAABLCAYAAADNo9uCAAAEB0lEQVR4Xu3dv4scZRjA8TsSIaKoEM8jt7O3M3unYuOvQ0XQTkELLWwUtBAFtRACFgZjnT/AK23EXgsJJxYWgpWtGCJCQIMiBFQsPBDR9XnJLgwve7szvK4k8PnAy+w8+2yw/LLe7q6tAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAwHWoruuvt7e3L7dPvtPXvH8zZm/kewAAdDAajf6IoHomnx9ld3f3lth/O153GOfbqqpujBi7P86JfHcm9n6I15zJ5wAAdNA32GL/SsTZJ3E91TTNfXH9Ztm7coINAKBAn2CL3fODweBkNjsb5+f2LCfYAAAK9Ay2P+fMnotzkM/bBBsAQIGewTap6/qd8Xh8a/7cIoINAKBAz2B7M0Vb++zt7d2Q7+UEGwBAgT7BlsT+q7H/1SzY6rp+Kt/JCTYAgAJdgm361R2P5PN47bmYf5jPc4INAKBAl2CL5x+LvU/nzM/E/K18nhNsAAAFugRb7HwU52J71jTNwzH7LR6ut+fzCDYAgAIdg+1S+nu19CsH2ezz9t5RBBsAQIEuwdY0zb3pOh6P74r9/dh/Kd9ZRLABABToEmylBBsAQAHBBgCwRPpfjOlrM9LjiJrTcf9+/nudqyTYAAAWSJ+0jJB5ra7r9+K8HGHzSlxfiOvFiLYq318FwQYAcISqqgYRMueHw+FDeaDF/WRBRB3b2dm5I3ZOLTv5C+cRbAAAR9jc3LwpQuaBuq5fj+u52TzuT8T9YQq59v6qLAq2eO7dPid//cxIsAEA17OImQsRM+PZ/TTg9ts7Ge+wAQD8nyJmDtO7aulx+vBBhM1nMXs0bo83TXN3tr42HA4fj+cvxd7lZSd/7TyCDQBgsfWImX9mN9tXf7Pzr3h4LH0QobW3MoINAGCJjY2Nm7NRirXbstnKdA22+G96PnZ/jTOJc2X2Lt70/ve1Bb8pKtgAAAp0DbYkdl+Mc2Fra+v21uzBFHDD4fDZ9m6bYAMAKNAz2L5MH4poz6afaj2I80V73ibYAAAK9Ay2X9Lf2bVn0++T+z7mH7TnbYINAKBAz2CbxOV4e1bX9Xcx/3vN37ABAKxG12BLH45IwTaafsdbVVV3xvVsnJ/i9U/m+22CDQCgQNdgSx8qiN0f83kXgg0AoEDXYIu9/TgH+bwLwQYAUKBLsMXOPaOrHzh4In+uC8EGAFBgSbCtDwaDk7HzcZxJVVW7aZYvLSPYAAAKLAq2eO7pFGrt0zTNZr63jGADACiwKNj+K4INAKCAYAMAuMYJNgCAa5xgAwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVuNfCnZDjZFa528AAAAASUVORK5CYII=>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAaCAYAAACHD21cAAABEElEQVR4XuWSvWoCQRSFXWIwraDNwv7BNgHBYgufIY2IWJnCMr6IdSSkClqKjZa2Ym9t5TPYCNb6XRllctkxkjI5cNidOfPtnFmmUPhniuO4F0XRGH9ZlnFXr/0mwEYYhh0WTvCRcV/GSZJEem2ugEYC8urpzCl2KAOtDXi/AF4FElhnNwXwYcCRzpyya8rOOneKxc94h/f8ybrOnbLPJ7ur2Mtt8euaUk0q4gMfyXTulFVz4/t+5TKfZdkjcwO8xDObOYvJuQHnaZqWLvNy5bh6rSAImmRbG3gxgPbK5G1pwHOKP6/gPWLHN6A1TaoMizrPFdAT0AIPqFvT+S15wEPAMed91+FP8syFeNDBX9YJ8bNNZKW9230AAAAASUVORK5CYII=>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAZCAYAAAArK+5dAAACBklEQVR4Xu2UT2sTURTFMyRYRaUWHAaSSSYZAqHRhSJ15TILRRQp6aofoMtCEAQ/Q6EiwYWkVBERpdCCuBC600XBjZvgQgIiAVddRrCC7e+QN/HxTEKFgC5y4DAz95x77/s3L5Wa4r9CFEXz8BHcKxQKX3luFIvFc64vQRzHs+hPjfcjbPJddH0DZLPZ8+h3SFjFfAj31dT1GXhod+GBvOTUed4MguC0a/wDGO/D5ybxlqsLaI/Rlnj2YNfVR4IZnCThNXxoGtxzPcBTcbwr8sA3rmEkcrlcSMIebJjklusplUpXy+XyDE02xwxiODDXSNrW0iSj06wS3ff9M2hPtF9obfiT72t2jZEwy6PiNRjz/g12NSvpxC5oRmEYnrJmuIWUcUoNhyn6jgI5a4Q94ldM0ZaayKvCaqB9cMrodC07sT7y+fxtxFe8ZnTceN9VES2XCtnFiH+B38lZsEpofwLin+3YAFH/5DSSb/1EaqAYfKb1t7y/YFszTWJjUalUzjLSt/aG6XSYBmvwsu03M9vk1bPjo5BmtC9J6jDliymTZE6URrpreT28l4j9kG5567oFzDL/XqKof//oStBIE763tE8699Vq9QRFdhxfwhtw0RyMF7A5aDBJULgEO8zkuqtNBObq+MBf7qeO+2/8BbQ3D2iwwVKuu+KkoEtwjmfaFab4dzgCPgaTz2/cwpkAAAAASUVORK5CYII=>