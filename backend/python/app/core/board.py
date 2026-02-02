"""
Board Module - Tic-Tac-Toe Board Representation

This module handles everything related to the game board:
- Representing the board state
- Making moves
- Checking for wins/draws
- State normalization (handling rotations/reflections)

DESIGN DECISIONS:

1. Board Representation: String of 9 characters
   - Each position is 'X', 'O', or '_' (empty)
   - Positions are numbered 0-8:

     0 | 1 | 2
     ---------
     3 | 4 | 5
     ---------
     6 | 7 | 8

   - Example: "X_O__X___" means:
     X | _ | O
     ---------
     _ | _ | X
     ---------
     _ | _ | _

2. Why a string and not a 2D array?
   - Strings are immutable (safer)
   - Easy to use as dictionary keys
   - Simple to serialize for database storage
   - Easy to compare for equality

3. State Normalization:
   - A board can be rotated 4 ways and flipped 2 ways = 8 equivalent states
   - We normalize to the "smallest" string representation
   - This reduces the number of unique states MENACE needs to learn
"""

from enum import Enum
from typing import List, Optional, Tuple


class Player(Enum):
    """
    Represents the two players in the game.

    Using an Enum (enumeration) instead of strings like "X" and "O" because:
    - Prevents typos (can't accidentally use "x" or "0")
    - IDE autocomplete support
    - Type safety
    """

    X = "X"
    O = "O"

    @property
    def other(self) -> "Player":
        """Return the opposite player."""
        return Player.O if self == Player.X else Player.X


class GameResult(Enum):
    """
    Possible outcomes of a game.

    From MENACE's perspective:
    - WIN: MENACE won
    - LOSS: MENACE lost
    - DRAW: Neither player won
    - IN_PROGRESS: Game is still ongoing
    """

    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"
    IN_PROGRESS = "in_progress"


class Board:
    """
    Represents a Tic-Tac-Toe board and provides game logic.

    Attributes:
        state (str): The current board state as a 9-character string

    Example Usage:
        >>> board = Board()  # Empty board
        >>> board = board.make_move(4, Player.X)  # X in center
        >>> print(board)
        _ | _ | _
        ---------
        _ | X | _
        ---------
        _ | _ | _
    """

    # Winning combinations: indices that form a winning line
    # Each tuple represents 3 positions that, if all same, is a win
    WINNING_LINES = [
        (0, 1, 2),  # Top row
        (3, 4, 5),  # Middle row
        (6, 7, 8),  # Bottom row
        (0, 3, 6),  # Left column
        (1, 4, 7),  # Middle column
        (2, 5, 8),  # Right column
        (0, 4, 8),  # Diagonal top-left to bottom-right
        (2, 4, 6),  # Diagonal top-right to bottom-left
    ]

    # Transformation mappings for normalization
    # Each list shows where each position goes after the transformation
    #
    # Example: ROTATE_90 = [6, 3, 0, 7, 4, 1, 8, 5, 2]
    # means position 0 becomes position 6, position 1 becomes position 3, etc.
    #
    # Original:     After 90° rotation:
    # 0 | 1 | 2     6 | 3 | 0
    # ---------     ---------
    # 3 | 4 | 5  →  7 | 4 | 1
    # ---------     ---------
    # 6 | 7 | 8     8 | 5 | 2

    TRANSFORMATIONS = [
        [0, 1, 2, 3, 4, 5, 6, 7, 8],  # Identity (no change)
        [6, 3, 0, 7, 4, 1, 8, 5, 2],  # Rotate 90°
        [8, 7, 6, 5, 4, 3, 2, 1, 0],  # Rotate 180°
        [2, 5, 8, 1, 4, 7, 0, 3, 6],  # Rotate 270°
        [2, 1, 0, 5, 4, 3, 8, 7, 6],  # Flip horizontal
        [6, 7, 8, 3, 4, 5, 0, 1, 2],  # Flip vertical
        [0, 3, 6, 1, 4, 7, 2, 5, 8],  # Flip diagonal (transpose)
        [8, 5, 2, 7, 4, 1, 6, 3, 0],  # Flip anti-diagonal
    ]

    # Empty board constant
    EMPTY = "_________"

    def __init__(self, state: str = EMPTY):
        """
        Initialize a board with the given state.

        Args:
            state: A 9-character string representing the board.
                   Default is an empty board.

        Raises:
            ValueError: If state is invalid
        """
        # Validate the state
        if len(state) != 9:
            raise ValueError(f"Board state must be 9 characters, got {len(state)}")

        valid_chars = set("XO_")
        if not all(c in valid_chars for c in state):
            raise ValueError(f"Board state can only contain 'X', 'O', or '_'")

        self._state = state

    @property
    def state(self) -> str:
        """Get the board state as a string."""
        return self._state

    def get_square(self, position: int) -> Optional[Player]:
        """
        Get the player at a given position.

        Args:
            position: Board position (0-8)

        Returns:
            Player.X, Player.O, or None if empty
        """
        char = self._state[position]
        if char == "X":
            return Player.X
        elif char == "O":
            return Player.O
        return None

    def get_empty_positions(self) -> List[int]:
        """
        Get all positions that are currently empty.

        Returns:
            List of position indices (0-8) that are empty

        Example:
            >>> board = Board("X_O__X___")
            >>> board.get_empty_positions()
            [1, 3, 4, 6, 7, 8]
        """
        return [i for i, char in enumerate(self._state) if char == "_"]

    def make_move(self, position: int, player: Player) -> "Board":
        """
        Make a move on the board.

        This returns a NEW Board object - the original is not modified.
        This immutability makes the code safer and easier to reason about.

        Args:
            position: Where to place the piece (0-8)
            player: Which player is making the move

        Returns:
            A new Board with the move applied

        Raises:
            ValueError: If the position is invalid or already occupied

        Example:
            >>> board = Board()
            >>> new_board = board.make_move(4, Player.X)
            >>> new_board.state
            '____X____'
        """
        if position < 0 or position > 8:
            raise ValueError(f"Position must be 0-8, got {position}")

        if self._state[position] != "_":
            raise ValueError(f"Position {position} is already occupied")

        # Create new state with the move
        new_state = self._state[:position] + player.value + self._state[position + 1 :]
        return Board(new_state)

    def check_winner(self) -> Optional[Player]:
        """
        Check if there's a winner.

        Returns:
            Player.X or Player.O if there's a winner, None otherwise
        """
        for line in self.WINNING_LINES:
            a, b, c = line
            if (
                self._state[a] != "_"
                and self._state[a] == self._state[b] == self._state[c]
            ):
                return Player(self._state[a])
        return None

    def is_draw(self) -> bool:
        """
        Check if the game is a draw.

        A draw occurs when the board is full and there's no winner.

        Returns:
            True if it's a draw, False otherwise
        """
        return "_" not in self._state and self.check_winner() is None

    def is_game_over(self) -> bool:
        """Check if the game has ended (win or draw)."""
        return self.check_winner() is not None or self.is_draw()

    def get_result(self, menace_player: Player) -> GameResult:
        """
        Get the game result from MENACE's perspective.

        Args:
            menace_player: Which player MENACE is (X or O)

        Returns:
            GameResult indicating win/loss/draw/in_progress
        """
        winner = self.check_winner()

        if winner is not None:
            return GameResult.WIN if winner == menace_player else GameResult.LOSS
        elif self.is_draw():
            return GameResult.DRAW
        else:
            return GameResult.IN_PROGRESS

    def normalize(self) -> Tuple[str, int]:
        """
        Normalize the board state to its canonical form.

        Due to the symmetry of tic-tac-toe, many board positions are
        essentially equivalent (just rotated or flipped versions of each other).

        By normalizing to a canonical form, we:
        1. Reduce the number of states MENACE needs to learn
        2. Allow learning to transfer between equivalent positions

        Returns:
            A tuple of (normalized_state, transformation_index)
            The transformation_index can be used to map moves back
        """
        # Generate all 8 transformations and pick the "smallest" one
        # "Smallest" means the one that comes first alphabetically
        transformations = []

        for i, transform in enumerate(self.TRANSFORMATIONS):
            # Apply the transformation
            transformed = "".join(self._state[pos] for pos in transform)
            transformations.append((transformed, i))

        # Sort to find the canonical (smallest) form
        transformations.sort(key=lambda x: x[0])

        return transformations[0]

    def transform_position(self, position: int, transform_idx: int) -> int:
        """
        Transform a position according to a transformation.

        When we normalize a board, moves need to be transformed too.
        This function maps a position from the original board to
        the normalized board (or vice versa).

        Args:
            position: The original position (0-8)
            transform_idx: Which transformation to apply

        Returns:
            The transformed position
        """
        transform = self.TRANSFORMATIONS[transform_idx]
        # Find where this position ends up in the transformation
        return transform.index(position)

    def inverse_transform_position(self, position: int, transform_idx: int) -> int:
        """
        Reverse-transform a position.

        When MENACE chooses a move on the normalized board, we need
        to map it back to the original board.

        Args:
            position: Position on the normalized board
            transform_idx: The transformation that was applied

        Returns:
            The position on the original board
        """
        transform = self.TRANSFORMATIONS[transform_idx]
        return transform[position]

    def __str__(self) -> str:
        """Pretty-print the board for debugging."""
        rows = []
        for i in range(0, 9, 3):
            row = " | ".join(self._state[i : i + 3])
            rows.append(row)
        return "\n---------\n".join(rows)

    def __repr__(self) -> str:
        """Programmer-friendly representation."""
        return f"Board('{self._state}')"

    def __eq__(self, other: object) -> bool:
        """Check equality based on state."""
        if not isinstance(other, Board):
            return False
        return self._state == other._state

    def __hash__(self) -> int:
        """Allow boards to be used as dictionary keys."""
        return hash(self._state)
