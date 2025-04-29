from fastapi import FastAPI, Request, Cookie, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from agent.conversation import handle_message
import os
import uuid
from typing import Optional

app = FastAPI()

# Mount static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_chat_ui(response: Response, session_id: Optional[str] = Cookie(None)):
    # Generate a new session ID if one doesn't exist
    if not session_id:
        session_id = str(uuid.uuid4())
        response.set_cookie(key="session_id", value=session_id, max_age=3600*24*30)  # 30 days
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.post("/chat")
async def chat(request: Request, session_id: Optional[str] = Cookie(None)):
    data = await request.json()
    user_message = data.get("message", "")
    user_id = data.get("user_id", session_id)
    
    # Fallback if no session ID
    if not user_id:
        user_id = str(uuid.uuid4())
        
    response = handle_message(user_message, user_id)
    return {"response": response} 