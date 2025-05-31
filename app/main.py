"""Main entry point for the Le Rhino API application."""
import os
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError, ServerError
from app.models.base import ApiResponse

# Import routes
from app.api.routes import auth, matieres, documents, questions, evaluations, challenges, leaderboard, users

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, set specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": str(exc.detail), "data": None},
        headers=exc.headers,
    )

@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": str(exc.detail), "data": None},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False, 
            "message": "Validation error", 
            "data": {"errors": exc.errors()}
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": f"Server error: {str(exc)}", "data": None},
    )

# Root endpoint
@app.get("/", tags=["Frontend"])
async def serve_homepage():
    """Serve the homepage."""
    return FileResponse("static/index.html")

# Root API endpoint
@app.get("/api", response_model=ApiResponse, tags=["Status"])
async def root():
    """Root endpoint to check API status."""
    return {
        "success": True,
        "message": "Le Rhino API", 
        "data": {"status": "online"}
    }

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(matieres.router, prefix="/api")
app.include_router(documents.router, prefix="/api")  # No prefix as it already has matiere-specific paths
app.include_router(questions.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")
app.include_router(challenges.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
# app.include_router(users.router, prefix="/users")
app.include_router(users.router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize resources at startup."""
    try:
        # Initialize Pinecone and other resources will be implemented here
        # for now just print a message
        print("Initializing API resources...")
    except Exception as e:
        print(f"Error during startup: {e}")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# For direct execution
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 