from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.routers import analyzer
import os

app = FastAPI(
    title="🧠 Project Analyzer API",
    description="Code Architecture Analyzer",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(analyzer.router, prefix="/api", tags=["Analyzer"])

# ✅ Mount frontend folder (for CSS/JS if any)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# ✅ Serve UI on root
@app.get("/", response_class=HTMLResponse)
def serve_ui():
    file_path = os.path.join("frontend", "index.html")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h2>Frontend not found</h2>"

# ✅ Keep API info separate (clean design)
@app.get("/api-info")
def api_info():
    return {
        "status": "running",
        "message": "🧠 Project Analyzer API",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy"}