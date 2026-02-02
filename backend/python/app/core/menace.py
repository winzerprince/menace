"""
MENACE Module - The Machine Learning Algorithm

This is the heart of MENACE - the algorithm that learns to play tic-tac-toe
through reinforcement learning.

HOW MENACE LEARNS:

1. MATCHBOXES: Each unique game state has a "matchbox" containing "beads"
   - Each bead represents a possible move
   - More beads = higher probability of choosing that move

2. MAKING A MOVE: MENACE draws a random bead (weighted by count)
   - If position 4 has 5 beads and position 0 has 2 beads,
     position 4 is ~2.5x more likely to be chosen

3. AFTER GAME ENDS:
   - WIN: Add beads to each move made (reward)
   - DRAW: Add fewer beads (small reward - draw is OK)
   - LOSS: Remove beads (punishment)

4. OVER TIME:
   - Winning moves accumulate beads (more likely)
   - Losing moves lose beads (less likely)
   - MENACE "learns" which moves lead to wins!

DESIGN DECISIONS:

1. Initial Beads: Each valid move starts with 3 beads
   - Enough randomness to explore different strategies
   - Not so many that learning takes forever

2. Rewards/Penalties:
   - Win: +3 beads per move
   - Draw: +1 bead per move
   - Loss: -1 bead per move
   - Minimum 1 bead (never completely remove a move option)

3. State Normalization:
   - We normalize board states to reduce unique matchboxes
   - This makes learning much faster!
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from app.core.board import Board, Player, GameResult


@dataclass
class Matchbox:
    """
    Represents a matchbox for a specific board state.

    In the physical MENACE, this was literally a matchbox with colored
    beads inside. Each color represented a different move position.

    Attributes:
        board_state: The normalized board state this matchbox is for
        beads: Dictionary mapping position (0-8) to bead count
        times_used: How many times this matchbox has been accessed

    Example:
        A matchbox for an empty board might look like:
        beads = {0: 3, 1: 3, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 3}

        After learning, it might become:
        beads = {0: 2, 1: 1, 2: 2, 3: 1, 4: 8, 5: 1, 6: 2, 7: 1, 8: 2}
        (Center move is now much more likely!)
    """

    board_state: str
    beads: Dict[int, int] = field(default_factory=dict)
    times_used: int = 0

    def draw_bead(self) -> int:
        """
        Draw a random bead (weighted by count).

        This simulates reaching into the matchbox and pulling out a bead.
        Positions with more beads are more likely to be chosen.

        Returns:
            The position (0-8) corresponding to the drawn bead

        Example:
            If beads = {0: 1, 4: 5, 8: 2}
            Position 4 has 5/(1+5+2) = 62.5% chance
            Position 0 has 1/8 = 12.5% chance
            Position 8 has 2/8 = 25% chance
        """
        if not self.beads:
            raise ValueError("Matchbox is empty - no moves available!")

        # Create a weighted list
        # e.g., {0: 2, 4: 3} becomes [0, 0, 4, 4, 4]
        weighted_positions = []
        for position, count in self.beads.items():
            weighted_positions.extend([position] * count)

        # Random choice from weighted list
        return random.choice(weighted_positions)

    def add_beads(self, position: int, count: int = 1):
        """
        Add beads to a position (reward).

        Args:
            position: The move position to reward
            count: How many beads to add
        """
        if position in self.beads:
            self.beads[position] += count

    def remove_beads(self, position: int, count: int = 1, min_beads: int = 1):
        """
        Remove beads from a position (punishment).

        Args:
            position: The move position to punish
            count: How many beads to remove
            min_beads: Minimum beads to keep (prevents removing move entirely)
        """
        if position in self.beads:
            self.beads[position] = max(min_beads, self.beads[position] - count)

    def get_total_beads(self) -> int:
        """Get the total number of beads in this matchbox."""
        return sum(self.beads.values())

    def get_probabilities(self) -> Dict[int, float]:
        """
        Get the probability of each move.

        Returns:
            Dictionary mapping position to probability (0.0 to 1.0)
        """
        total = self.get_total_beads()
        if total == 0:
            return {}
        return {pos: count / total for pos, count in self.beads.items()}

    def to_dict(self) -> dict:
        """Convert to a dictionary for JSON serialization."""
        return {
            "board_state": self.board_state,
            "beads": self.beads,
            "times_used": self.times_used,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Matchbox":
        """Create a Matchbox from a dictionary."""
        return cls(
            board_state=data["board_state"],
            beads={int(k): v for k, v in data["beads"].items()},
            times_used=data.get("times_used", 0),
        )


@dataclass
class MoveRecord:
    """
    Records a single move made during a game.

    Used to track MENACE's moves so we can apply learning after the game.
    """

    board_state: str  # The normalized board state
    position: int  # The position chosen (on normalized board)
    transform_idx: int  # The transformation used to normalize


class Menace:
    """
    The MENACE machine learning agent.

    This class manages all matchboxes and the learning process.

    Attributes:
        matchboxes: Dictionary mapping board states to Matchbox objects
        player: Which player MENACE is (X or O)
        move_history: Moves made in the current game (for learning)
        initial_beads: Starting beads for new matchboxes
        win_reward: Beads to add for each winning move
        draw_reward: Beads to add for each draw move
        loss_penalty: Beads to remove for each losing move

    Usage:
        menace = Menace(player=Player.X)

        # During game:
        move = menace.get_move(board)

        # After game:
        menace.learn(GameResult.WIN)
    """

    # Learning parameters - these can be tuned!
    DEFAULT_INITIAL_BEADS = 3  # Starting beads per valid position
    DEFAULT_WIN_REWARD = 3  # Beads added for winning moves
    DEFAULT_DRAW_REWARD = 1  # Beads added for draw moves
    DEFAULT_LOSS_PENALTY = 1  # Beads removed for losing moves
    MIN_BEADS = 1  # Never go below this (keeps move possible)

    def __init__(
        self,
        player: Player = Player.X,
        initial_beads: int = DEFAULT_INITIAL_BEADS,
        win_reward: int = DEFAULT_WIN_REWARD,
        draw_reward: int = DEFAULT_DRAW_REWARD,
        loss_penalty: int = DEFAULT_LOSS_PENALTY,
    ):
        """
        Initialize MENACE.

        Args:
            player: Which player MENACE will be (X or O)
            initial_beads: Starting beads for each valid move
            win_reward: Beads to add on win
            draw_reward: Beads to add on draw
            loss_penalty: Beads to remove on loss
        """
        self.player = player
        self.matchboxes: Dict[str, Matchbox] = {}
        self.move_history: List[MoveRecord] = []

        # Learning parameters
        self.initial_beads = initial_beads
        self.win_reward = win_reward
        self.draw_reward = draw_reward
        self.loss_penalty = loss_penalty

        # Statistics
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0

        # History tracking for graphs
        # Each entry: {games: int, total_beads: int, matchbox_count: int, wins: int, losses: int, draws: int}
        self.history: List[dict] = []

    def _get_or_create_matchbox(self, normalized_state: str, board: Board) -> Matchbox:
        """
        Get an existing matchbox or create a new one.

        If this is a new board state, we create a matchbox with
        initial beads for each empty position.

        Args:
            normalized_state: The normalized board state string
            board: The Board object (for finding empty positions)

        Returns:
            The Matchbox for this state
        """
        if normalized_state not in self.matchboxes:
            # Create new matchbox with initial beads
            # We need to find empty positions on the normalized board
            normalized_board = Board(normalized_state)
            empty_positions = normalized_board.get_empty_positions()

            # Initialize beads for each empty position
            beads = {pos: self.initial_beads for pos in empty_positions}

            self.matchboxes[normalized_state] = Matchbox(
                board_state=normalized_state, beads=beads
            )

        return self.matchboxes[normalized_state]

    def get_move(self, board: Board) -> int:
        """
        Get MENACE's move for the current board state.

        This is the main decision-making function. It:
        1. Normalizes the board state
        2. Gets (or creates) the matchbox for that state
        3. Draws a random bead to select the move
        4. Records the move for later learning
        5. Returns the move position on the ORIGINAL board

        Args:
            board: The current game board

        Returns:
            Position (0-8) on the original board where MENACE plays
        """
        # Step 1: Normalize the board
        normalized_state, transform_idx = board.normalize()

        # Step 2: Get the matchbox
        matchbox = self._get_or_create_matchbox(normalized_state, board)
        matchbox.times_used += 1

        # Step 3: Draw a bead (choose a move)
        normalized_position = matchbox.draw_bead()

        # Step 4: Record the move for learning
        self.move_history.append(
            MoveRecord(
                board_state=normalized_state,
                position=normalized_position,
                transform_idx=transform_idx,
            )
        )

        # Step 5: Transform position back to original board
        original_position = board.inverse_transform_position(
            normalized_position, transform_idx
        )

        return original_position

    def learn(self, result: GameResult):
        """
        Apply learning based on the game result.

        This is called after a game ends. Based on whether MENACE
        won, lost, or drew, we adjust the beads in each matchbox
        that was used during the game.

        Args:
            result: The game result (WIN, LOSS, or DRAW)
        """
        # Update statistics
        self.games_played += 1

        if result == GameResult.WIN:
            self.wins += 1
            reward = self.win_reward
        elif result == GameResult.DRAW:
            self.draws += 1
            reward = self.draw_reward
        elif result == GameResult.LOSS:
            self.losses += 1
            reward = -self.loss_penalty
        else:
            # Game still in progress - don't learn
            return

        # Apply learning to each move made
        for move in self.move_history:
            matchbox = self.matchboxes[move.board_state]

            if reward > 0:
                matchbox.add_beads(move.position, reward)
            else:
                matchbox.remove_beads(move.position, abs(reward), self.MIN_BEADS)

        # Clear move history for next game
        self.move_history = []

        # Record snapshot for history graph
        self._record_history_snapshot()

    def _record_history_snapshot(self):
        """
        Record a snapshot of current stats for history tracking.

        This is called after each game to track MENACE's learning
        progress over time, enabling visualization of bead growth.
        """
        # Only record every N games to keep history manageable
        # Record every game for first 100, then every 10, then every 100
        if self.games_played <= 100:
            record = True
        elif self.games_played <= 1000:
            record = self.games_played % 10 == 0
        else:
            record = self.games_played % 100 == 0

        if record:
            self.history.append(
                {
                    "games": self.games_played,
                    "total_beads": self.get_total_beads(),
                    "matchbox_count": self.get_matchbox_count(),
                    "wins": self.wins,
                    "losses": self.losses,
                    "draws": self.draws,
                    "win_rate": self.wins / max(1, self.games_played),
                }
            )

    def reset_game(self):
        """Reset for a new game (clear move history)."""
        self.move_history = []

    def get_matchbox_count(self) -> int:
        """Get the number of matchboxes MENACE has created."""
        return len(self.matchboxes)

    def get_total_beads(self) -> int:
        """Get the total beads across all matchboxes."""
        return sum(mb.get_total_beads() for mb in self.matchboxes.values())

    def get_statistics(self) -> dict:
        """Get MENACE's learning statistics."""
        return {
            "games_played": self.games_played,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "win_rate": self.wins / max(1, self.games_played),
            "matchbox_count": self.get_matchbox_count(),
            "total_beads": self.get_total_beads(),
        }

    def get_history(self) -> List[dict]:
        """
        Get the history of MENACE's learning progress.

        Returns a list of snapshots, each containing:
        - games: Number of games played at snapshot time
        - total_beads: Total beads across all matchboxes
        - matchbox_count: Number of matchboxes
        - wins, losses, draws: Cumulative counts
        - win_rate: Win percentage at that point

        Used for graphing bead growth over time.
        """
        return self.history.copy()

    def get_matchbox_data(self, board_state: str) -> Optional[dict]:
        """
        Get data about a specific matchbox.

        Args:
            board_state: The board state to look up

        Returns:
            Matchbox data or None if not found
        """
        # Normalize the state first
        board = Board(board_state)
        normalized_state, _ = board.normalize()

        if normalized_state in self.matchboxes:
            return self.matchboxes[normalized_state].to_dict()
        return None

    def to_dict(self) -> dict:
        """Serialize MENACE's state for persistence."""
        return {
            "player": self.player.value,
            "matchboxes": {
                state: mb.to_dict() for state, mb in self.matchboxes.items()
            },
            "games_played": self.games_played,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "initial_beads": self.initial_beads,
            "win_reward": self.win_reward,
            "draw_reward": self.draw_reward,
            "loss_penalty": self.loss_penalty,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Menace":
        """Load MENACE's state from a dictionary."""
        menace = cls(
            player=Player(data["player"]),
            initial_beads=data.get("initial_beads", cls.DEFAULT_INITIAL_BEADS),
            win_reward=data.get("win_reward", cls.DEFAULT_WIN_REWARD),
            draw_reward=data.get("draw_reward", cls.DEFAULT_DRAW_REWARD),
            loss_penalty=data.get("loss_penalty", cls.DEFAULT_LOSS_PENALTY),
        )

        menace.games_played = data.get("games_played", 0)
        menace.wins = data.get("wins", 0)
        menace.losses = data.get("losses", 0)
        menace.draws = data.get("draws", 0)

        menace.matchboxes = {
            state: Matchbox.from_dict(mb_data)
            for state, mb_data in data.get("matchboxes", {}).items()
        }

        menace.history = data.get("history", [])

        return menace
