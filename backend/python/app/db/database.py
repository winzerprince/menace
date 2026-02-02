"""
Database Connection Module

This module handles the SQLite database connection for persisting
MENACE's learned state and game history.

WHY SQLITE?

1. Zero Configuration:
   - No separate database server to install or configure
   - Just a single file that contains all data

2. Perfect for Learning:
   - Simple to understand and work with
   - Can open the database file directly to see data

3. Portable:
   - The database is just a file
   - Easy to backup, share, or reset

4. Sufficient Performance:
   - Handles millions of rows easily
   - More than enough for our use case

DATABASE LOCATION:
The database file is stored in the backend/python directory as 'menace.db'.
This file will be created automatically when the app starts.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# Database file path (relative to this file's location)
DB_PATH = Path(__file__).parent.parent.parent / "menace.db"


def get_connection() -> sqlite3.Connection:
    """
    Get a database connection.

    Returns:
        SQLite connection object
    """
    conn = sqlite3.connect(str(DB_PATH))
    # Return rows as dictionaries instead of tuples
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """
    Context manager for database connections.

    Usage:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM matchboxes")
            rows = cursor.fetchall()

    This ensures the connection is properly closed even if an error occurs.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Initialize the database with required tables.

    This creates all tables if they don't exist.
    Safe to call multiple times - won't overwrite existing data.
    """
    with get_db() as conn:
        # Matchboxes table - stores MENACE's learned states
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS matchboxes (
                board_state TEXT PRIMARY KEY,
                beads TEXT NOT NULL,
                times_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Games table - stores game history
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                result TEXT NOT NULL,
                menace_player TEXT NOT NULL,
                moves TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Stats snapshots - periodic snapshots for graphing progress
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS stats_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                games_played INTEGER NOT NULL,
                wins INTEGER NOT NULL,
                losses INTEGER NOT NULL,
                draws INTEGER NOT NULL,
                matchbox_count INTEGER NOT NULL,
                total_beads INTEGER NOT NULL,
                snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # MENACE state - single row storing overall MENACE state
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS menace_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                player TEXT NOT NULL DEFAULT 'X',
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                initial_beads INTEGER DEFAULT 3,
                win_reward INTEGER DEFAULT 3,
                draw_reward INTEGER DEFAULT 1,
                loss_penalty INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Insert default MENACE state if not exists
        conn.execute(
            """
            INSERT OR IGNORE INTO menace_state (id) VALUES (1)
        """
        )


def reset_db():
    """
    Reset the database by dropping all tables and recreating them.

    WARNING: This deletes all data!
    """
    with get_db() as conn:
        conn.execute("DROP TABLE IF EXISTS matchboxes")
        conn.execute("DROP TABLE IF EXISTS games")
        conn.execute("DROP TABLE IF EXISTS stats_snapshots")
        conn.execute("DROP TABLE IF EXISTS menace_state")

    init_db()


# ============================================================================
# Matchbox Operations
# ============================================================================


def save_matchbox(board_state: str, beads: dict, times_used: int = 0):
    """
    Save a matchbox to the database.

    Args:
        board_state: The normalized board state
        beads: Dictionary of position -> bead count
        times_used: How many times this matchbox has been used
    """
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO matchboxes (board_state, beads, times_used, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(board_state) DO UPDATE SET
                beads = excluded.beads,
                times_used = excluded.times_used,
                updated_at = CURRENT_TIMESTAMP
        """,
            (board_state, json.dumps(beads), times_used),
        )


def load_matchbox(board_state: str) -> Optional[dict]:
    """
    Load a matchbox from the database.

    Args:
        board_state: The normalized board state

    Returns:
        Dictionary with beads and times_used, or None if not found
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM matchboxes WHERE board_state = ?", (board_state,)
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return {
            "board_state": row["board_state"],
            "beads": json.loads(row["beads"]),
            "times_used": row["times_used"],
        }


def load_all_matchboxes() -> list:
    """
    Load all matchboxes from the database.

    Returns:
        List of matchbox dictionaries
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM matchboxes")
        rows = cursor.fetchall()

        return [
            {
                "board_state": row["board_state"],
                "beads": json.loads(row["beads"]),
                "times_used": row["times_used"],
            }
            for row in rows
        ]


def save_all_matchboxes(matchboxes: list):
    """
    Save multiple matchboxes to the database efficiently.

    Args:
        matchboxes: List of matchbox dictionaries
    """
    with get_db() as conn:
        for mb in matchboxes:
            conn.execute(
                """
                INSERT INTO matchboxes (board_state, beads, times_used, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(board_state) DO UPDATE SET
                    beads = excluded.beads,
                    times_used = excluded.times_used,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (mb["board_state"], json.dumps(mb["beads"]), mb["times_used"]),
            )


# ============================================================================
# Game History Operations
# ============================================================================


def save_game(game_id: str, result: str, menace_player: str, moves: list):
    """
    Save a completed game to the database.

    Args:
        game_id: Unique game identifier
        result: 'win', 'loss', or 'draw'
        menace_player: 'X' or 'O'
        moves: List of move dictionaries
    """
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO games (id, result, menace_player, moves)
            VALUES (?, ?, ?, ?)
        """,
            (game_id, result, menace_player, json.dumps(moves)),
        )


def get_game_history(limit: int = 100) -> list:
    """
    Get recent game history.

    Args:
        limit: Maximum number of games to return

    Returns:
        List of game dictionaries
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM games ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "result": row["result"],
                "menace_player": row["menace_player"],
                "moves": json.loads(row["moves"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]


# ============================================================================
# Statistics Operations
# ============================================================================


def save_stats_snapshot(
    games_played: int,
    wins: int,
    losses: int,
    draws: int,
    matchbox_count: int,
    total_beads: int,
):
    """
    Save a statistics snapshot for progress tracking.

    Args:
        games_played: Total games played
        wins: Total wins
        losses: Total losses
        draws: Total draws
        matchbox_count: Number of matchboxes
        total_beads: Total beads across all matchboxes
    """
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO stats_snapshots 
            (games_played, wins, losses, draws, matchbox_count, total_beads)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (games_played, wins, losses, draws, matchbox_count, total_beads),
        )


def get_stats_history(limit: int = 100) -> list:
    """
    Get statistics history for graphing.

    Args:
        limit: Maximum number of snapshots to return

    Returns:
        List of snapshot dictionaries
    """
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM stats_snapshots ORDER BY snapshot_at DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "games_played": row["games_played"],
                "wins": row["wins"],
                "losses": row["losses"],
                "draws": row["draws"],
                "matchbox_count": row["matchbox_count"],
                "total_beads": row["total_beads"],
                "snapshot_at": row["snapshot_at"],
            }
            for row in rows
        ]


# ============================================================================
# MENACE State Operations
# ============================================================================


def save_menace_state(state: dict):
    """
    Save MENACE's overall state.

    Args:
        state: Dictionary with MENACE's state
    """
    with get_db() as conn:
        conn.execute(
            """
            UPDATE menace_state SET
                player = ?,
                games_played = ?,
                wins = ?,
                losses = ?,
                draws = ?,
                initial_beads = ?,
                win_reward = ?,
                draw_reward = ?,
                loss_penalty = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """,
            (
                state.get("player", "X"),
                state.get("games_played", 0),
                state.get("wins", 0),
                state.get("losses", 0),
                state.get("draws", 0),
                state.get("initial_beads", 3),
                state.get("win_reward", 3),
                state.get("draw_reward", 1),
                state.get("loss_penalty", 1),
            ),
        )


def load_menace_state() -> dict:
    """
    Load MENACE's overall state.

    Returns:
        Dictionary with MENACE's state
    """
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM menace_state WHERE id = 1")
        row = cursor.fetchone()

        if row is None:
            return {}

        return {
            "player": row["player"],
            "games_played": row["games_played"],
            "wins": row["wins"],
            "losses": row["losses"],
            "draws": row["draws"],
            "initial_beads": row["initial_beads"],
            "win_reward": row["win_reward"],
            "draw_reward": row["draw_reward"],
            "loss_penalty": row["loss_penalty"],
        }
