from fastapi import APIRouter

# Import route modules
from .routes.characters import router as characters_router
from .routes.projects import router as projects_router
from .routes.scripts import router as scripts_router
from .routes.storyboards import router as storyboards_router
from .routes.assets import router as assets_router
from .routes.scenes import router as scenes_router
from .routes.films import router as films_router
from .routes.shots import router as shots_router
from .routes.drafts import router as drafts_router
from .routes.users import router as users_router

# Create the main router
router = APIRouter()

# Include all route modules with appropriate prefixes
router.include_router(characters_router, prefix='/characters', tags=['characters'])
router.include_router(projects_router, prefix='/projects', tags=['projects'])
router.include_router(scripts_router, prefix='/scripts', tags=['scripts'])
router.include_router(storyboards_router, prefix='/storyboards', tags=['storyboards'])
router.include_router(assets_router, prefix='/assets', tags=['assets'])
router.include_router(scenes_router, prefix='/scenes', tags=['scenes'])
router.include_router(films_router, prefix='/films', tags=['films'])
router.include_router(shots_router, prefix='/shots', tags=['shots'])
router.include_router(drafts_router, prefix='/drafts', tags=['drafts'])
router.include_router(users_router, prefix='/users', tags=['users'])
