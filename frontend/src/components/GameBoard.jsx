/**
 * GameBoard Component
 * 
 * The main game interface where users play tic-tac-toe against MENACE.
 * 
 * GAME FLOW:
 * 1. User starts a new game
 * 2. If MENACE goes first, it makes a move
 * 3. User clicks a square to make their move
 * 4. MENACE responds with its move
 * 5. Repeat until game ends
 * 6. Display result and offer to play again
 * 
 * STATE:
 * - gameId: Current game's unique identifier
 * - board: Current board state (9-character string)
 * - currentTurn: 'X' or 'O'
 * - isGameOver: Whether the game has ended
 * - result: 'win', 'loss', 'draw' (from MENACE's perspective)
 * - winner: 'X' or 'O' if there's a winner
 * - menacePlayer: Which symbol MENACE is playing
 * - isLoading: Whether we're waiting for API response
 */

import { useState, useEffect } from 'react'
import './GameBoard.css'

// Square component - individual cell in the grid
function Square({ value, onClick, isWinning, disabled }) {
  return (
    <button 
      className={`square ${value || ''} ${isWinning ? 'winning' : ''}`}
      onClick={onClick}
      disabled={disabled}
    >
      {value || ''}
    </button>
  )
}

function GameBoard({ onGameEnd }) {
  // Game state
  const [gameId, setGameId] = useState(null)
  const [board, setBoard] = useState('_________')
  const [currentTurn, setCurrentTurn] = useState('X')
  const [isGameOver, setIsGameOver] = useState(false)
  const [result, setResult] = useState(null)
  const [winner, setWinner] = useState(null)
  const [menacePlayer, setMenacePlayer] = useState('X')
  const [isLoading, setIsLoading] = useState(false)
  const [lastMenaceMove, setLastMenaceMove] = useState(null)
  
  // Settings
  const [menaceFirst, setMenaceFirst] = useState(true)
  
  /**
   * Start a new game
   */
  const startNewGame = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/game/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ menace_plays_first: menaceFirst }),
      })
      
      if (!response.ok) throw new Error('Failed to start game')
      
      const data = await response.json()
      
      setGameId(data.game_id)
      setBoard(data.board)
      setCurrentTurn(data.current_turn)
      setMenacePlayer(data.menace_player)
      setIsGameOver(false)
      setResult(null)
      setWinner(null)
      setLastMenaceMove(data.menace_move)
      
    } catch (error) {
      console.error('Error starting game:', error)
      alert('Failed to start game. Is the backend running?')
    } finally {
      setIsLoading(false)
    }
  }
  
  /**
   * Make a move
   */
  const makeMove = async (position) => {
    if (isGameOver || isLoading || !gameId) return
    
    // Check if it's the player's turn (not MENACE's turn)
    if (currentTurn === menacePlayer) return
    
    // Check if position is valid
    if (board[position] !== '_') return
    
    setIsLoading(true)
    try {
      const response = await fetch(`/api/game/${gameId}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position }),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to make move')
      }
      
      const data = await response.json()
      
      setBoard(data.board)
      setCurrentTurn(data.current_turn)
      setIsGameOver(data.is_game_over)
      setResult(data.result)
      setWinner(data.winner)
      setLastMenaceMove(data.menace_move)
      
      // Notify parent if game ended
      if (data.is_game_over && onGameEnd) {
        onGameEnd()
      }
      
    } catch (error) {
      console.error('Error making move:', error)
      alert(error.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  /**
   * Get the display message based on game state
   */
  const getMessage = () => {
    if (!gameId) return 'Click "New Game" to start!'
    if (isLoading) return 'MENACE is thinking...'
    if (isGameOver) {
      if (result === 'win') return '🤖 MENACE wins!'
      if (result === 'loss') return '🎉 You win!'
      return "🤝 It's a draw!"
    }
    if (currentTurn === menacePlayer) return "MENACE's turn..."
    return 'Your turn - click a square!'
  }
  
  /**
   * Get human-readable turn indicator
   */
  const getTurnIndicator = () => {
    const humanPlayer = menacePlayer === 'X' ? 'O' : 'X'
    return (
      <div className="turn-indicator">
        <span className={`player ${menacePlayer}`}>
          🤖 MENACE ({menacePlayer})
        </span>
        <span className="vs">vs</span>
        <span className={`player ${humanPlayer}`}>
          👤 You ({humanPlayer})
        </span>
      </div>
    )
  }
  
  return (
    <div className="game-board-container">
      <div className="card game-card">
        <h2>Play Against MENACE</h2>
        
        {/* Game Settings */}
        {!gameId && (
          <div className="game-settings">
            <label className="setting">
              <input
                type="checkbox"
                checked={menaceFirst}
                onChange={(e) => setMenaceFirst(e.target.checked)}
              />
              <span>MENACE plays first (as X)</span>
            </label>
          </div>
        )}
        
        {/* Turn Indicator */}
        {gameId && getTurnIndicator()}
        
        {/* Game Board */}
        <div className={`board ${isLoading ? 'loading' : ''}`}>
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map(i => (
            <Square
              key={i}
              value={board[i] === '_' ? null : board[i]}
              onClick={() => makeMove(i)}
              isWinning={false}  // TODO: Highlight winning line
              disabled={
                isGameOver || 
                isLoading || 
                board[i] !== '_' ||
                currentTurn === menacePlayer
              }
            />
          ))}
        </div>
        
        {/* Status Message */}
        <p className={`game-message ${isLoading ? 'animate-pulse' : ''}`}>
          {getMessage()}
        </p>
        
        {/* Last MENACE Move */}
        {lastMenaceMove !== null && !isLoading && (
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>
            MENACE played position {lastMenaceMove}
          </p>
        )}
        
        {/* Controls */}
        <div className="game-controls">
          <button 
            className="btn-primary"
            onClick={startNewGame}
            disabled={isLoading}
          >
            {gameId ? 'New Game' : 'Start Game'}
          </button>
          
          {isGameOver && (
            <button 
              className="btn-secondary"
              onClick={startNewGame}
              disabled={isLoading}
            >
              Play Again
            </button>
          )}
        </div>
      </div>
      
      {/* How It Works */}
      <div className="card how-it-works">
        <h3>How MENACE Works</h3>
        <p>
          MENACE learns through <strong>reinforcement learning</strong>. 
          Each game state has a "matchbox" with beads representing possible moves.
        </p>
        <ul>
          <li><strong>Win:</strong> MENACE adds beads to moves it made (reward)</li>
          <li><strong>Draw:</strong> Small reward</li>
          <li><strong>Loss:</strong> MENACE removes beads (punishment)</li>
        </ul>
        <p>
          Over time, good moves accumulate more beads and become more likely!
        </p>
      </div>
    </div>
  )
}

export default GameBoard
