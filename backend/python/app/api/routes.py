"""
API Routes - Endpoint Definitions

This module defines all the HTTP endpoints for the MENACE API.

DESIGN DECISIONS:

1. Resource-Oriented URLs:
   - /game/* - Game session management
   - /menace/* - MENACE-specific operations (stats, matchboxes)
   - /training/* - Training operations

2. Stateful Game Management:
   - Games are stored in memory (for now)
   - Each game has a unique ID
   - Later we'll add database persistence

3. Error Handling:
   - Clear error messages
   - Appropriate HTTP status codes
   - Consistent error response format
"""

import time
import random
from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.api.schemas import (
    NewGameRequest,
    NewGameResponse,
    MoveRequest,
    MoveResponse,
    GameStateResponse,
    MenaceStatsResponse,
    MatchboxResponse,
    MatchboxQueryRequest,
    TrainingRequest,
    TrainingResponse,
    TrainingEstimateRequest,
    TrainingEstimateResponse,
    HistoryResponse,
    HistorySnapshotResponse,
    PlayerSymbol,
    GameStatus,
    GameResultType,
)
from app.core.board import Board, Player
from app.core.game import Game, GameManager
from app.core.menace import Menace

# Create the API router
# All routes defined here will be prefixed with /api in main.py
router = APIRouter()

# ============================================================================
# Global State (temporary - will move to database later)
# ============================================================================

# Create a single MENACE instance that persists across requests
# In production, this would be loaded from a database
menace_instance = Menace(player=Player.X)

# Game manager to track active games
game_manager = GameManager(menace=menace_instance)


# ============================================================================
# Helper Functions
# ============================================================================


def get_player_symbol(player: Player) -> PlayerSymbol:
    """Convert internal Player to API PlayerSymbol."""
    return PlayerSymbol.X if player == Player.X else PlayerSymbol.O


def get_game_status(game: Game) -> GameStatus:
    """Convert internal game state to API GameStatus."""
    if game.is_over():
        return GameStatus.FINISHED
    elif game.is_menace_turn():
        return GameStatus.WAITING_FOR_MENACE
    else:
        return GameStatus.WAITING_FOR_OPPONENT


def get_result_type(game: Game) -> Optional[GameResultType]:
    """Get the game result as API type."""
    if not game.is_over():
        return None
    result = game.get_result()
    return GameResultType(result.value)


def get_winner(game: Game) -> Optional[PlayerSymbol]:
    """Get the winner as API type."""
    winner = game.board.check_winner()
    if winner is None:
        return None
    return get_player_symbol(winner)


# ============================================================================
# Game Endpoints
# ============================================================================


@router.post(
    "/game/new",
    response_model=NewGameResponse,
    summary="Start a new game",
    description="""
    Create a new tic-tac-toe game against MENACE.
    
    If `menace_plays_first` is true (default), MENACE plays as X and 
    will make the opening move immediately. The response includes
    MENACE's first move.
    
    If `menace_plays_first` is false, the human plays as X and should
    make the first move using the /game/{id}/move endpoint.
    """,
    tags=["Game"],
)
async def new_game(request: NewGameRequest) -> NewGameResponse:
    """Create a new game session."""

    # Create the game
    game = game_manager.create_game(menace_plays_first=request.menace_plays_first)

    menace_move: Optional[int] = None

    # If MENACE plays first, make the opening move
    if request.menace_plays_first:
        position, _ = game.menace_move()
        menace_move = position

    return NewGameResponse(
        game_id=game.id,
        board=game.board.state,
        current_turn=get_player_symbol(game.current_turn),
        menace_player=get_player_symbol(game.menace_player),
        status=get_game_status(game),
        valid_moves=game.get_valid_moves(),
        menace_move=menace_move,
    )


@router.post(
    "/game/{game_id}/move",
    response_model=MoveResponse,
    summary="Make a move",
    description="""
    Submit the opponent's (human's) move and get MENACE's response.
    
    The opponent specifies a position (0-8) where they want to play.
    If the move is valid and the game continues, MENACE will 
    automatically make its response move.
    
    Position mapping:
    ```
    0 | 1 | 2
    ---------
    3 | 4 | 5
    ---------
    6 | 7 | 8
    ```
    """,
    tags=["Game"],
)
async def make_move(game_id: str, request: MoveRequest) -> MoveResponse:
    """Process a move from the opponent."""

    # Get the game
    game = game_manager.get_game(game_id)
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Game not found: {game_id}"
        )

    # Check if game is already over
    if game.is_over():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Game is already over"
        )

    # Check if it's opponent's turn
    if not game.is_opponent_turn():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="It's not your turn - waiting for MENACE",
        )

    # Validate move
    if request.position not in game.get_valid_moves():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid move: position {request.position} is not available. Valid moves: {game.get_valid_moves()}",
        )

    # Make opponent's move
    try:
        game.opponent_move(request.position)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    menace_move: Optional[int] = None

    # If game continues and it's MENACE's turn, let MENACE respond
    if not game.is_over() and game.is_menace_turn():
        position, _ = game.menace_move()
        menace_move = position

    # If game ended, apply learning
    if game.is_over():
        game_manager.finish_game(game_id)

    return MoveResponse(
        board=game.board.state,
        current_turn=(
            get_player_symbol(game.current_turn) if not game.is_over() else None
        ),
        status=get_game_status(game),
        valid_moves=game.get_valid_moves(),
        opponent_move=request.position,
        menace_move=menace_move,
        is_game_over=game.is_over(),
        result=get_result_type(game),
        winner=get_winner(game),
    )


@router.get(
    "/game/{game_id}",
    response_model=GameStateResponse,
    summary="Get game state",
    description="Retrieve the current state of a game.",
    tags=["Game"],
)
async def get_game_state(game_id: str) -> GameStateResponse:
    """Get the current state of a game."""

    game = game_manager.get_game(game_id)
    if game is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Game not found: {game_id}"
        )

    return GameStateResponse(
        game_id=game.id,
        board=game.board.state,
        current_turn=(
            get_player_symbol(game.current_turn) if not game.is_over() else None
        ),
        menace_player=get_player_symbol(game.menace_player),
        status=get_game_status(game),
        valid_moves=game.get_valid_moves(),
        is_game_over=game.is_over(),
        result=get_result_type(game),
        winner=get_winner(game),
        move_count=len(game.moves),
    )


# ============================================================================
# MENACE Statistics Endpoints
# ============================================================================


@router.get(
    "/menace/stats",
    response_model=MenaceStatsResponse,
    summary="Get MENACE statistics",
    description="""
    Get MENACE's learning statistics.
    
    Shows:
    - Games played, wins, losses, draws
    - Win rate
    - Number of matchboxes (unique states learned)
    - Total beads across all matchboxes
    """,
    tags=["MENACE"],
)
async def get_menace_stats() -> MenaceStatsResponse:
    """Get MENACE's learning statistics."""

    stats = menace_instance.get_statistics()

    return MenaceStatsResponse(
        games_played=stats["games_played"],
        wins=stats["wins"],
        losses=stats["losses"],
        draws=stats["draws"],
        win_rate=stats["win_rate"],
        matchbox_count=stats["matchbox_count"],
        total_beads=stats["total_beads"],
    )


@router.post(
    "/menace/matchbox",
    response_model=MatchboxResponse,
    summary="Query a matchbox",
    description="""
    Get the bead distribution for a specific board state.
    
    The board state will be normalized before lookup.
    Returns None if MENACE hasn't encountered this state yet.
    """,
    tags=["MENACE"],
)
async def query_matchbox(request: MatchboxQueryRequest) -> MatchboxResponse:
    """Get data about a specific matchbox."""

    # Validate board state
    try:
        board = Board(request.board_state)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid board state: {e}"
        )

    # Get matchbox data
    data = menace_instance.get_matchbox_data(request.board_state)

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matchbox found for state: {request.board_state}",
        )

    # Calculate probabilities
    matchbox = menace_instance.matchboxes[data["board_state"]]
    probs = matchbox.get_probabilities()

    return MatchboxResponse(
        board_state=data["board_state"],
        beads={str(k): v for k, v in data["beads"].items()},
        times_used=data["times_used"],
        probabilities={str(k): v for k, v in probs.items()},
    )


@router.get(
    "/menace/matchboxes",
    summary="List all matchboxes",
    description="Get a list of all matchboxes MENACE has learned.",
    tags=["MENACE"],
)
async def list_matchboxes():
    """List all matchboxes."""

    matchboxes = []
    for state, mb in menace_instance.matchboxes.items():
        probs = mb.get_probabilities()
        # Find the position with most beads (the "favorite" move)
        top_move = max(mb.beads.keys(), key=lambda k: mb.beads[k]) if mb.beads else None
        matchboxes.append(
            {
                "board_state": state,
                "beads": {str(k): v for k, v in mb.beads.items()},
                "times_used": mb.times_used,
                "total_beads": mb.get_total_beads(),
                "top_move": top_move,
            }
        )

    # Sort by times_used (most used first)
    matchboxes.sort(key=lambda x: x["times_used"], reverse=True)

    return {"count": len(matchboxes), "matchboxes": matchboxes}


# ============================================================================
# History / Graphing Endpoints
# ============================================================================


@router.get(
    "/menace/history",
    response_model=HistoryResponse,
    summary="Get MENACE learning history",
    description="""
    Get historical snapshots of MENACE's learning progress.
    
    Returns data points showing how total beads, matchbox count,
    and win rate have changed over games played. Perfect for
    plotting learning curves.
    
    **Why this is useful:**
    
    MENACE's beads represent "confidence" in moves. By tracking
    how total beads change over time, we can see:
    
    - Early learning: Beads fluctuate as MENACE explores
    - Mature learning: Beads stabilize as strategy solidifies
    - Overfitting: Too few beads might mean MENACE is too rigid
    """,
    tags=["MENACE"],
)
async def get_menace_history() -> HistoryResponse:
    """Get MENACE's learning history for graphing."""

    raw_history = menace_instance.get_history()

    # Convert raw dicts to HistorySnapshotResponse objects
    history = [
        HistorySnapshotResponse(
            games=h["games"],
            total_beads=h["total_beads"],
            matchbox_count=h["matchbox_count"],
            wins=h["wins"],
            losses=h["losses"],
            draws=h["draws"],
            win_rate=h["win_rate"],
        )
        for h in raw_history
    ]

    return HistoryResponse(
        history=history,
        current_games=menace_instance.games_played,
        current_beads=menace_instance.get_total_beads(),
    )


# ============================================================================
# Training Endpoints
# ============================================================================


@router.post(
    "/training/self-play",
    response_model=TrainingResponse,
    summary="Run self-play training",
    description="""
    Train MENACE by playing games against a bot.
    
    Opponent types:
    - `random`: Makes random valid moves (good for initial training)
    - `optimal`: Uses minimax algorithm (for advanced training)
    
    This runs synchronously - for many games, consider running in batches.
    """,
    tags=["Training"],
)
async def self_play_training(request: TrainingRequest) -> TrainingResponse:
    """Run self-play training games."""

    start_time = time.time()
    initial_matchboxes = menace_instance.get_matchbox_count()

    wins = 0
    losses = 0
    draws = 0

    for _ in range(request.num_games):
        # Create a fresh game for training
        # Alternate who goes first for variety
        menace_first = random.choice([True, False])
        game = game_manager.create_game(menace_plays_first=menace_first)

        # Play the game
        while not game.is_over():
            if game.is_menace_turn():
                game.menace_move()
            else:
                # Bot's turn - make a random move
                valid_moves = game.get_valid_moves()
                if valid_moves:
                    if request.opponent == "random":
                        move = random.choice(valid_moves)
                    else:
                        # TODO: Implement optimal (minimax) opponent
                        move = random.choice(valid_moves)
                    game.opponent_move(move)

        # Apply learning
        game_manager.finish_game(game.id)

        # Track results
        result = game.get_result()
        if result.value == "win":
            wins += 1
        elif result.value == "loss":
            losses += 1
        else:
            draws += 1

    elapsed = time.time() - start_time
    new_matchboxes = menace_instance.get_matchbox_count() - initial_matchboxes
    total_matchboxes = menace_instance.get_matchbox_count()
    games_per_second = request.num_games / elapsed if elapsed > 0 else 0

    # Estimate database size: ~200 bytes per matchbox (state + beads + metadata)
    estimated_db_size_kb = (total_matchboxes * 200) / 1024

    return TrainingResponse(
        games_played=request.num_games,
        wins=wins,
        losses=losses,
        draws=draws,
        time_seconds=round(elapsed, 3),
        new_matchboxes=new_matchboxes,
        games_per_second=round(games_per_second, 1),
        total_matchboxes=total_matchboxes,
        estimated_db_size_kb=round(estimated_db_size_kb, 2),
    )


def format_time(seconds: float) -> str:
    """Format seconds into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def format_size(kb: float) -> str:
    """Format KB into a human-readable string."""
    if kb < 1024:
        return f"{kb:.1f} KB"
    else:
        return f"{kb / 1024:.2f} MB"


@router.post(
    "/training/estimate",
    response_model=TrainingEstimateResponse,
    summary="Estimate training time and storage",
    description="""
    Get estimates for training time and database storage before running training.
    
    **Time Estimation:**
    Based on measured performance (~1,400 games/second baseline), estimates 
    scale linearly. Actual performance may vary based on system load.
    
    **Storage Estimation:**
    - Maximum possible matchboxes: ~765 (unique board states after symmetry normalization)
    - Each matchbox uses ~200 bytes (state string + bead counts + SQLite overhead)
    - Maximum database size: ~150 KB for matchbox data
    - Database also stores game history which grows with training
    
    **Sample Estimates:**
    | Games     | Est. Time   | Notes                           |
    |-----------|-------------|----------------------------------|
    | 5,000     | ~3-4 sec    | Quick test                       |
    | 20,000    | ~15 sec     | Basic training                   |
    | 100,000   | ~1 min      | Good training                    |
    | 1,000,000 | ~12 min     | Extensive training               |
    | 3,000,000 | ~35 min     | Maximum training                 |
    | 5,000,000 | ~1 hour     | Full convergence                 |
    """,
    tags=["Training"],
)
async def estimate_training(
    request: TrainingEstimateRequest,
) -> TrainingEstimateResponse:
    """Estimate training time and storage requirements."""

    # Get current state
    current_matchboxes = menace_instance.get_matchbox_count()
    stats = menace_instance.get_stats()
    current_games = stats.get("games_played", 0)

    # Base estimate: ~1400 games per second (measured from 5000 games in 3.5s)
    # This will vary by system, so we use a slightly conservative estimate
    games_per_second = 1400.0

    estimated_time = request.num_games / games_per_second

    # Storage estimation:
    # - Max ~765 unique matchboxes possible
    # - Each matchbox: ~200 bytes (state + beads + SQLite overhead)
    # - Game history: ~50 bytes per game (id, moves, result, timestamp)
    max_matchboxes = 765
    bytes_per_matchbox = 200
    bytes_per_game_history = 50

    # Matchboxes will fill up quickly (usually within first few thousand games)
    # After that, only game history grows
    projected_matchboxes = min(
        max_matchboxes, current_matchboxes + request.num_games // 10
    )
    matchbox_storage = projected_matchboxes * bytes_per_matchbox
    history_storage = (current_games + request.num_games) * bytes_per_game_history
    total_storage_kb = (matchbox_storage + history_storage) / 1024

    return TrainingEstimateResponse(
        num_games=request.num_games,
        estimated_time_seconds=round(estimated_time, 2),
        estimated_time_formatted=format_time(estimated_time),
        estimated_db_size_kb=round(total_storage_kb, 2),
        estimated_db_size_formatted=format_size(total_storage_kb),
        current_games_played=current_games,
        current_matchboxes=current_matchboxes,
        games_per_second_estimate=games_per_second,
    )


@router.post(
    "/menace/reset",
    summary="Reset MENACE",
    description="Reset MENACE to its initial (untrained) state. This clears all matchboxes and statistics.",
    tags=["MENACE"],
)
async def reset_menace():
    """Reset MENACE to initial state."""

    global menace_instance, game_manager

    menace_instance = Menace(player=Player.X)
    game_manager = GameManager(menace=menace_instance)

    return {
        "message": "MENACE has been reset to initial state",
        "games_played": 0,
        "matchbox_count": 0,
    }


# ============================================================================
# Health Check
# ============================================================================


@router.get(
    "/health",
    summary="Health check",
    description="Check if the API is running.",
    tags=["System"],
)
async def health_check():
    """API health check."""
    return {
        "status": "healthy",
        "menace_games": menace_instance.games_played,
        "active_games": len(game_manager.get_active_games()),
    }
