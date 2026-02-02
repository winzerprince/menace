/*
Package game manages individual game sessions between a human and MENACE.
*/
package game

import (
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/winzerprince/menace/backend/go/pkg/board"
	"github.com/winzerprince/menace/backend/go/pkg/menace"
)

// GameState represents the current state of a game
type GameState string

const (
	StateWaitingForOpponent GameState = "waiting_for_opponent"
	StateWaitingForMenace   GameState = "waiting_for_menace"
	StateFinished           GameState = "finished"
)

// Move records a single move in the game
type Move struct {
	Player     board.Player `json:"player"`
	Position   int          `json:"position"`
	BoardAfter string       `json:"board_after"`
	Timestamp  time.Time    `json:"timestamp"`
}

// Game represents a single game session
type Game struct {
	ID           string           `json:"id"`
	Board        *board.Board     `json:"-"`
	Menace       *menace.Menace   `json:"-"`
	MenacePlayer board.Player     `json:"menace_player"`
	CurrentTurn  board.Player     `json:"current_turn"`
	Moves        []Move           `json:"moves"`
	Result       board.GameResult `json:"result"`
	CreatedAt    time.Time        `json:"created_at"`
}

// NewGame creates a new game session
func NewGame(m *menace.Menace, menacePlaysFirst bool) *Game {
	menacePlayer := board.PlayerX
	if !menacePlaysFirst {
		menacePlayer = board.PlayerO
	}

	game := &Game{
		ID:           uuid.New().String(),
		Board:        board.NewEmpty(),
		Menace:       m,
		MenacePlayer: menacePlayer,
		CurrentTurn:  board.PlayerX, // X always goes first
		Moves:        make([]Move, 0),
		Result:       board.ResultInProgress,
		CreatedAt:    time.Now(),
	}

	m.StartNewGame()
	return game
}

// State returns the current game state
func (g *Game) State() GameState {
	if g.IsOver() {
		return StateFinished
	}
	if g.CurrentTurn == g.MenacePlayer {
		return StateWaitingForMenace
	}
	return StateWaitingForOpponent
}

// IsOver returns true if the game has ended
func (g *Game) IsOver() bool {
	return g.Board.IsGameOver()
}

// IsMenaceTurn returns true if it's MENACE's turn
func (g *Game) IsMenaceTurn() bool {
	return g.CurrentTurn == g.MenacePlayer && !g.IsOver()
}

// IsOpponentTurn returns true if it's the opponent's turn
func (g *Game) IsOpponentTurn() bool {
	return g.CurrentTurn != g.MenacePlayer && !g.IsOver()
}

// GetResult returns the game result from MENACE's perspective
func (g *Game) GetResult() board.GameResult {
	return g.Board.GetResult(g.MenacePlayer)
}

// GetValidMoves returns available positions
func (g *Game) GetValidMoves() []int {
	if g.IsOver() {
		return []int{}
	}
	return g.Board.GetEmptyPositions()
}

// MenaceMove lets MENACE make its move
func (g *Game) MenaceMove() (int, error) {
	if g.IsOver() {
		return -1, nil
	}
	if !g.IsMenaceTurn() {
		return -1, nil
	}

	position := g.Menace.GetMove(g.Board)

	newBoard, err := g.Board.MakeMove(position, g.MenacePlayer)
	if err != nil {
		return -1, err
	}

	g.Board = newBoard
	g.Moves = append(g.Moves, Move{
		Player:     g.MenacePlayer,
		Position:   position,
		BoardAfter: g.Board.State(),
		Timestamp:  time.Now(),
	})

	g.CurrentTurn = g.CurrentTurn.Other()

	if g.IsOver() {
		g.Result = g.GetResult()
	}

	return position, nil
}

// OpponentMove processes the opponent's move
func (g *Game) OpponentMove(position int) error {
	if g.IsOver() {
		return nil
	}
	if !g.IsOpponentTurn() {
		return nil
	}

	opponentPlayer := g.MenacePlayer.Other()
	newBoard, err := g.Board.MakeMove(position, opponentPlayer)
	if err != nil {
		return err
	}

	g.Board = newBoard
	g.Moves = append(g.Moves, Move{
		Player:     opponentPlayer,
		Position:   position,
		BoardAfter: g.Board.State(),
		Timestamp:  time.Now(),
	})

	g.CurrentTurn = g.CurrentTurn.Other()

	if g.IsOver() {
		g.Result = g.GetResult()
	}

	return nil
}

// GameManager manages active game sessions
type GameManager struct {
	mu     sync.RWMutex
	games  map[string]*Game
	menace *menace.Menace
}

// NewGameManager creates a new game manager
func NewGameManager(m *menace.Menace) *GameManager {
	return &GameManager{
		games:  make(map[string]*Game),
		menace: m,
	}
}

// CreateGame creates a new game
func (gm *GameManager) CreateGame(menacePlaysFirst bool) *Game {
	game := NewGame(gm.menace, menacePlaysFirst)

	gm.mu.Lock()
	gm.games[game.ID] = game
	gm.mu.Unlock()

	return game
}

// GetGame retrieves a game by ID
func (gm *GameManager) GetGame(id string) *Game {
	gm.mu.RLock()
	defer gm.mu.RUnlock()
	return gm.games[id]
}

// FinishGame applies learning and optionally removes the game
func (gm *GameManager) FinishGame(id string) {
	gm.mu.Lock()
	game, exists := gm.games[id]
	gm.mu.Unlock()

	if !exists || !game.IsOver() {
		return
	}

	// Apply learning
	result := game.GetResult()
	gm.menace.Learn(result)
}

// GetActiveGames returns all active game IDs
func (gm *GameManager) GetActiveGames() []string {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	ids := make([]string, 0, len(gm.games))
	for id, game := range gm.games {
		if !game.IsOver() {
			ids = append(ids, id)
		}
	}
	return ids
}

// SetMenace updates the menace instance
func (gm *GameManager) SetMenace(m *menace.Menace) {
	gm.mu.Lock()
	defer gm.mu.Unlock()
	gm.menace = m
	gm.games = make(map[string]*Game) // Clear all games
}
