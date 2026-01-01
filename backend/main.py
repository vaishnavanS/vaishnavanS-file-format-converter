import os
import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from converter import FileConverter
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For cloud platforms (Netlify/Vercel/Heroku), use /tmp for temporary storage
IS_CLOUD = os.environ.get('NETLIFY') or os.environ.get('VERCEL')
TMP_BASE = Path("/tmp") if IS_CLOUD else Path(".")

UPLOAD_DIR = TMP_BASE / "uploads"
DOWNLOAD_DIR = TMP_BASE / "downloads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

converter = FileConverter(str(UPLOAD_DIR), str(DOWNLOAD_DIR))

# In-memory task status storage
tasks = {}

def conversion_task(task_id: str, input_filename: str, target_format: str):
    try:
        tasks[task_id]["status"] = "processing"
        output_path = converter.process_conversion(input_filename, target_format)
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["output_file"] = str(output_path.name)
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), target_format: str = "pdf"):
    # File size limit (e.g., 10MB)
    MAX_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")
    
    file_id = str(uuid.uuid4())
    input_filename = f"{file_id}_{file.filename}"
    input_path = UPLOAD_DIR / input_filename
    
    with open(input_path, "wb") as f:
        f.write(content)
    
    task_id = file_id
    tasks[task_id] = {
        "status": "pending",
        "input_file": input_filename,
        "target_format": target_format
    }
    
    background_tasks.add_task(conversion_task, task_id, input_filename, target_format)
    
    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/download/{task_id}")
async def download_file(task_id: str, background_tasks: BackgroundTasks):
    if task_id not in tasks or tasks[task_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="File not ready or task not found")
    
    output_filename = tasks[task_id]["output_file"]
    file_path = DOWNLOAD_DIR / output_filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Schedule cleanup after download
    background_tasks.add_task(cleanup_files, task_id)
    
    return FileResponse(path=file_path, filename=output_filename, media_type='application/octet-stream')

def cleanup_files(task_id: str):
    task = tasks.get(task_id)
    if task:
        input_path = UPLOAD_DIR / task["input_file"]
        output_path = DOWNLOAD_DIR / task["output_file"]
        
        if input_path.exists():
            input_path.unlink()
        if output_path.exists():
            output_path.unlink()
        
        # Optionally remove from tasks dict
        # del tasks[task_id]

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "EasyConverter backend is live!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
