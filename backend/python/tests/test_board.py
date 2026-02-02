"""
Tests for the Board module.

These tests verify that the Board class correctly:
- Represents game state
- Makes moves
- Detects wins and draws
- Normalizes equivalent states
"""

import pytest
from app.core.board import Board, Player, GameResult


class TestBoardBasics:
    """Test basic board operations."""

    def test_empty_board_creation(self):
        """An empty board should have all underscores."""
        board = Board()
        assert board.state == "_________"

    def test_custom_board_creation(self):
        """Should be able to create a board with a custom state."""
        board = Board("X_O__X___")
        assert board.state == "X_O__X___"

    def test_invalid_board_length(self):
        """Should reject boards that aren't 9 characters."""
        with pytest.raises(ValueError):
            Board("XO")  # Too short

        with pytest.raises(ValueError):
            Board("X_O__X____")  # Too long

    def test_invalid_board_characters(self):
        """Should reject boards with invalid characters."""
        with pytest.raises(ValueError):
            Board("X_O__Y___")  # Y is not valid


class TestBoardMoves:
    """Test making moves on the board."""

    def test_make_move_on_empty_board(self):
        """Should be able to make a move on an empty board."""
        board = Board()
        new_board = board.make_move(4, Player.X)
        assert new_board.state == "____X____"

    def test_make_move_preserves_original(self):
        """Original board should not be modified."""
        board = Board()
        new_board = board.make_move(4, Player.X)
        assert board.state == "_________"  # Original unchanged
        assert new_board.state == "____X____"  # New board has move

    def test_make_move_on_occupied_position(self):
        """Should not be able to make a move on an occupied position."""
        board = Board("____X____")
        with pytest.raises(ValueError):
            board.make_move(4, Player.O)

    def test_make_move_invalid_position(self):
        """Should reject positions outside 0-8 range."""
        board = Board()
        with pytest.raises(ValueError):
            board.make_move(-1, Player.X)
        with pytest.raises(ValueError):
            board.make_move(9, Player.X)

    def test_get_empty_positions(self):
        """Should correctly identify empty positions."""
        board = Board("X_O__X___")
        expected = [1, 3, 4, 6, 7, 8]
        assert board.get_empty_positions() == expected

    def test_get_empty_positions_full_board(self):
        """Full board should have no empty positions."""
        board = Board("XOXOXOXOX")
        assert board.get_empty_positions() == []


class TestWinDetection:
    """Test win and draw detection."""

    def test_horizontal_wins(self):
        """Should detect horizontal wins."""
        # Top row
        assert Board("XXX______").check_winner() == Player.X
        # Middle row
        assert Board("___OOO___").check_winner() == Player.O
        # Bottom row
        assert Board("______XXX").check_winner() == Player.X

    def test_vertical_wins(self):
        """Should detect vertical wins."""
        # Left column
        assert Board("X__X__X__").check_winner() == Player.X
        # Middle column
        assert Board("_O__O__O_").check_winner() == Player.O
        # Right column
        assert Board("__X__X__X").check_winner() == Player.X

    def test_diagonal_wins(self):
        """Should detect diagonal wins."""
        # Top-left to bottom-right
        assert Board("X___X___X").check_winner() == Player.X
        # Top-right to bottom-left
        assert Board("__O_O_O__").check_winner() == Player.O

    def test_no_winner(self):
        """Should return None when there's no winner."""
        assert Board("_________").check_winner() is None
        assert Board("XOXOXOOXO").check_winner() is None  # Draw

    def test_is_draw(self):
        """Should correctly detect draws."""
        assert Board("XOXOXOOXO").is_draw() is True
        assert Board("XOXXOXOXO").is_draw() is True

    def test_not_draw_if_empty_squares(self):
        """Game with empty squares is not a draw."""
        assert Board("XOX______").is_draw() is False

    def test_not_draw_if_winner(self):
        """Game with a winner is not a draw."""
        # Full board but X wins
        assert Board("XXXOOXOOX").is_draw() is False

    def test_game_over(self):
        """Should correctly detect game over state."""
        assert Board("XXX______").is_game_over() is True  # Win
        assert Board("XOXOXOOXO").is_game_over() is True  # Draw
        assert Board("XO_______").is_game_over() is False  # In progress


class TestGameResult:
    """Test game result from MENACE's perspective."""

    def test_menace_wins(self):
        """Should return WIN when MENACE's player wins."""
        board = Board("XXX______")  # X wins
        assert board.get_result(Player.X) == GameResult.WIN
        assert board.get_result(Player.O) == GameResult.LOSS

    def test_menace_loses(self):
        """Should return LOSS when opponent wins."""
        board = Board("OOO______")  # O wins
        assert board.get_result(Player.X) == GameResult.LOSS
        assert board.get_result(Player.O) == GameResult.WIN

    def test_draw(self):
        """Should return DRAW when neither player wins."""
        board = Board("XOXOXOOXO")
        assert board.get_result(Player.X) == GameResult.DRAW
        assert board.get_result(Player.O) == GameResult.DRAW

    def test_in_progress(self):
        """Should return IN_PROGRESS when game is not over."""
        board = Board("X________")
        assert board.get_result(Player.X) == GameResult.IN_PROGRESS


class TestNormalization:
    """Test board state normalization."""

    def test_identity_normalization(self):
        """A normalized board should normalize to itself."""
        board = Board("X________")  # X in corner
        normalized, transform_idx = board.normalize()
        # The canonical form has X in position 0 (top-left)
        assert "X" in normalized
        assert len(normalized) == 9

    def test_rotation_equivalence(self):
        """Rotated boards should normalize to the same state."""
        # X in each corner should normalize to the same state
        boards = [
            Board("X________"),  # Top-left
            Board("__X______"),  # Top-right
            Board("______X__"),  # Bottom-left
            Board("________X"),  # Bottom-right
        ]

        normalized_states = [b.normalize()[0] for b in boards]
        # All should be the same
        assert all(s == normalized_states[0] for s in normalized_states)

    def test_position_transformation(self):
        """Should correctly transform positions."""
        board = Board()

        # Test that inverse transform undoes transform
        for pos in range(9):
            for transform_idx in range(8):
                transformed = board.transform_position(pos, transform_idx)
                restored = board.inverse_transform_position(transformed, transform_idx)
                assert restored == pos


class TestPlayerEnum:
    """Test the Player enum."""

    def test_player_other(self):
        """Should correctly return the other player."""
        assert Player.X.other == Player.O
        assert Player.O.other == Player.X

    def test_player_values(self):
        """Should have correct string values."""
        assert Player.X.value == "X"
        assert Player.O.value == "O"


class TestBoardStringRepresentation:
    """Test string representations."""

    def test_str_empty_board(self):
        """String representation should be readable."""
        board = Board()
        expected = "_ | _ | _\n---------\n_ | _ | _\n---------\n_ | _ | _"
        assert str(board) == expected

    def test_repr(self):
        """Repr should be valid Python."""
        board = Board("X_O__X___")
        assert repr(board) == "Board('X_O__X___')"

    def test_equality(self):
        """Boards with same state should be equal."""
        board1 = Board("X_O__X___")
        board2 = Board("X_O__X___")
        assert board1 == board2

    def test_hash(self):
        """Boards should be hashable for use as dict keys."""
        board1 = Board("X_O__X___")
        board2 = Board("X_O__X___")

        # Should be able to use as dict key
        d = {board1: "test"}
        assert d[board2] == "test"
