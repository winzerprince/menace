/**
 * TrainingPanel Component
 * 
 * Allows users to train MENACE through self-play.
 * MENACE plays games against a bot to learn faster.
 * 
 * TRAINING OPTIONS:
 * - Number of games to play (up to 5 million)
 * - Opponent type (random or optimal)
 * - Time and storage estimates before training
 * 
 * The training runs on the server and returns results.
 */

import { useState, useEffect } from 'react'
import './TrainingPanel.css'

/**
 * Training option presets with human-readable descriptions
 * These cover a wide range from quick tests to extensive training
 */
const TRAINING_OPTIONS = [
  { value: 10, label: '10 games', desc: 'Quick test' },
  { value: 50, label: '50 games', desc: 'Very quick' },
  { value: 100, label: '100 games', desc: 'Quick' },
  { value: 500, label: '500 games', desc: '~0.5 sec' },
  { value: 1000, label: '1,000 games', desc: '~1 sec' },
  { value: 5000, label: '5,000 games', desc: '~3-4 sec' },
  { value: 20000, label: '20,000 games', desc: '~15 sec' },
  { value: 100000, label: '100,000 games', desc: '~1 min' },
  { value: 500000, label: '500,000 games', desc: '~6 min' },
  { value: 1000000, label: '1,000,000 games', desc: '~12 min' },
  { value: 3000000, label: '3,000,000 games', desc: '~35 min' },
  { value: 5000000, label: '5,000,000 games', desc: '~1 hour' },
]

function TrainingPanel({ onTrainingComplete }) {
  // Training settings
  const [numGames, setNumGames] = useState(100)
  const [opponent, setOpponent] = useState('random')
  
  // Training state
  const [isTraining, setIsTraining] = useState(false)
  const [lastResult, setLastResult] = useState(null)
  const [error, setError] = useState(null)
  
  // Estimate state
  const [estimate, setEstimate] = useState(null)
  const [isLoadingEstimate, setIsLoadingEstimate] = useState(false)
  
  /**
   * Fetch training estimate when numGames changes
   */
  useEffect(() => {
    const fetchEstimate = async () => {
      // Only fetch for larger training runs
      if (numGames < 1000) {
        setEstimate(null)
        return
      }
      
      setIsLoadingEstimate(true)
      try {
        const response = await fetch('/api/training/estimate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ num_games: numGames }),
        })
        
        if (response.ok) {
          const data = await response.json()
          setEstimate(data)
        }
      } catch (err) {
        console.error('Failed to fetch estimate:', err)
      } finally {
        setIsLoadingEstimate(false)
      }
    }
    
    // Debounce the fetch
    const timer = setTimeout(fetchEstimate, 300)
    return () => clearTimeout(timer)
  }, [numGames])
  
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
      setEstimate(null)
      
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
              {TRAINING_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>
                  {opt.label} ({opt.desc})
                </option>
              ))}
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
        
        {/* Training Estimate */}
        {estimate && numGames >= 1000 && (
          <div className="training-estimate">
            <h4>📊 Training Estimate</h4>
            <div className="estimate-grid">
              <div className="estimate-item">
                <span className="estimate-label">Est. Time:</span>
                <span className="estimate-value">{estimate.estimated_time_formatted}</span>
              </div>
              <div className="estimate-item">
                <span className="estimate-label">Est. DB Size:</span>
                <span className="estimate-value">{estimate.estimated_db_size_formatted}</span>
              </div>
              <div className="estimate-item">
                <span className="estimate-label">Current Games:</span>
                <span className="estimate-value">{estimate.current_games_played.toLocaleString()}</span>
              </div>
              <div className="estimate-item">
                <span className="estimate-label">Current Matchboxes:</span>
                <span className="estimate-value">{estimate.current_matchboxes}</span>
              </div>
            </div>
          </div>
        )}
        
        {isLoadingEstimate && numGames >= 1000 && (
          <div className="training-estimate loading">
            <span className="spinner small"></span> Loading estimate...
          </div>
        )}
        
        {/* Warning for large training runs */}
        {numGames >= 100000 && (
          <div className="training-warning">
            ⚠️ Large training run! This may take several minutes. 
            The browser will wait for completion.
          </div>
        )}
        
        {/* Training Button */}
        <button
          className="btn-primary train-button"
          onClick={startTraining}
          disabled={isTraining}
        >
          {isTraining ? (
            <>
              <span className="spinner"></span>
              Training {numGames.toLocaleString()} games...
            </>
          ) : (
            `Start Training (${numGames.toLocaleString()} games)`
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
                <span className="result-value">{lastResult.games_played.toLocaleString()}</span>
                <span className="result-label">Games</span>
              </div>
              <div className="result-item wins">
                <span className="result-value">{lastResult.wins.toLocaleString()}</span>
                <span className="result-label">Wins</span>
              </div>
              <div className="result-item losses">
                <span className="result-value">{lastResult.losses.toLocaleString()}</span>
                <span className="result-label">Losses</span>
              </div>
              <div className="result-item draws">
                <span className="result-value">{lastResult.draws.toLocaleString()}</span>
                <span className="result-label">Draws</span>
              </div>
              <div className="result-item">
                <span className="result-value">{lastResult.time_seconds.toFixed(2)}s</span>
                <span className="result-label">Time</span>
              </div>
              <div className="result-item">
                <span className="result-value">+{lastResult.new_matchboxes}</span>
                <span className="result-label">New Matchboxes</span>
              </div>
              {lastResult.games_per_second > 0 && (
                <div className="result-item">
                  <span className="result-value">{Math.round(lastResult.games_per_second).toLocaleString()}</span>
                  <span className="result-label">Games/sec</span>
                </div>
              )}
              {lastResult.total_matchboxes > 0 && (
                <div className="result-item">
                  <span className="result-value">{lastResult.total_matchboxes}</span>
                  <span className="result-label">Total Matchboxes</span>
                </div>
              )}
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
