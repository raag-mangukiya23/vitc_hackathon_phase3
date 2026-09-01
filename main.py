from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import time

# 1. Connect to Firebase using the file you just downloaded
cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. Start the FastAPI application
app = FastAPI()

# 3. Allow your HTML file to communicate with this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Create the endpoint that receives data from your HTML form
@app.post("/api/submit-complaint")
async def submit_complaint(
    text: str = Form(...),
    location: str = Form(...),
    image: UploadFile = File(None),
    audio: UploadFile = File(None)
):
    # (Later, you will pass the 'image' and 'audio' variables to OpenAI/Gemini here)
    
    # For now, we simulate AI keyword analysis on the text:
    lower_text = text.lower()
    if any(word in lower_text for word in ['spark', 'wire', 'electric', 'shock']):
        category, dept, score, level, sla, reason = "Electricity Board", "DISCOM Rapid Response", 89, "critical", "🚨 4h SLA (Urgent)", "Immediate electrocution risk flagged."
    elif any(word in lower_text for word in ['sewage', 'water', 'leak']):
        category, dept, score, level, sla, reason = "Water Supply", "Water & Sanitation", 75, "high", "⚠️ 24h SLA", "Public health hazard detected."
    else:
        category, dept, score, level, sla, reason = "Roads & Highways", "Public Works", 42, "medium", "3-Day SLA", "Routine maintenance ticket."

    # Create a unique ticket ID
    ticket_id = f"TCK-{uuid.uuid4().hex[:6].upper()}"
    
    # Package the data
    complaint_data = {
        "ticketId": ticket_id,
        "text": text,
        "location": location,
        "category": category,
        "department": dept,
        "score": score,
        "level": level,
        "sla": sla,
        "reason": reason,
        "timestamp": int(time.time() * 1000)
    }

    # Save it securely to Firebase Firestore
    db.collection("complaints").add(complaint_data)

    return {"status": "success", "ticketId": ticket_id}