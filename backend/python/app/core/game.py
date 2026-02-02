"""
Game Module - Game Session Management

This module manages individual game sessions between a human (or bot)
and MENACE. It handles:
- Turn management
- Move validation
- Game state tracking
- Determining when the game is over

DESIGN DECISIONS:

1. Game as a State Machine:
   - A game progresses through states: NEW -> IN_PROGRESS -> FINISHED
   - Each state has allowed actions

2. Immutability for Boards:
   - Each move creates a new Board object
   - This makes it easy to track game history

3. Player Roles:
   - MENACE is always one player (X or O)
   - The opponent can be a human or a bot
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from app.core.board import Board, Player, GameResult
from app.core.menace import Menace


class GameState(Enum):
    """The current state of a game session."""

    WAITING_FOR_OPPONENT = "waiting_for_opponent"  # Opponent's turn
    WAITING_FOR_MENACE = "waiting_for_menace"  # MENACE's turn
    FINISHED = "finished"  # Game over


class OpponentType(Enum):
    """What kind of opponent is playing against MENACE."""

    HUMAN = "human"
    RANDOM_BOT = "random_bot"
    OPTIMAL_BOT = "optimal_bot"


@dataclass
class Move:
    """
    Records a single move in the game.

    Attributes:
        player: Who made the move (X or O)
        position: Where they moved (0-8)
        board_after: The board state after the move
        timestamp: When the move was made
    """

    player: Player
    position: int
    board_after: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "player": self.player.value,
            "position": self.position,
            "board_after": self.board_after,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Game:
    """
    Represents a single game session.

    This class manages the entire lifecycle of a game from start to finish.

    Attributes:
        id: Unique identifier for this game
        board: Current board state
        menace: Reference to the MENACE player
        menace_player: Which player MENACE is (X or O)
        current_turn: Whose turn it is
        moves: History of moves made
        result: Final result (None until game ends)
        created_at: When the game started

    Example Usage:
        menace = Menace(player=Player.X)
        game = Game(menace=menace)

        # MENACE plays first (X)
        game.menace_move()

        # Human responds
        game.opponent_move(4)

        # Continue until game over...
        if game.is_over():
            result = game.get_result()
            menace.learn(result)
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    board: Board = field(default_factory=Board)
    menace: Menace = None
    menace_player: Player = Player.X
    current_turn: Player = Player.X  # X always goes first
    moves: List[Move] = field(default_factory=list)
    result: Optional[GameResult] = None
    opponent_type: OpponentType = OpponentType.HUMAN
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Initialize after dataclass creation."""
        # Ensure menace player matches
        if self.menace is not None:
            self.menace_player = self.menace.player

    @property
    def state(self) -> GameState:
        """Get the current game state."""
        if self.is_over():
            return GameState.FINISHED
        elif self.current_turn == self.menace_player:
            return GameState.WAITING_FOR_MENACE
        else:
            return GameState.WAITING_FOR_OPPONENT

    def is_over(self) -> bool:
        """Check if the game has ended."""
        return self.board.is_game_over()

    def is_menace_turn(self) -> bool:
        """Check if it's MENACE's turn."""
        return self.current_turn == self.menace_player and not self.is_over()

    def is_opponent_turn(self) -> bool:
        """Check if it's the opponent's turn."""
        return self.current_turn != self.menace_player and not self.is_over()

    def get_result(self) -> GameResult:
        """
        Get the game result from MENACE's perspective.

        Returns:
            GameResult.WIN if MENACE won
            GameResult.LOSS if MENACE lost
            GameResult.DRAW if draw
            GameResult.IN_PROGRESS if game not over
        """
        return self.board.get_result(self.menace_player)

    def menace_move(self) -> Tuple[int, Board]:
        """
        Let MENACE make its move.

        Returns:
            Tuple of (position, new_board)

        Raises:
            ValueError: If it's not MENACE's turn or game is over
        """
        if self.is_over():
            raise ValueError("Game is already over")

        if not self.is_menace_turn():
            raise ValueError("It's not MENACE's turn")

        if self.menace is None:
            raise ValueError("No MENACE instance attached to game")

        # Get MENACE's move
        position = self.menace.get_move(self.board)

        # Make the move
        self.board = self.board.make_move(position, self.menace_player)

        # Record the move
        self.moves.append(
            Move(
                player=self.menace_player,
                position=position,
                board_after=self.board.state,
            )
        )

        # Switch turns
        self.current_turn = self.current_turn.other

        # Update result if game ended
        if self.is_over():
            self.result = self.get_result()

        return position, self.board

    def opponent_move(self, position: int) -> Board:
        """
        Process the opponent's (human/bot) move.

        Args:
            position: Where the opponent wants to play (0-8)

        Returns:
            The new board state

        Raises:
            ValueError: If it's not opponent's turn, game is over, or invalid move
        """
        if self.is_over():
            raise ValueError("Game is already over")

        if not self.is_opponent_turn():
            raise ValueError("It's not the opponent's turn")

        # Validate the position
        if position not in self.board.get_empty_positions():
            raise ValueError(f"Invalid move: position {position} is not available")

        opponent_player = self.menace_player.other

        # Make the move
        self.board = self.board.make_move(position, opponent_player)

        # Record the move
        self.moves.append(
            Move(
                player=opponent_player,
                position=position,
                board_after=self.board.state,
            )
        )

        # Switch turns
        self.current_turn = self.current_turn.other

        # Update result if game ended
        if self.is_over():
            self.result = self.get_result()

        return self.board

    def get_valid_moves(self) -> List[int]:
        """Get list of valid moves for the current player."""
        if self.is_over():
            return []
        return self.board.get_empty_positions()

    def to_dict(self) -> dict:
        """Convert game to dictionary for API response."""
        return {
            "id": self.id,
            "board": self.board.state,
            "current_turn": self.current_turn.value,
            "menace_player": self.menace_player.value,
            "state": self.state.value,
            "is_over": self.is_over(),
            "result": self.result.value if self.result else None,
            "valid_moves": self.get_valid_moves(),
            "moves": [m.to_dict() for m in self.moves],
            "created_at": self.created_at.isoformat(),
        }


class GameManager:
    """
    Manages multiple game sessions.

    This class keeps track of active games and provides methods
    to create and retrieve games.
    """

    def __init__(self, menace: Menace):
        """
        Initialize the game manager.

        Args:
            menace: The MENACE instance to use for all games
        """
        self.menace = menace
        self.games: dict[str, Game] = {}
        self.completed_games: List[str] = []

    def create_game(
        self,
        menace_plays_first: bool = True,
        opponent_type: OpponentType = OpponentType.HUMAN,
    ) -> Game:
        """
        Create a new game.

        Args:
            menace_plays_first: If True, MENACE is X and goes first
            opponent_type: What kind of opponent (human, random bot, etc.)

        Returns:
            The new Game object
        """
        # Reset MENACE for new game
        self.menace.reset_game()

        # Determine player assignment
        if menace_plays_first:
            self.menace.player = Player.X
        else:
            self.menace.player = Player.O

        game = Game(
            menace=self.menace,
            menace_player=self.menace.player,
            opponent_type=opponent_type,
        )

        self.games[game.id] = game
        return game

    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a game by ID."""
        return self.games.get(game_id)

    def finish_game(self, game_id: str):
        """
        Mark a game as finished and apply learning.

        Args:
            game_id: The ID of the game to finish
        """
        game = self.get_game(game_id)
        if game and game.is_over():
            # Apply learning
            self.menace.learn(game.get_result())

            # Track completion
            self.completed_games.append(game_id)

    def get_active_games(self) -> List[Game]:
        """Get all active (not finished) games."""
        return [g for g in self.games.values() if not g.is_over()]
