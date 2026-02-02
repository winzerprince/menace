"""
Database Models

Simple dataclasses representing database records.

NOTE: We're using simple dataclasses instead of a full ORM like SQLAlchemy.
This keeps things simpler for learning purposes. In a larger project,
you might want to use SQLAlchemy for more complex queries and relationships.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class MatchboxModel:
    """
    Database model for a matchbox.

    Represents a row in the 'matchboxes' table.
    """

    board_state: str
    beads: Dict[int, int]
    times_used: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class GameModel:
    """
    Database model for a completed game.

    Represents a row in the 'games' table.
    """

    id: str
    result: str  # 'win', 'loss', 'draw'
    menace_player: str  # 'X' or 'O'
    moves: List[dict]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StatsSnapshot:
    """
    Database model for a statistics snapshot.

    Represents a row in the 'stats_snapshots' table.
    Used for tracking learning progress over time.
    """

    id: int
    games_played: int
    wins: int
    losses: int
    draws: int
    matchbox_count: int
    total_beads: int
    snapshot_at: datetime = field(default_factory=datetime.now)

    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played

    @property
    def loss_rate(self) -> float:
        """Calculate loss rate."""
        if self.games_played == 0:
            return 0.0
        return self.losses / self.games_played

    @property
    def draw_rate(self) -> float:
        """Calculate draw rate."""
        if self.games_played == 0:
            return 0.0
        return self.draws / self.games_played
