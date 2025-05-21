from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from pydantic import BaseModel
import shutil
import os
import logging
from backend.utils.ocr_store import ocr_cache
from backend.graph.langgraph_flow import app as langgraph_app, ocr_tool, dealer_risk_tool
from backend.utils.dealer_risk_store import dealer_risk_cache
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logging.info(f"[{datetime.utcnow().isoformat()}] Incoming request: {request.method} {request.url.path}")
        return await call_next(request)

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)

UPLOAD_DIR = "ocr_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    query: str
    history: list

@app.post("/upload_file")
async def upload_file(file: UploadFile):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ocr_tool.load_document(file_path)
    ocr_cache[file.filename] = ocr_tool.ocr_data

    return JSONResponse({
        "filename": file.filename,
        "ocr_text": ocr_tool.ocr_data
    })

@app.get("/uploaded_files")
async def list_uploaded_files():
    files = os.listdir(UPLOAD_DIR)
    files_with_ocr = [
        {"filename": f, "ocr_text": ocr_cache.get(f, "Not OCR'd yet")} for f in files
    ]
    return files_with_ocr

@app.post("/chat")
async def chat(request: ChatRequest):
    session_state = {
        "task_queue": [request.query],
        "last_result": "",
        "next_agent": "",
        "done": False,
        "task_attempts": {},
        "chat_history": request.history  # Pass the provided history into the state
    }
    print(f"[Session State]: {session_state}")

    task_result = langgraph_app.invoke(session_state)
    return JSONResponse(content={"response": task_result["last_result"]})

@app.get("/status")
async def status():
    return {"status": "ok"}

@app.get("/version")
async def version():
    return {"version": "v1.0.0", "model": "mistral"}

@app.get("/refresh_dealer_index")
async def refresh_dealer_index():
    dealer_risk_tool.load_risk_index()
    return JSONResponse(content={"dealer_risk_index": dealer_risk_cache})

@app.get("/available_tools")
async def available_tools():
    tools = {
        "llm": "General knowledge queries (definitions, explanations)",
        "ocr": "Answer questions about uploaded document text",
        "dealer_risk": "Analyze dealer repossession risk by dealer_id or lotname",
        "research": "Search the web for up-to-date information"
    }

    # Add the cached dealer count
    dealer_count = len(dealer_risk_cache)
    return JSONResponse(content={"tools": tools, "dealer_risk_count": dealer_count})


app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
