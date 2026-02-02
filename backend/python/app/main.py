"""
FastAPI Application Entry Point

This is where we create and configure the FastAPI application.
Think of this as the "front door" of our backend - all HTTP requests
come through here first.

Key Concepts:
- FastAPI(): Creates our web application
- CORS: Allows our React frontend to talk to this backend
- Routers: Organize our API endpoints into logical groups
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our API routes (we'll create these next)
from app.api.routes import router as api_router

# Create the FastAPI application
# The metadata here shows up in the automatic documentation
app = FastAPI(
    title="MENACE API",
    description="""
    ## Machine Educable Noughts And Crosses Engine
    
    This API provides endpoints to:
    - **Play** tic-tac-toe against MENACE
    - **Train** MENACE through self-play
    - **View** learning statistics and matchbox data
    
    MENACE learns through reinforcement learning, adjusting its strategy
    based on game outcomes.
    """,
    version="0.1.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc at /redoc
)

# Configure CORS (Cross-Origin Resource Sharing)
# This is ESSENTIAL for the React frontend to communicate with our backend
#
# WHY DO WE NEED THIS?
# Browsers have a security feature that blocks web pages from making requests
# to a different domain/port. Our React app runs on port 3000, but our
# FastAPI backend runs on port 8000. Without CORS, the browser would block
# all requests from React to FastAPI.
app.add_middleware(
    CORSMiddleware,
    # Which origins (domains) can access our API
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    # Allow credentials (cookies, auth headers)
    allow_credentials=True,
    # Which HTTP methods are allowed
    allow_methods=["*"],  # All methods (GET, POST, PUT, DELETE, etc.)
    # Which headers can be sent
    allow_headers=["*"],  # All headers
)

# Include our API routes
# The prefix means all routes in api_router will start with /api
# So if we have a route "/game/new", it becomes "/api/game/new"
app.include_router(api_router, prefix="/api")


# Root endpoint - just a health check / welcome message
@app.get("/")
async def root():
    """
    Root endpoint - confirms the API is running.

    This is a simple health check. If you can reach this endpoint,
    the server is up and running!
    """
    return {"message": "Welcome to MENACE API", "docs": "/docs", "status": "running"}


# Event handlers for startup/shutdown
@app.on_event("startup")
async def startup_event():
    """
    Runs when the server starts.

    This is where we'll initialize:
    - Database connections
    - Load MENACE's learned state
    """
    print("🎮 MENACE API starting up...")
    # TODO: Initialize database
    # TODO: Load MENACE state
    print("✅ MENACE API ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when the server shuts down.

    This is where we'll:
    - Save MENACE's learned state
    - Close database connections
    """
    print("💾 Saving MENACE state...")
    # TODO: Save state
    print("👋 MENACE API shutting down")
