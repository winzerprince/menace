/*
Package menace implements the MENACE machine learning algorithm.

HOW MENACE LEARNS:

1. MATCHBOXES: Each unique game state has a "matchbox" containing "beads"
  - Each bead represents a possible move
  - More beads = higher probability of choosing that move

2. MAKING A MOVE: MENACE draws a random bead (weighted by count)

3. AFTER GAME ENDS:
  - WIN: Add beads to each move made (reward)
  - DRAW: Add fewer beads (small reward)
  - LOSS: Remove beads (punishment)

4. OVER TIME:
  - Winning moves accumulate beads
  - Losing moves lose beads
  - MENACE "learns" which moves lead to wins!
*/
package menace

import (
	"math/rand"
	"sync"

	"github.com/winzerprince/menace/backend/go/pkg/board"
)

// Matchbox represents a matchbox for a specific board state
type Matchbox struct {
	BoardState string      `json:"board_state"`
	Beads      map[int]int `json:"beads"`
	TimesUsed  int         `json:"times_used"`
}

// NewMatchbox creates a new matchbox for the given board state
func NewMatchbox(boardState string, validMoves []int, initialBeads int) *Matchbox {
	beads := make(map[int]int)
	for _, pos := range validMoves {
		beads[pos] = initialBeads
	}
	return &Matchbox{
		BoardState: boardState,
		Beads:      beads,
		TimesUsed:  0,
	}
}

// DrawBead draws a random bead weighted by count
func (m *Matchbox) DrawBead() int {
	if len(m.Beads) == 0 {
		return -1
	}

	// Create weighted list
	var weightedPositions []int
	for pos, count := range m.Beads {
		for i := 0; i < count; i++ {
			weightedPositions = append(weightedPositions, pos)
		}
	}

	if len(weightedPositions) == 0 {
		return -1
	}

	return weightedPositions[rand.Intn(len(weightedPositions))]
}

// AddBeads adds beads to a position (reward)
func (m *Matchbox) AddBeads(position, count int) {
	if _, exists := m.Beads[position]; exists {
		m.Beads[position] += count
	}
}

// RemoveBeads removes beads from a position (punishment)
func (m *Matchbox) RemoveBeads(position, count, minBeads int) {
	if current, exists := m.Beads[position]; exists {
		newCount := current - count
		if newCount < minBeads {
			newCount = minBeads
		}
		m.Beads[position] = newCount
	}
}

// GetTotalBeads returns the total beads in this matchbox
func (m *Matchbox) GetTotalBeads() int {
	total := 0
	for _, count := range m.Beads {
		total += count
	}
	return total
}

// GetProbabilities returns the probability of each move
func (m *Matchbox) GetProbabilities() map[int]float64 {
	total := m.GetTotalBeads()
	if total == 0 {
		return make(map[int]float64)
	}
	probs := make(map[int]float64)
	for pos, count := range m.Beads {
		probs[pos] = float64(count) / float64(total)
	}
	return probs
}

// MoveRecord records a single move made during a game
type MoveRecord struct {
	BoardState   string
	Position     int
	TransformIdx int
}

// HistorySnapshot stores learning state at a point in time
type HistorySnapshot struct {
	Games         int     `json:"games"`
	TotalBeads    int     `json:"total_beads"`
	MatchboxCount int     `json:"matchbox_count"`
	Wins          int     `json:"wins"`
	Losses        int     `json:"losses"`
	Draws         int     `json:"draws"`
	WinRate       float64 `json:"win_rate"`
}

// Menace is the MENACE machine learning agent
type Menace struct {
	mu          sync.RWMutex
	Matchboxes  map[string]*Matchbox
	Player      board.Player
	MoveHistory []MoveRecord
	History     []HistorySnapshot

	// Learning parameters
	InitialBeads int
	WinReward    int
	DrawReward   int
	LossPenalty  int
	MinBeads     int

	// Statistics
	GamesPlayed int
	Wins        int
	Losses      int
	Draws       int
}

// NewMenace creates a new MENACE agent
func NewMenace(player board.Player) *Menace {
	return &Menace{
		Matchboxes:   make(map[string]*Matchbox),
		Player:       player,
		MoveHistory:  make([]MoveRecord, 0),
		History:      make([]HistorySnapshot, 0),
		InitialBeads: 3,
		WinReward:    3,
		DrawReward:   1,
		LossPenalty:  1,
		MinBeads:     1,
		GamesPlayed:  0,
		Wins:         0,
		Losses:       0,
		Draws:        0,
	}
}

// GetOrCreateMatchbox gets or creates a matchbox for a normalized state
func (m *Menace) GetOrCreateMatchbox(normalizedState string, validMoves []int) *Matchbox {
	m.mu.Lock()
	defer m.mu.Unlock()

	if mb, exists := m.Matchboxes[normalizedState]; exists {
		return mb
	}

	mb := NewMatchbox(normalizedState, validMoves, m.InitialBeads)
	m.Matchboxes[normalizedState] = mb
	return mb
}

// GetMove selects a move for the given board state
func (m *Menace) GetMove(b *board.Board) int {
	// Normalize the board
	normalizedState, transformIdx := b.Normalize()

	// Get valid moves on the ORIGINAL board
	originalMoves := b.GetEmptyPositions()

	// Transform valid moves to normalized board positions
	normalizedMoves := make([]int, len(originalMoves))
	for i, pos := range originalMoves {
		normalizedMoves[i] = board.TransformPosition(pos, transformIdx)
	}

	// Get or create matchbox for normalized state
	matchbox := m.GetOrCreateMatchbox(normalizedState, normalizedMoves)

	m.mu.Lock()
	matchbox.TimesUsed++
	m.mu.Unlock()

	// Draw a bead (position on normalized board)
	normalizedPos := matchbox.DrawBead()

	// Transform back to original board position
	originalPos := board.InverseTransformPosition(normalizedPos, transformIdx)

	// Record this move for later learning
	m.mu.Lock()
	m.MoveHistory = append(m.MoveHistory, MoveRecord{
		BoardState:   normalizedState,
		Position:     normalizedPos,
		TransformIdx: transformIdx,
	})
	m.mu.Unlock()

	return originalPos
}

// Learn applies learning after a game ends
func (m *Menace) Learn(result board.GameResult) {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.GamesPlayed++

	// Track results
	switch result {
	case board.ResultWin:
		m.Wins++
	case board.ResultLoss:
		m.Losses++
	case board.ResultDraw:
		m.Draws++
	}

	// Apply rewards/penalties to each move made
	for _, move := range m.MoveHistory {
		mb := m.Matchboxes[move.BoardState]
		if mb == nil {
			continue
		}

		switch result {
		case board.ResultWin:
			mb.AddBeads(move.Position, m.WinReward)
		case board.ResultDraw:
			mb.AddBeads(move.Position, m.DrawReward)
		case board.ResultLoss:
			mb.RemoveBeads(move.Position, m.LossPenalty, m.MinBeads)
		}
	}

	// Clear move history for next game
	m.MoveHistory = make([]MoveRecord, 0)

	// Record history snapshot
	m.recordHistorySnapshot()
}

// recordHistorySnapshot records current state for graphing
func (m *Menace) recordHistorySnapshot() {
	// Only record every 10 games to avoid too much data
	if m.GamesPlayed%10 != 0 {
		return
	}

	winRate := 0.0
	if m.GamesPlayed > 0 {
		winRate = float64(m.Wins) / float64(m.GamesPlayed)
	}

	m.History = append(m.History, HistorySnapshot{
		Games:         m.GamesPlayed,
		TotalBeads:    m.getTotalBeadsUnsafe(),
		MatchboxCount: len(m.Matchboxes),
		Wins:          m.Wins,
		Losses:        m.Losses,
		Draws:         m.Draws,
		WinRate:       winRate,
	})
}

// StartNewGame clears move history for a new game
func (m *Menace) StartNewGame() {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.MoveHistory = make([]MoveRecord, 0)
}

// GetStatistics returns learning statistics
func (m *Menace) GetStatistics() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	winRate := 0.0
	if m.GamesPlayed > 0 {
		winRate = float64(m.Wins) / float64(m.GamesPlayed)
	}

	return map[string]interface{}{
		"games_played":   m.GamesPlayed,
		"wins":           m.Wins,
		"losses":         m.Losses,
		"draws":          m.Draws,
		"win_rate":       winRate,
		"matchbox_count": len(m.Matchboxes),
		"total_beads":    m.getTotalBeadsUnsafe(),
	}
}

// getTotalBeadsUnsafe returns total beads without locking (caller must hold lock)
func (m *Menace) getTotalBeadsUnsafe() int {
	total := 0
	for _, mb := range m.Matchboxes {
		total += mb.GetTotalBeads()
	}
	return total
}

// GetTotalBeads returns total beads across all matchboxes
func (m *Menace) GetTotalBeads() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.getTotalBeadsUnsafe()
}

// GetMatchboxCount returns number of matchboxes
func (m *Menace) GetMatchboxCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.Matchboxes)
}

// GetHistory returns the history snapshots
func (m *Menace) GetHistory() []HistorySnapshot {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// Return a copy to avoid race conditions
	result := make([]HistorySnapshot, len(m.History))
	copy(result, m.History)
	return result
}

// GetMatchboxData returns data for a specific matchbox
func (m *Menace) GetMatchboxData(boardState string) map[string]interface{} {
	// Try to normalize the state first
	normalized, _, err := board.NormalizeState(boardState)
	if err != nil {
		return nil
	}

	m.mu.RLock()
	defer m.mu.RUnlock()

	mb, exists := m.Matchboxes[normalized]
	if !exists {
		return nil
	}

	return map[string]interface{}{
		"board_state": mb.BoardState,
		"beads":       mb.Beads,
		"times_used":  mb.TimesUsed,
	}
}

// Reset resets MENACE to initial state
func (m *Menace) Reset() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.Matchboxes = make(map[string]*Matchbox)
	m.MoveHistory = make([]MoveRecord, 0)
	m.History = make([]HistorySnapshot, 0)
	m.GamesPlayed = 0
	m.Wins = 0
	m.Losses = 0
	m.Draws = 0
}
