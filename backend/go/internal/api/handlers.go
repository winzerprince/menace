/*
Package api provides the HTTP API handlers for the MENACE backend.
*/
package api

import (
	"fmt"
	"math/rand"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/winzerprince/menace/backend/go/pkg/board"
	"github.com/winzerprince/menace/backend/go/pkg/game"
	"github.com/winzerprince/menace/backend/go/pkg/menace"
)

// Handler contains the API handlers and dependencies
type Handler struct {
	menace      *menace.Menace
	gameManager *game.GameManager
}

// NewHandler creates a new API handler
func NewHandler() *Handler {
	m := menace.NewMenace(board.PlayerX)
	gm := game.NewGameManager(m)
	return &Handler{
		menace:      m,
		gameManager: gm,
	}
}

// ============================================================================
// Request/Response Types
// ============================================================================

type NewGameRequest struct {
	MenacePlaysFirst bool `json:"menace_plays_first"`
}

type NewGameResponse struct {
	GameID       string `json:"game_id"`
	Board        string `json:"board"`
	CurrentTurn  string `json:"current_turn"`
	MenacePlayer string `json:"menace_player"`
	Status       string `json:"status"`
	ValidMoves   []int  `json:"valid_moves"`
	MenaceMove   *int   `json:"menace_move"`
}

type MoveRequest struct {
	Position int `json:"position" binding:"min=0,max=8"`
}

type MoveResponse struct {
	Board        string  `json:"board"`
	CurrentTurn  *string `json:"current_turn"`
	Status       string  `json:"status"`
	ValidMoves   []int   `json:"valid_moves"`
	OpponentMove int     `json:"opponent_move"`
	MenaceMove   *int    `json:"menace_move"`
	IsGameOver   bool    `json:"is_game_over"`
	Result       *string `json:"result"`
	Winner       *string `json:"winner"`
}

type GameStateResponse struct {
	GameID       string  `json:"game_id"`
	Board        string  `json:"board"`
	CurrentTurn  *string `json:"current_turn"`
	MenacePlayer string  `json:"menace_player"`
	Status       string  `json:"status"`
	ValidMoves   []int   `json:"valid_moves"`
	IsGameOver   bool    `json:"is_game_over"`
	Result       *string `json:"result"`
	Winner       *string `json:"winner"`
	MoveCount    int     `json:"move_count"`
}

type MenaceStatsResponse struct {
	GamesPlayed   int     `json:"games_played"`
	Wins          int     `json:"wins"`
	Losses        int     `json:"losses"`
	Draws         int     `json:"draws"`
	WinRate       float64 `json:"win_rate"`
	MatchboxCount int     `json:"matchbox_count"`
	TotalBeads    int     `json:"total_beads"`
}

type MatchboxResponse struct {
	BoardState    string             `json:"board_state"`
	Beads         map[string]int     `json:"beads"`
	TimesUsed     int                `json:"times_used"`
	Probabilities map[string]float64 `json:"probabilities"`
}

type MatchboxQueryRequest struct {
	BoardState string `json:"board_state" binding:"required,len=9"`
}

type TrainingRequest struct {
	NumGames int    `json:"num_games" binding:"min=1,max=5000000"`
	Opponent string `json:"opponent"`
}

type TrainingResponse struct {
	GamesPlayed      int     `json:"games_played"`
	Wins             int     `json:"wins"`
	Losses           int     `json:"losses"`
	Draws            int     `json:"draws"`
	TimeSeconds      float64 `json:"time_seconds"`
	NewMatchboxes    int     `json:"new_matchboxes"`
	GamesPerSecond   float64 `json:"games_per_second"`
	TotalMatchboxes  int     `json:"total_matchboxes"`
	EstimatedDBSizeKB float64 `json:"estimated_db_size_kb"`
}

type TrainingEstimateRequest struct {
	NumGames int `json:"num_games" binding:"required,min=1,max=5000000"`
}

type TrainingEstimateResponse struct {
	NumGames              int     `json:"num_games"`
	EstimatedTimeSeconds  float64 `json:"estimated_time_seconds"`
	EstimatedTimeFormatted string `json:"estimated_time_formatted"`
	EstimatedDBSizeKB     float64 `json:"estimated_db_size_kb"`
	EstimatedDBSizeFormatted string `json:"estimated_db_size_formatted"`
	CurrentGamesPlayed    int     `json:"current_games_played"`
	CurrentMatchboxes     int     `json:"current_matchboxes"`
	GamesPerSecondEstimate float64 `json:"games_per_second_estimate"`
}

type HistorySnapshotResponse struct {
	Games         int     `json:"games"`
	TotalBeads    int     `json:"total_beads"`
	MatchboxCount int     `json:"matchbox_count"`
	Wins          int     `json:"wins"`
	Losses        int     `json:"losses"`
	Draws         int     `json:"draws"`
	WinRate       float64 `json:"win_rate"`
}

type HistoryResponse struct {
	History      []HistorySnapshotResponse `json:"history"`
	CurrentGames int                       `json:"current_games"`
	CurrentBeads int                       `json:"current_beads"`
}

// ============================================================================
// Helper Functions
// ============================================================================

func getPlayerSymbol(p board.Player) string {
	if p == board.PlayerX {
		return "X"
	}
	return "O"
}

func getGameStatus(g *game.Game) string {
	if g.IsOver() {
		return "finished"
	}
	if g.IsMenaceTurn() {
		return "waiting_for_menace"
	}
	return "waiting_for_opponent"
}

func getResultType(g *game.Game) *string {
	if !g.IsOver() {
		return nil
	}
	result := string(g.GetResult())
	return &result
}

func getWinner(g *game.Game) *string {
	winner := g.Board.CheckWinner()
	if winner == board.PlayerNone {
		return nil
	}
	s := getPlayerSymbol(winner)
	return &s
}

// ============================================================================
// Game Endpoints
// ============================================================================

// NewGame creates a new game session
// POST /api/game/new
func (h *Handler) NewGame(c *gin.Context) {
	var req NewGameRequest
	req.MenacePlaysFirst = true // Default

	if err := c.ShouldBindJSON(&req); err != nil && c.Request.ContentLength > 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	g := h.gameManager.CreateGame(req.MenacePlaysFirst)

	var menaceMove *int

	// If MENACE plays first, make the opening move
	if req.MenacePlaysFirst {
		pos, err := g.MenaceMove()
		if err == nil && pos >= 0 {
			menaceMove = &pos
		}
	}

	currentTurn := getPlayerSymbol(g.CurrentTurn)

	c.JSON(http.StatusOK, NewGameResponse{
		GameID:       g.ID,
		Board:        g.Board.State(),
		CurrentTurn:  currentTurn,
		MenacePlayer: getPlayerSymbol(g.MenacePlayer),
		Status:       getGameStatus(g),
		ValidMoves:   g.GetValidMoves(),
		MenaceMove:   menaceMove,
	})
}

// MakeMove processes a move
// POST /api/game/:id/move
func (h *Handler) MakeMove(c *gin.Context) {
	gameID := c.Param("id")

	g := h.gameManager.GetGame(gameID)
	if g == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Game not found: " + gameID})
		return
	}

	if g.IsOver() {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Game is already over"})
		return
	}

	if !g.IsOpponentTurn() {
		c.JSON(http.StatusBadRequest, gin.H{"error": "It's not your turn - waiting for MENACE"})
		return
	}

	var req MoveRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Check if move is valid
	validMoves := g.GetValidMoves()
	isValid := false
	for _, m := range validMoves {
		if m == req.Position {
			isValid = true
			break
		}
	}
	if !isValid {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":       "Invalid move: position is not available",
			"valid_moves": validMoves,
		})
		return
	}

	// Make opponent's move
	if err := g.OpponentMove(req.Position); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	var menaceMove *int

	// If game continues and it's MENACE's turn, let MENACE respond
	if !g.IsOver() && g.IsMenaceTurn() {
		pos, err := g.MenaceMove()
		if err == nil && pos >= 0 {
			menaceMove = &pos
		}
	}

	// If game ended, apply learning
	if g.IsOver() {
		h.gameManager.FinishGame(gameID)
	}

	var currentTurn *string
	if !g.IsOver() {
		ct := getPlayerSymbol(g.CurrentTurn)
		currentTurn = &ct
	}

	c.JSON(http.StatusOK, MoveResponse{
		Board:        g.Board.State(),
		CurrentTurn:  currentTurn,
		Status:       getGameStatus(g),
		ValidMoves:   g.GetValidMoves(),
		OpponentMove: req.Position,
		MenaceMove:   menaceMove,
		IsGameOver:   g.IsOver(),
		Result:       getResultType(g),
		Winner:       getWinner(g),
	})
}

// GetGameState retrieves current game state
// GET /api/game/:id
func (h *Handler) GetGameState(c *gin.Context) {
	gameID := c.Param("id")

	g := h.gameManager.GetGame(gameID)
	if g == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Game not found: " + gameID})
		return
	}

	var currentTurn *string
	if !g.IsOver() {
		ct := getPlayerSymbol(g.CurrentTurn)
		currentTurn = &ct
	}

	c.JSON(http.StatusOK, GameStateResponse{
		GameID:       g.ID,
		Board:        g.Board.State(),
		CurrentTurn:  currentTurn,
		MenacePlayer: getPlayerSymbol(g.MenacePlayer),
		Status:       getGameStatus(g),
		ValidMoves:   g.GetValidMoves(),
		IsGameOver:   g.IsOver(),
		Result:       getResultType(g),
		Winner:       getWinner(g),
		MoveCount:    len(g.Moves),
	})
}

// ============================================================================
// MENACE Statistics Endpoints
// ============================================================================

// GetMenaceStats returns MENACE's learning statistics
// GET /api/menace/stats
func (h *Handler) GetMenaceStats(c *gin.Context) {
	stats := h.menace.GetStatistics()

	c.JSON(http.StatusOK, MenaceStatsResponse{
		GamesPlayed:   stats["games_played"].(int),
		Wins:          stats["wins"].(int),
		Losses:        stats["losses"].(int),
		Draws:         stats["draws"].(int),
		WinRate:       stats["win_rate"].(float64),
		MatchboxCount: stats["matchbox_count"].(int),
		TotalBeads:    stats["total_beads"].(int),
	})
}

// QueryMatchbox returns data for a specific matchbox
// POST /api/menace/matchbox
func (h *Handler) QueryMatchbox(c *gin.Context) {
	var req MatchboxQueryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	data := h.menace.GetMatchboxData(req.BoardState)
	if data == nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "No matchbox found for state: " + req.BoardState})
		return
	}

	// Get the matchbox to calculate probabilities
	normalized, _, _ := board.NormalizeState(req.BoardState)

	beads := data["beads"].(map[int]int)
	beadsStr := make(map[string]int)
	for k, v := range beads {
		beadsStr[strconv.Itoa(k)] = v
	}

	// Calculate probabilities
	total := 0
	for _, v := range beads {
		total += v
	}
	probs := make(map[string]float64)
	if total > 0 {
		for k, v := range beads {
			probs[strconv.Itoa(k)] = float64(v) / float64(total)
		}
	}

	c.JSON(http.StatusOK, MatchboxResponse{
		BoardState:    normalized,
		Beads:         beadsStr,
		TimesUsed:     data["times_used"].(int),
		Probabilities: probs,
	})
}

// ListMatchboxes returns all matchboxes
// GET /api/menace/matchboxes
func (h *Handler) ListMatchboxes(c *gin.Context) {
	matchboxes := make([]map[string]interface{}, 0)

	for state, mb := range h.menace.Matchboxes {
		beadsStr := make(map[string]int)
		var topMove *int
		maxBeads := 0
		for k, v := range mb.Beads {
			beadsStr[strconv.Itoa(k)] = v
			if v > maxBeads {
				maxBeads = v
				pos := k
				topMove = &pos
			}
		}

		matchboxes = append(matchboxes, map[string]interface{}{
			"board_state": state,
			"beads":       beadsStr,
			"times_used":  mb.TimesUsed,
			"total_beads": mb.GetTotalBeads(),
			"top_move":    topMove,
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"count":      len(matchboxes),
		"matchboxes": matchboxes,
	})
}

// GetMenaceHistory returns learning history
// GET /api/menace/history
func (h *Handler) GetMenaceHistory(c *gin.Context) {
	history := h.menace.GetHistory()

	snapshots := make([]HistorySnapshotResponse, len(history))
	for i, snap := range history {
		snapshots[i] = HistorySnapshotResponse{
			Games:         snap.Games,
			TotalBeads:    snap.TotalBeads,
			MatchboxCount: snap.MatchboxCount,
			Wins:          snap.Wins,
			Losses:        snap.Losses,
			Draws:         snap.Draws,
			WinRate:       snap.WinRate,
		}
	}

	c.JSON(http.StatusOK, HistoryResponse{
		History:      snapshots,
		CurrentGames: h.menace.GamesPlayed,
		CurrentBeads: h.menace.GetTotalBeads(),
	})
}

// ============================================================================
// Training Endpoints
// ============================================================================

// SelfPlayTraining runs training games
// POST /api/training/self-play
func (h *Handler) SelfPlayTraining(c *gin.Context) {
	var req TrainingRequest
	req.NumGames = 100 // Default
	req.Opponent = "random"

	if err := c.ShouldBindJSON(&req); err != nil && c.Request.ContentLength > 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	startTime := time.Now()
	initialMatchboxes := h.menace.GetMatchboxCount()

	wins := 0
	losses := 0
	draws := 0

	for i := 0; i < req.NumGames; i++ {
		// Alternate who goes first
		menaceFirst := rand.Intn(2) == 0
		g := h.gameManager.CreateGame(menaceFirst)

		// Play the game
		for !g.IsOver() {
			if g.IsMenaceTurn() {
				g.MenaceMove()
			} else {
				// Bot's turn - random move
				validMoves := g.GetValidMoves()
				if len(validMoves) > 0 {
					move := validMoves[rand.Intn(len(validMoves))]
					g.OpponentMove(move)
				}
			}
		}

		// Apply learning
		h.gameManager.FinishGame(g.ID)

		// Track results
		result := g.GetResult()
		switch result {
		case board.ResultWin:
			wins++
		case board.ResultLoss:
			losses++
		case board.ResultDraw:
			draws++
		}
	}

	elapsed := time.Since(startTime).Seconds()
	newMatchboxes := h.menace.GetMatchboxCount() - initialMatchboxes
	totalMatchboxes := h.menace.GetMatchboxCount()
	gamesPerSecond := float64(req.NumGames) / elapsed
	
	// Estimate database size: ~200 bytes per matchbox
	estimatedDBSizeKB := float64(totalMatchboxes*200) / 1024

	c.JSON(http.StatusOK, TrainingResponse{
		GamesPlayed:      req.NumGames,
		Wins:             wins,
		Losses:           losses,
		Draws:            draws,
		TimeSeconds:      elapsed,
		NewMatchboxes:    newMatchboxes,
		GamesPerSecond:   gamesPerSecond,
		TotalMatchboxes:  totalMatchboxes,
		EstimatedDBSizeKB: estimatedDBSizeKB,
	})
}

// formatTime formats seconds into a human-readable string
func formatTime(seconds float64) string {
	if seconds < 60 {
		return fmt.Sprintf("%.1fs", seconds)
	} else if seconds < 3600 {
		mins := int(seconds / 60)
		secs := int(int(seconds) % 60)
		return fmt.Sprintf("%dm %ds", mins, secs)
	} else {
		hours := int(seconds / 3600)
		mins := int(int(seconds) % 3600 / 60)
		return fmt.Sprintf("%dh %dm", hours, mins)
	}
}

// formatSize formats KB into a human-readable string
func formatSize(kb float64) string {
	if kb < 1024 {
		return fmt.Sprintf("%.1f KB", kb)
	}
	return fmt.Sprintf("%.2f MB", kb/1024)
}

// EstimateTraining estimates training time and storage
// POST /api/training/estimate
func (h *Handler) EstimateTraining(c *gin.Context) {
	var req TrainingEstimateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get current state
	currentMatchboxes := h.menace.GetMatchboxCount()
	currentGames := h.menace.GamesPlayed

	// Base estimate: ~1400 games per second (conservative)
	gamesPerSecond := 1400.0
	estimatedTime := float64(req.NumGames) / gamesPerSecond

	// Storage estimation:
	// - Max ~765 unique matchboxes possible
	// - Each matchbox: ~200 bytes
	// - Game history: ~50 bytes per game
	maxMatchboxes := 765
	bytesPerMatchbox := 200
	bytesPerGameHistory := 50

	projectedMatchboxes := currentMatchboxes + req.NumGames/10
	if projectedMatchboxes > maxMatchboxes {
		projectedMatchboxes = maxMatchboxes
	}

	matchboxStorage := projectedMatchboxes * bytesPerMatchbox
	historyStorage := (currentGames + req.NumGames) * bytesPerGameHistory
	totalStorageKB := float64(matchboxStorage+historyStorage) / 1024

	c.JSON(http.StatusOK, TrainingEstimateResponse{
		NumGames:              req.NumGames,
		EstimatedTimeSeconds:  estimatedTime,
		EstimatedTimeFormatted: formatTime(estimatedTime),
		EstimatedDBSizeKB:     totalStorageKB,
		EstimatedDBSizeFormatted: formatSize(totalStorageKB),
		CurrentGamesPlayed:    currentGames,
		CurrentMatchboxes:     currentMatchboxes,
		GamesPerSecondEstimate: gamesPerSecond,
	})
}

// ResetMenace resets MENACE to initial state
// POST /api/menace/reset
func (h *Handler) ResetMenace(c *gin.Context) {
	h.menace.Reset()
	h.gameManager.SetMenace(h.menace)

	c.JSON(http.StatusOK, gin.H{
		"message":        "MENACE has been reset to initial state",
		"games_played":   0,
		"matchbox_count": 0,
	})
}

// ============================================================================
// Health Check
// ============================================================================

// HealthCheck returns API health status
// GET /api/health
func (h *Handler) HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":       "healthy",
		"menace_games": h.menace.GamesPlayed,
		"active_games": len(h.gameManager.GetActiveGames()),
	})
}
