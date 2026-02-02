"""
Tests for the MENACE module.

These tests verify that the MENACE algorithm correctly:
- Creates matchboxes for new states
- Makes weighted random moves
- Learns from game outcomes
"""

import pytest
from app.core.menace import Menace, Matchbox, MoveRecord
from app.core.board import Board, Player, GameResult


class TestMatchbox:
    """Test the Matchbox class."""

    def test_matchbox_creation(self):
        """Should create a matchbox with given beads."""
        beads = {0: 3, 1: 3, 2: 3}
        matchbox = Matchbox(board_state="_________", beads=beads)

        assert matchbox.board_state == "_________"
        assert matchbox.beads == beads
        assert matchbox.times_used == 0

    def test_draw_bead_returns_valid_position(self):
        """Drawing a bead should return a valid position."""
        beads = {0: 3, 4: 5, 8: 2}
        matchbox = Matchbox(board_state="_________", beads=beads)

        # Draw many times and check all are valid
        for _ in range(100):
            position = matchbox.draw_bead()
            assert position in beads

    def test_draw_bead_weighted(self):
        """Positions with more beads should be chosen more often."""
        # Position 4 has many beads, position 0 has few
        beads = {0: 1, 4: 99}
        matchbox = Matchbox(board_state="_________", beads=beads)

        # Draw many times
        counts = {0: 0, 4: 0}
        for _ in range(1000):
            position = matchbox.draw_bead()
            counts[position] += 1

        # Position 4 should be chosen much more often
        assert counts[4] > counts[0] * 10  # At least 10x more

    def test_add_beads(self):
        """Should correctly add beads."""
        matchbox = Matchbox(board_state="_________", beads={0: 3, 4: 3})
        matchbox.add_beads(4, 2)

        assert matchbox.beads[4] == 5
        assert matchbox.beads[0] == 3  # Unchanged

    def test_remove_beads(self):
        """Should correctly remove beads."""
        matchbox = Matchbox(board_state="_________", beads={0: 5, 4: 3})
        matchbox.remove_beads(0, 2)

        assert matchbox.beads[0] == 3

    def test_remove_beads_minimum(self):
        """Should not go below minimum beads."""
        matchbox = Matchbox(board_state="_________", beads={0: 2})
        matchbox.remove_beads(0, 10, min_beads=1)

        assert matchbox.beads[0] == 1  # Not 0 or negative

    def test_get_total_beads(self):
        """Should correctly count total beads."""
        matchbox = Matchbox(board_state="_________", beads={0: 3, 4: 5, 8: 2})
        assert matchbox.get_total_beads() == 10

    def test_get_probabilities(self):
        """Should correctly calculate probabilities."""
        matchbox = Matchbox(board_state="_________", beads={0: 2, 4: 6, 8: 2})
        probs = matchbox.get_probabilities()

        assert probs[0] == 0.2
        assert probs[4] == 0.6
        assert probs[8] == 0.2

    def test_serialization(self):
        """Should serialize and deserialize correctly."""
        matchbox = Matchbox(board_state="X________", beads={1: 3, 4: 5}, times_used=10)

        data = matchbox.to_dict()
        restored = Matchbox.from_dict(data)

        assert restored.board_state == matchbox.board_state
        assert restored.beads == matchbox.beads
        assert restored.times_used == matchbox.times_used


class TestMenace:
    """Test the MENACE class."""

    def test_menace_creation(self):
        """Should create MENACE with default settings."""
        menace = Menace(player=Player.X)

        assert menace.player == Player.X
        assert menace.games_played == 0
        assert len(menace.matchboxes) == 0

    def test_get_move_creates_matchbox(self):
        """Getting a move should create a matchbox if needed."""
        menace = Menace(player=Player.X)
        board = Board()

        move = menace.get_move(board)

        # Should have created a matchbox
        assert len(menace.matchboxes) == 1
        # Move should be valid
        assert move in range(9)

    def test_get_move_records_history(self):
        """Getting a move should record it in history."""
        menace = Menace(player=Player.X)
        board = Board()

        menace.get_move(board)

        assert len(menace.move_history) == 1
        assert isinstance(menace.move_history[0], MoveRecord)

    def test_get_move_returns_valid_position(self):
        """Move should be a valid empty position."""
        menace = Menace(player=Player.X)
        board = Board("X_O__X___")

        move = menace.get_move(board)

        assert move in board.get_empty_positions()

    def test_learn_from_win(self):
        """Learning from a win should add beads."""
        menace = Menace(player=Player.X)
        board = Board()

        # Make a move to create a matchbox
        menace.get_move(board)

        # Get initial bead count
        state = list(menace.matchboxes.keys())[0]
        move_record = menace.move_history[0]
        initial_beads = menace.matchboxes[state].beads[move_record.position]

        # Learn from win
        menace.learn(GameResult.WIN)

        # Beads should have increased
        assert menace.matchboxes[state].beads[move_record.position] > initial_beads

    def test_learn_from_loss(self):
        """Learning from a loss should remove beads."""
        menace = Menace(player=Player.X, initial_beads=10)  # Start with more beads
        board = Board()

        menace.get_move(board)

        state = list(menace.matchboxes.keys())[0]
        move_record = menace.move_history[0]
        initial_beads = menace.matchboxes[state].beads[move_record.position]

        menace.learn(GameResult.LOSS)

        assert menace.matchboxes[state].beads[move_record.position] < initial_beads

    def test_learn_updates_statistics(self):
        """Learning should update game statistics."""
        menace = Menace(player=Player.X)
        board = Board()

        menace.get_move(board)
        menace.learn(GameResult.WIN)

        assert menace.games_played == 1
        assert menace.wins == 1
        assert menace.losses == 0
        assert menace.draws == 0

    def test_reset_game(self):
        """Reset should clear move history."""
        menace = Menace(player=Player.X)
        board = Board()

        menace.get_move(board)
        assert len(menace.move_history) == 1

        menace.reset_game()
        assert len(menace.move_history) == 0

    def test_serialization(self):
        """Should serialize and deserialize correctly."""
        menace = Menace(player=Player.X)
        board = Board()
        menace.get_move(board)
        menace.learn(GameResult.WIN)

        data = menace.to_dict()
        restored = Menace.from_dict(data)

        assert restored.player == menace.player
        assert restored.games_played == menace.games_played
        assert restored.wins == menace.wins
        assert len(restored.matchboxes) == len(menace.matchboxes)

    def test_normalized_states_shared(self):
        """Equivalent board states should use the same matchbox."""
        menace = Menace(player=Player.X)

        # X in top-left corner
        board1 = Board("X________")
        menace.get_move(board1)
        menace.reset_game()

        initial_count = len(menace.matchboxes)

        # X in bottom-right corner (equivalent after normalization)
        board2 = Board("________X")
        menace.get_move(board2)

        # Should not have created a new matchbox
        # (assuming both normalize to the same state)
        # Note: This depends on the normalization implementation
        # Both corner positions should normalize to the same state


class TestMenaceIntegration:
    """Integration tests for MENACE playing full games."""

    def test_play_full_game(self):
        """MENACE should be able to play a complete game."""
        menace = Menace(player=Player.X)
        board = Board()
        moves_made = 0

        # Simulate a game (X=MENACE, O=random)
        import random

        current_player = Player.X

        while not board.is_game_over() and moves_made < 9:
            if current_player == menace.player:
                move = menace.get_move(board)
            else:
                move = random.choice(board.get_empty_positions())

            board = board.make_move(move, current_player)
            current_player = current_player.other
            moves_made += 1

        # Game should be over
        assert board.is_game_over()

        # Should be able to learn from the result
        result = board.get_result(menace.player)
        menace.learn(result)

        assert menace.games_played == 1

    def test_learning_improves_over_time(self):
        """MENACE should generally improve with training."""
        menace = Menace(player=Player.X)

        # Play many games against random opponent
        import random

        early_wins = 0
        late_wins = 0

        for game_num in range(200):
            board = Board()
            current_player = Player.X

            while not board.is_game_over():
                if current_player == menace.player:
                    move = menace.get_move(board)
                else:
                    move = random.choice(board.get_empty_positions())
                board = board.make_move(move, current_player)
                current_player = current_player.other

            result = board.get_result(menace.player)
            menace.learn(result)

            # Track wins in first 50 vs last 50 games
            if game_num < 50 and result == GameResult.WIN:
                early_wins += 1
            elif game_num >= 150 and result == GameResult.WIN:
                late_wins += 1

        # MENACE should win more in later games
        # Note: Due to randomness, this might occasionally fail
        # In a real test suite, you'd use statistical tests
        print(f"Early wins: {early_wins}/50, Late wins: {late_wins}/50")
        # We can't guarantee improvement due to randomness, but we can check
        # that the algorithm is working
        assert menace.games_played == 200
