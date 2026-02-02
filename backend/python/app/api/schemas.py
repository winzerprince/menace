"""
API Schemas - Request and Response Models

This module defines Pydantic models for API request/response validation.

WHY PYDANTIC?

1. Automatic Validation:
   - Pydantic checks that incoming data matches our expectations
   - Invalid requests are rejected with clear error messages

2. Type Safety:
   - IDE autocomplete and error detection
   - Self-documenting code

3. Automatic Documentation:
   - FastAPI uses these schemas to generate Swagger docs
   - Users can see exactly what format to use

4. Serialization:
   - Easy conversion to/from JSON
   - Handles dates, enums, etc. automatically

Example:
    If a client sends: {"position": "not a number"}
    Pydantic will respond with:
    {"detail": "value is not a valid integer"}
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# Enums for API
# ============================================================================


class PlayerSymbol(str, Enum):
    """Player symbol for API responses."""

    X = "X"
    O = "O"


class GameStatus(str, Enum):
    """Game status values."""

    WAITING_FOR_OPPONENT = "waiting_for_opponent"
    WAITING_FOR_MENACE = "waiting_for_menace"
    FINISHED = "finished"


class GameResultType(str, Enum):
    """Game result from MENACE's perspective."""

    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"


# ============================================================================
# Game Endpoints
# ============================================================================


class NewGameRequest(BaseModel):
    """
    Request to start a new game.

    Attributes:
        menace_plays_first: If true, MENACE plays X and goes first.
                           If false, human plays X and goes first.
    """

    menace_plays_first: bool = Field(
        default=True,
        description="If true, MENACE plays first as X. If false, human plays first.",
    )

    class Config:
        json_schema_extra = {"example": {"menace_plays_first": True}}


class NewGameResponse(BaseModel):
    """
    Response after creating a new game.

    Returns the game ID and initial state.
    If MENACE plays first, includes MENACE's opening move.
    """

    game_id: str = Field(description="Unique identifier for this game")
    board: str = Field(description="Current board state (9 characters)")
    current_turn: PlayerSymbol = Field(description="Whose turn it is")
    menace_player: PlayerSymbol = Field(description="Which symbol MENACE is playing")
    status: GameStatus = Field(description="Current game status")
    valid_moves: List[int] = Field(description="List of valid move positions (0-8)")
    menace_move: Optional[int] = Field(
        default=None, description="Position where MENACE moved (if MENACE went first)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "abc123",
                "board": "____X____",
                "current_turn": "O",
                "menace_player": "X",
                "status": "waiting_for_opponent",
                "valid_moves": [0, 1, 2, 3, 5, 6, 7, 8],
                "menace_move": 4,
            }
        }


class MoveRequest(BaseModel):
    """
    Request to make a move.

    The human/opponent sends their move position.
    """

    position: int = Field(
        ge=0,  # Greater than or equal to 0
        le=8,  # Less than or equal to 8
        description="Position to play (0-8, top-left to bottom-right)",
    )

    class Config:
        json_schema_extra = {"example": {"position": 4}}


class MoveResponse(BaseModel):
    """
    Response after making a move.

    Returns the updated game state and MENACE's response move (if game continues).
    """

    board: str = Field(description="Board state after all moves")
    current_turn: Optional[PlayerSymbol] = Field(
        description="Whose turn it is (null if game over)"
    )
    status: GameStatus = Field(description="Current game status")
    valid_moves: List[int] = Field(description="Available moves for next player")
    opponent_move: int = Field(description="The move the opponent just made")
    menace_move: Optional[int] = Field(
        default=None,
        description="MENACE's response move (null if game ended or not MENACE's turn)",
    )
    is_game_over: bool = Field(description="Whether the game has ended")
    result: Optional[GameResultType] = Field(
        default=None,
        description="Game result from MENACE's perspective (null if not over)",
    )
    winner: Optional[PlayerSymbol] = Field(
        default=None, description="The winning player (null if draw or not over)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "board": "X___OX___",
                "current_turn": "O",
                "status": "waiting_for_opponent",
                "valid_moves": [1, 2, 3, 6, 7, 8],
                "opponent_move": 4,
                "menace_move": 5,
                "is_game_over": False,
                "result": None,
                "winner": None,
            }
        }


class GameStateResponse(BaseModel):
    """
    Full game state response.

    Returns complete information about a game.
    """

    game_id: str
    board: str
    current_turn: Optional[PlayerSymbol]
    menace_player: PlayerSymbol
    status: GameStatus
    valid_moves: List[int]
    is_game_over: bool
    result: Optional[GameResultType]
    winner: Optional[PlayerSymbol]
    move_count: int = Field(description="Number of moves made")

    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "abc123",
                "board": "XOX_O_X__",
                "current_turn": "O",
                "menace_player": "X",
                "status": "waiting_for_opponent",
                "valid_moves": [3, 5, 7, 8],
                "is_game_over": False,
                "result": None,
                "winner": None,
                "move_count": 5,
            }
        }


# ============================================================================
# MENACE Statistics Endpoints
# ============================================================================


class MenaceStatsResponse(BaseModel):
    """
    MENACE's learning statistics.

    Shows how well MENACE has learned.
    """

    games_played: int = Field(description="Total games completed")
    wins: int = Field(description="Games MENACE won")
    losses: int = Field(description="Games MENACE lost")
    draws: int = Field(description="Games that ended in draw")
    win_rate: float = Field(description="Win percentage (0.0 to 1.0)")
    matchbox_count: int = Field(description="Number of unique states learned")
    total_beads: int = Field(description="Total beads across all matchboxes")

    class Config:
        json_schema_extra = {
            "example": {
                "games_played": 100,
                "wins": 45,
                "losses": 30,
                "draws": 25,
                "win_rate": 0.45,
                "matchbox_count": 85,
                "total_beads": 1250,
            }
        }


class MatchboxResponse(BaseModel):
    """
    Data about a specific matchbox.

    Shows the bead distribution for a game state.
    """

    board_state: str = Field(description="The normalized board state")
    beads: Dict[str, int] = Field(
        description="Bead count for each position (position as string key)"
    )
    times_used: int = Field(description="How many times this state was encountered")
    probabilities: Dict[str, float] = Field(
        description="Probability of each move being selected"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "board_state": "_________",
                "beads": {
                    "0": 5,
                    "1": 2,
                    "2": 5,
                    "3": 2,
                    "4": 12,
                    "5": 2,
                    "6": 5,
                    "7": 2,
                    "8": 5,
                },
                "times_used": 50,
                "probabilities": {
                    "0": 0.125,
                    "1": 0.05,
                    "2": 0.125,
                    "3": 0.05,
                    "4": 0.3,
                    "5": 0.05,
                    "6": 0.125,
                    "7": 0.05,
                    "8": 0.125,
                },
            }
        }


class MatchboxQueryRequest(BaseModel):
    """
    Request to query a matchbox by board state.
    """

    board_state: str = Field(
        min_length=9,
        max_length=9,
        description="Board state to look up (9 characters: X, O, or _)",
    )

    class Config:
        json_schema_extra = {"example": {"board_state": "X___O____"}}


# ============================================================================
# Training Endpoints
# ============================================================================


class TrainingRequest(BaseModel):
    """
    Request to run self-play training.
    """

    num_games: int = Field(
        default=100, ge=1, le=10000, description="Number of games to play (1-10000)"
    )
    opponent: str = Field(
        default="random", description="Opponent type: 'random' or 'optimal'"
    )

    class Config:
        json_schema_extra = {"example": {"num_games": 100, "opponent": "random"}}


class TrainingResponse(BaseModel):
    """
    Response after training session.
    """

    games_played: int
    wins: int
    losses: int
    draws: int
    time_seconds: float = Field(description="Time taken for training")
    new_matchboxes: int = Field(description="New matchboxes created during training")

    class Config:
        json_schema_extra = {
            "example": {
                "games_played": 100,
                "wins": 35,
                "losses": 40,
                "draws": 25,
                "time_seconds": 0.5,
                "new_matchboxes": 42,
            }
        }


# ============================================================================
# History / Graphing Endpoints
# ============================================================================


class HistorySnapshotResponse(BaseModel):
    """
    A single snapshot of MENACE's learning state.

    Used for plotting bead growth and learning progress over time.
    """

    games: int = Field(description="Number of games played at snapshot time")
    total_beads: int = Field(description="Total beads across all matchboxes")
    matchbox_count: int = Field(description="Number of matchboxes at this point")
    wins: int = Field(description="Cumulative wins")
    losses: int = Field(description="Cumulative losses")
    draws: int = Field(description="Cumulative draws")
    win_rate: float = Field(description="Win rate at this point (0.0 to 1.0)")


class HistoryResponse(BaseModel):
    """
    MENACE's learning history for graphing.

    Contains snapshots of stats over time to visualize learning progress.
    """

    history: List[HistorySnapshotResponse] = Field(
        description="List of historical snapshots"
    )
    current_games: int = Field(description="Current total games played")
    current_beads: int = Field(description="Current total beads")

    class Config:
        json_schema_extra = {
            "example": {
                "history": [
                    {
                        "games": 10,
                        "total_beads": 150,
                        "matchbox_count": 15,
                        "wins": 3,
                        "losses": 5,
                        "draws": 2,
                        "win_rate": 0.3,
                    },
                    {
                        "games": 20,
                        "total_beads": 280,
                        "matchbox_count": 28,
                        "wins": 8,
                        "losses": 8,
                        "draws": 4,
                        "win_rate": 0.4,
                    },
                ],
                "current_games": 100,
                "current_beads": 1250,
            }
        }


# ============================================================================
# Error Responses
# ============================================================================


class ErrorResponse(BaseModel):
    """
    Standard error response.
    """

    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error info")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid move",
                "detail": "Position 4 is already occupied",
            }
        }
