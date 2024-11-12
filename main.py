import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from uuid import uuid4
from chatbot import handle_chat_query  # Import the modified handle_chat_query function

# Initialize FastAPI application
app = FastAPI()

# Mount the 'static' directory to serve CSS and JS files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates for HTML rendering
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Serve the homepage with the form for the chatbot
    return templates.TemplateResponse("index.html", {"request": request})

# Load the secret key from the environment variables
SECRET_KEY = "I_am_Admin"

# Define a Pydantic model to validate the request body
class ChatRequest(BaseModel):
    user_input: str

@app.post("/chatbot")
async def chat_route(request: Request, chat_request: ChatRequest):
    # Extract the secret key from the request headers
    client_secret = request.headers.get('X-SECRET-KEY')
    
    # Check if the secret key is valid
    if client_secret != SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized access. Invalid secret key.")
    
    # Generate or retrieve a unique session ID for the user
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid4())  # Generate a new session ID if none exists
    
    # Process the chat request using the chatbot logic with session_id
    user_input = chat_request.user_input
    chatbot_response_text = await handle_chat_query(session_id, user_input)  # Pass session_id to handle_chat_query

    # Prepare the JSON response
    response = JSONResponse(content={"response": chatbot_response_text})
    
    # Set the session ID as a cookie in the response if it's newly generated
    if not request.cookies.get("session_id"):
        response.set_cookie(key="session_id", value=session_id)
    
    return response
