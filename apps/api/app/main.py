from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],  # Update this to your front-end domain(s) if needed
    allow_credentials=True,
    allow_methods=["*"],  # Update methods if necessary
    allow_headers=["*"]
)


# Health endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Route registrations for different entities
@app.get("/projects")
async def get_projects():
    return {"message": "List of projects"}

@app.get("/scripts")
async def get_scripts():
    return {"message": "List of scripts"}

@app.get("/storyboards")
async def get_storyboards():
    return {"message": "List of storyboards"}

@app.get("/assets")
async def get_assets():
    return {"message": "List of assets"}

@app.get("/scenes")
async def get_scenes():
    return {"message": "List of scenes"}

@app.get("/films")
async def get_films():
    return {"message": "List of films"}