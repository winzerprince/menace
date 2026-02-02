"""
API Module

Contains FastAPI routes and Pydantic schemas for the MENACE API.
"""

from app.api.routes import router
from app.api.schemas import (
    NewGameRequest,
    NewGameResponse,
    MoveRequest,
    MoveResponse,
    GameStateResponse,
    MenaceStatsResponse,
)

__all__ = [
    "router",
    "NewGameRequest",
    "NewGameResponse",
    "MoveRequest",
    "MoveResponse",
    "GameStateResponse",
    "MenaceStatsResponse",
]
