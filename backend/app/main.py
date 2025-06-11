from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.auth import router as auth_router
from .api.files import router as files_router
from .api.gpt import router as gpt_router

app = FastAPI(
    title="Full-Stack AI Agent API",
    description="FastAPI backend with user authentication, file upload, and GPT integration",
    version="1.0.0"
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://localhost:8501"],  # Include Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(files_router)
app.include_router(gpt_router)


@app.get("/")
def read_root():
    return {
        "message": "Full-Stack AI Agent API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "files": "/files",
            "gpt": "/gpt",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running"}
