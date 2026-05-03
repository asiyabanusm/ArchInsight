from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analyzer

app = FastAPI(
    title="🧠 Project Analyzer API",
    description="AI-powered codebase analysis tool",
    version="1.0.0"
)

# CORS Configuration - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(analyzer.router, prefix="/api", tags=["Analyzer"])


@app.get("/")
def root():
    return {
        "status": "running",
        "message": "🧠 Project Analyzer API",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}