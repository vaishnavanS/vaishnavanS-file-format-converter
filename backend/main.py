import os
import uuid
import sys
import traceback
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

# Try to import converter with explicit error catching
try:
    from converter import FileConverter
    IMPORT_ERROR = None
except Exception as e:
    IMPORT_ERROR = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel-friendly storage
IS_CLOUD = os.environ.get('VERCEL') == '1'
TMP_BASE = Path("/tmp") if IS_CLOUD else Path(".")

UPLOAD_DIR = TMP_BASE / "uploads"
DOWNLOAD_DIR = TMP_BASE / "downloads"

try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DIR_ERROR = None
except Exception as e:
    DIR_ERROR = str(e)

if not IMPORT_ERROR:
    try:
        converter = FileConverter(str(UPLOAD_DIR), str(DOWNLOAD_DIR))
        CONVERTER_ERROR = None
    except Exception as e:
        CONVERTER_ERROR = str(e)
else:
    converter = None
    CONVERTER_ERROR = "Module import failed"

tasks = {}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc), "traceback": traceback.format_exc()}
    )

@app.post("/api/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), target_format: str = "pdf"):
    if IMPORT_ERROR or CONVERTER_ERROR:
        raise HTTPException(status_code=500, detail=f"System Error: {IMPORT_ERROR or CONVERTER_ERROR}")

    # Vercel Free Tier Payload Limit
    MAX_SIZE = 4 * 1024 * 1024 
    content = await file.read()
    
    if len(content) > MAX_SIZE:
        return JSONResponse(status_code=413, content={"error": "File too large", "detail": "Max 4MB on Vercel."})
    
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
    
    # Run conversion
    try:
        tasks[task_id]["status"] = "processing"
        output_path = converter.process_conversion(input_filename, target_format)
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["output_file"] = str(output_path.name)
        return {"task_id": task_id, "status": "completed"}
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        return JSONResponse(status_code=500, content={"error": "Conversion failed", "detail": str(e)})

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in tasks:
        return {"status": "failed", "error": "Task not found"}
    return tasks[task_id]

@app.get("/api/download/{task_id}")
async def download_file(task_id: str):
    if task_id not in tasks or tasks[task_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="File not ready")
    
    file_path = DOWNLOAD_DIR / tasks[task_id]["output_file"]
    return FileResponse(path=file_path, filename=tasks[task_id]["output_file"])

@app.get("/api/debug")
async def debug():
    return {
        "import_error": IMPORT_ERROR,
        "dir_error": DIR_ERROR,
        "converter_error": CONVERTER_ERROR,
        "cwd": os.getcwd(),
        "sys_path": sys.path,
        "is_cloud": IS_CLOUD,
        "python_version": sys.version
    }

@app.get("/")
@app.get("/api")
async def root():
    return {"message": "EasyConverter API is live!", "debug_url": "/api/debug"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
