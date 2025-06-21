from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Form
from typing import Union
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime
import certifi
import os

# Load environment variables
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")

# Improve MongoDB connection with error handling
try:
    # Get MongoDB connection parameters 
    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("MONGO_DB_NAME")
    
    if not mongo_url or not db_name:
        raise ValueError("MongoDB connection parameters missing in .env file")
    
    # Connect with SSL certificate verification and timeouts
    conn = MongoClient(
        mongo_url,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,  # Lower timeout for faster feedback
        connectTimeoutMS=10000
    )
    db = conn[db_name]
    
    # Test the connection
    conn.admin.command('ping')
    print("MongoDB connection successful!")
    
except Exception as e:
    print(f"MongoDB connection error: {str(e)}")
    # Create fallback in-memory data for development
    conn = None
    db = None

@app.get("/", response_class=HTMLResponse)
async def read_notes(request: Request):
    try:
        if db is None:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "docs": [],
                "error": "Database connection failed"
            })
            
        # Get a reference to the correct collection
        notes_collection = db.notes
        # Find all documents - changed from find_one to find
        docs = list(notes_collection.find())
        
        print(f"Found {len(docs)} notes in the collection")
        return templates.TemplateResponse("index.html", {"request": request, "docs": docs})
    
    except Exception as e:
        print(f"Error accessing MongoDB: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request, 
            "docs": [],
            "error": str(e)
        })

# Modify your POST endpoint
@app.post("/send", response_class=HTMLResponse)
async def create_note(request: Request, title: str = Form(...), description: str = Form(...)):
    try:
        if db is None:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "docs": [],
                "error": "Database connection failed"
            })
        
        # Get a reference to the collection
        notes_collection = db.notes
        
        # Create a new note document
        new_note = {
            "title": title,
            "description": description,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Insert into MongoDB
        result = notes_collection.insert_one(new_note)
        print(f"Note created with ID: {result.inserted_id}")
        
        # Redirect to home page after successful submission
        # This prevents form resubmission issues
        return RedirectResponse("/", status_code=303)
        
    except Exception as e:
        print(f"Error creating note: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "docs": [],
            "error": f"Error creating note: {str(e)}"
        })

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str|None=None):
    return {"item_id": item_id, "q": q}