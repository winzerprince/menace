/*
Package board provides the tic-tac-toe board representation and game logic.

DESIGN DECISIONS:

1. Board Representation: String of 9 characters

  - Each position is 'X', 'O', or '_' (empty)

  - Positions are numbered 0-8:

    0 | 1 | 2
    ---------
    3 | 4 | 5
    ---------
    6 | 7 | 8

2. State Normalization:
  - A board can be rotated 4 ways and flipped 2 ways = 8 equivalent states
  - We normalize to the "smallest" string representation
  - This reduces the number of unique states MENACE needs to learn
*/
package board

import (
	"errors"
	"sort"
	"strings"
)

// Player represents the two players in the game
type Player string

const (
	PlayerX    Player = "X"
	PlayerO    Player = "O"
	PlayerNone Player = "_"
)

// Other returns the opposite player
func (p Player) Other() Player {
	if p == PlayerX {
		return PlayerO
	}
	return PlayerX
}

// GameResult represents possible outcomes of a game
type GameResult string

const (
	ResultWin        GameResult = "win"
	ResultLoss       GameResult = "loss"
	ResultDraw       GameResult = "draw"
	ResultInProgress GameResult = "in_progress"
)

// WinningLines contains all possible winning combinations
// Each slice represents 3 positions that form a winning line
var WinningLines = [][]int{
	{0, 1, 2}, // Top row
	{3, 4, 5}, // Middle row
	{6, 7, 8}, // Bottom row
	{0, 3, 6}, // Left column
	{1, 4, 7}, // Middle column
	{2, 5, 8}, // Right column
	{0, 4, 8}, // Diagonal top-left to bottom-right
	{2, 4, 6}, // Diagonal top-right to bottom-left
}

// Transformations contains mappings for board rotations and reflections
// Each slice shows where each position maps to after transformation
var Transformations = [][]int{
	{0, 1, 2, 3, 4, 5, 6, 7, 8}, // Identity
	{6, 3, 0, 7, 4, 1, 8, 5, 2}, // Rotate 90°
	{8, 7, 6, 5, 4, 3, 2, 1, 0}, // Rotate 180°
	{2, 5, 8, 1, 4, 7, 0, 3, 6}, // Rotate 270°
	{2, 1, 0, 5, 4, 3, 8, 7, 6}, // Flip horizontal
	{6, 7, 8, 3, 4, 5, 0, 1, 2}, // Flip vertical
	{0, 3, 6, 1, 4, 7, 2, 5, 8}, // Flip diagonal
	{8, 5, 2, 7, 4, 1, 6, 3, 0}, // Flip anti-diagonal
}

// EmptyBoard is the initial empty board state
const EmptyBoard = "_________"

// Board represents a tic-tac-toe board
type Board struct {
	state string
}

// New creates a new board with the given state
func New(state string) (*Board, error) {
	if len(state) != 9 {
		return nil, errors.New("board state must be 9 characters")
	}
	for _, c := range state {
		if c != 'X' && c != 'O' && c != '_' {
			return nil, errors.New("board state can only contain 'X', 'O', or '_'")
		}
	}
	return &Board{state: state}, nil
}

// NewEmpty creates a new empty board
func NewEmpty() *Board {
	return &Board{state: EmptyBoard}
}

// State returns the board state as a string
func (b *Board) State() string {
	return b.state
}

// GetSquare returns the player at a given position (or PlayerNone if empty)
func (b *Board) GetSquare(position int) Player {
	char := b.state[position]
	switch char {
	case 'X':
		return PlayerX
	case 'O':
		return PlayerO
	default:
		return PlayerNone
	}
}

// GetEmptyPositions returns all positions that are empty
func (b *Board) GetEmptyPositions() []int {
	positions := make([]int, 0)
	for i, c := range b.state {
		if c == '_' {
			positions = append(positions, i)
		}
	}
	return positions
}

// MakeMove creates a new board with the move applied
// The original board is not modified (immutability)
func (b *Board) MakeMove(position int, player Player) (*Board, error) {
	if position < 0 || position > 8 {
		return nil, errors.New("position must be 0-8")
	}
	if b.state[position] != '_' {
		return nil, errors.New("position is already occupied")
	}

	// Create new state with the move
	newState := []byte(b.state)
	newState[position] = player[0]

	return &Board{state: string(newState)}, nil
}

// CheckWinner returns the winning player, or PlayerNone if no winner yet
func (b *Board) CheckWinner() Player {
	for _, line := range WinningLines {
		a, c, d := b.state[line[0]], b.state[line[1]], b.state[line[2]]
		if a != '_' && a == c && c == d {
			return Player(string(a))
		}
	}
	return PlayerNone
}

// IsFull returns true if the board has no empty spaces
func (b *Board) IsFull() bool {
	return !strings.Contains(b.state, "_")
}

// IsGameOver returns true if the game has ended (win or draw)
func (b *Board) IsGameOver() bool {
	return b.CheckWinner() != PlayerNone || b.IsFull()
}

// GetResult returns the game result from the given player's perspective
func (b *Board) GetResult(player Player) GameResult {
	winner := b.CheckWinner()
	if winner == PlayerNone {
		if b.IsFull() {
			return ResultDraw
		}
		return ResultInProgress
	}
	if winner == player {
		return ResultWin
	}
	return ResultLoss
}

// applyTransform applies a transformation to the board state
func applyTransform(state string, transform []int) string {
	result := make([]byte, 9)
	for newPos, oldPos := range transform {
		result[newPos] = state[oldPos]
	}
	return string(result)
}

// inverseTransform applies the inverse of a transformation to a position
// This maps a position on the normalized board back to the original board
func inverseTransform(position int, transformIdx int) int {
	transform := Transformations[transformIdx]
	for origPos, normPos := range transform {
		if normPos == position {
			return origPos
		}
	}
	return position
}

// Normalize returns the normalized board state and the transformation index used
// The normalized state is the lexicographically smallest among all rotations/reflections
func (b *Board) Normalize() (string, int) {
	variants := make([]struct {
		state string
		idx   int
	}, len(Transformations))

	for i, transform := range Transformations {
		variants[i] = struct {
			state string
			idx   int
		}{
			state: applyTransform(b.state, transform),
			idx:   i,
		}
	}

	// Sort by state string to find the smallest
	sort.Slice(variants, func(i, j int) bool {
		return variants[i].state < variants[j].state
	})

	return variants[0].state, variants[0].idx
}

// NormalizeState is a convenience function to normalize a state string
func NormalizeState(state string) (string, int, error) {
	board, err := New(state)
	if err != nil {
		return "", 0, err
	}
	normalized, idx := board.Normalize()
	return normalized, idx, nil
}

// TransformPosition converts a position from original board to normalized board
func TransformPosition(position int, transformIdx int) int {
	return Transformations[transformIdx][position]
}

// InverseTransformPosition converts a position from normalized board to original board
func InverseTransformPosition(position int, transformIdx int) int {
	return inverseTransform(position, transformIdx)
}

// String returns a visual representation of the board
func (b *Board) String() string {
	return b.state[0:1] + " | " + b.state[1:2] + " | " + b.state[2:3] + "\n" +
		"---------\n" +
		b.state[3:4] + " | " + b.state[4:5] + " | " + b.state[5:6] + "\n" +
		"---------\n" +
		b.state[6:7] + " | " + b.state[7:8] + " | " + b.state[8:9]
}
