/**
 * TrainingPanel Component
 * 
 * Allows users to train MENACE through self-play.
 * MENACE plays games against a bot to learn faster.
 * 
 * TRAINING OPTIONS:
 * - Number of games to play
 * - Opponent type (random or optimal)
 * 
 * The training runs on the server and returns results.
 */

import { useState } from 'react'
import './TrainingPanel.css'

function TrainingPanel({ onTrainingComplete }) {
  // Training settings
  const [numGames, setNumGames] = useState(100)
  const [opponent, setOpponent] = useState('random')
  
  // Training state
  const [isTraining, setIsTraining] = useState(false)
  const [lastResult, setLastResult] = useState(null)
  const [error, setError] = useState(null)
  
  /**
   * Start self-play training
   */
  const startTraining = async () => {
    setIsTraining(true)
    setError(null)
    
    try {
      const response = await fetch('/api/training/self-play', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          num_games: numGames,
          opponent: opponent,
        }),
      })
      
      if (!response.ok) {
        throw new Error('Training failed')
      }
      
      const data = await response.json()
      setLastResult(data)
      
      // Notify parent to refresh stats
      if (onTrainingComplete) {
        onTrainingComplete()
      }
      
    } catch (err) {
      console.error('Training error:', err)
      setError('Training failed. Is the backend running?')
    } finally {
      setIsTraining(false)
    }
  }
  
  /**
   * Reset MENACE to untrained state
   */
  const resetMenace = async () => {
    if (!confirm('Are you sure? This will erase all of MENACE\'s learning!')) {
      return
    }
    
    try {
      const response = await fetch('/api/menace/reset', {
        method: 'POST',
      })
      
      if (!response.ok) {
        throw new Error('Reset failed')
      }
      
      setLastResult(null)
      
      if (onTrainingComplete) {
        onTrainingComplete()
      }
      
      alert('MENACE has been reset to its initial state.')
      
    } catch (err) {
      console.error('Reset error:', err)
      setError('Failed to reset MENACE.')
    }
  }
  
  return (
    <div className="training-panel-container">
      <div className="card training-card">
        <h2>🏋️ Train MENACE</h2>
        <p className="text-muted">
          Run self-play training to help MENACE learn faster.
        </p>
        
        {/* Training Options */}
        <div className="training-options">
          <div className="option-group">
            <label htmlFor="num-games">Number of Games</label>
            <select 
              id="num-games"
              value={numGames}
              onChange={(e) => setNumGames(Number(e.target.value))}
              disabled={isTraining}
            >
              <option value={10}>10 games</option>
              <option value={50}>50 games</option>
              <option value={100}>100 games</option>
              <option value={500}>500 games</option>
              <option value={1000}>1,000 games</option>
              <option value={5000}>5,000 games</option>
            </select>
          </div>
          
          <div className="option-group">
            <label htmlFor="opponent">Opponent Type</label>
            <select 
              id="opponent"
              value={opponent}
              onChange={(e) => setOpponent(e.target.value)}
              disabled={isTraining}
            >
              <option value="random">Random Bot</option>
              <option value="optimal">Optimal Bot (Minimax)</option>
            </select>
          </div>
        </div>
        
        {/* Training Button */}
        <button
          className="btn-primary train-button"
          onClick={startTraining}
          disabled={isTraining}
        >
          {isTraining ? (
            <>
              <span className="spinner"></span>
              Training...
            </>
          ) : (
            'Start Training'
          )}
        </button>
        
        {/* Error Message */}
        {error && (
          <p className="error-message">{error}</p>
        )}
        
        {/* Training Results */}
        {lastResult && !isTraining && (
          <div className="training-results">
            <h3>Training Complete!</h3>
            <div className="results-grid">
              <div className="result-item">
                <span className="result-value">{lastResult.games_played}</span>
                <span className="result-label">Games</span>
              </div>
              <div className="result-item wins">
                <span className="result-value">{lastResult.wins}</span>
                <span className="result-label">Wins</span>
              </div>
              <div className="result-item losses">
                <span className="result-value">{lastResult.losses}</span>
                <span className="result-label">Losses</span>
              </div>
              <div className="result-item draws">
                <span className="result-value">{lastResult.draws}</span>
                <span className="result-label">Draws</span>
              </div>
              <div className="result-item">
                <span className="result-value">{lastResult.time_seconds}s</span>
                <span className="result-label">Time</span>
              </div>
              <div className="result-item">
                <span className="result-value">+{lastResult.new_matchboxes}</span>
                <span className="result-label">New Matchboxes</span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Training Info */}
      <div className="card training-info">
        <h3>About Training</h3>
        <p>
          <strong>Random Bot:</strong> Makes random valid moves. Good for initial training
          as MENACE gets to see many different game situations.
        </p>
        <p>
          <strong>Optimal Bot:</strong> Plays perfectly using the minimax algorithm.
          MENACE will mostly lose at first but eventually learn to draw consistently.
        </p>
        <p className="text-muted" style={{ marginTop: 'var(--spacing-md)' }}>
          Tip: Start with random training, then switch to optimal training
          for MENACE to learn advanced strategies.
        </p>
      </div>
      
      {/* Reset Section */}
      <div className="card reset-section">
        <h3>⚠️ Reset MENACE</h3>
        <p className="text-muted">
          This will erase all of MENACE's learning and start fresh.
        </p>
        <button 
          className="btn-danger"
          onClick={resetMenace}
          disabled={isTraining}
        >
          Reset MENACE
        </button>
      </div>
    </div>
  )
}

export default TrainingPanel
