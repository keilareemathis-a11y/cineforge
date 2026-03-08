from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router
from app.core.config import Settings

# Initialize settings
settings = Settings(app_name="Cineforge API", debug=True, version="0.1.0")

# Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Backend API for the Cineforge AI short-film creation platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - returns API status"""
    return {
        "message": "Welcome to Cineforge API",
        "status": "running",
        "version": settings.version,
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint - confirms API is running"""
    return {
        "status": "healthy",
        "service": "cineforge-api",
        "timestamp": "2026-03-08T17:00:00Z"
    }

# Include the main API router
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)