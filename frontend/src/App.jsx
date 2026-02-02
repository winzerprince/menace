/**
 * App Component - Main Application
 * 
 * This is the root component that orchestrates the entire application.
 * It manages the overall layout and navigation between different views.
 * 
 * COMPONENT ARCHITECTURE:
 * 
 * App
 * ├── Header (navigation)
 * ├── Main Content
 * │   ├── GameBoard (play against MENACE)
 * │   ├── TrainingPanel (self-play training)
 * │   └── Statistics (learning progress)
 * └── Footer
 * 
 * STATE MANAGEMENT:
 * 
 * For this simple app, we use React's built-in useState hook.
 * In a larger app, you might use Redux, Zustand, or Context API.
 */

import { useState } from 'react'
import './App.css'

// Import components (we'll create these next)
import Header from './components/Header'
import GameBoard from './components/GameBoard'
import TrainingPanel from './components/TrainingPanel'
import Statistics from './components/Statistics'

/**
 * App Component
 * 
 * The main component that renders the entire application.
 */
function App() {
  // Current active tab: 'play', 'train', or 'stats'
  const [activeTab, setActiveTab] = useState('play')
  
  // MENACE statistics - we'll fetch these from the API
  const [stats, setStats] = useState({
    gamesPlayed: 0,
    wins: 0,
    losses: 0,
    draws: 0,
    winRate: 0,
    matchboxCount: 0,
    totalBeads: 0,
  })

  /**
   * Refresh statistics from the API
   * Called after games or training sessions
   */
  const refreshStats = async () => {
    try {
      const response = await fetch('/api/menace/stats')
      if (response.ok) {
        const data = await response.json()
        setStats({
          gamesPlayed: data.games_played,
          wins: data.wins,
          losses: data.losses,
          draws: data.draws,
          winRate: data.win_rate,
          matchboxCount: data.matchbox_count,
          totalBeads: data.total_beads,
        })
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  /**
   * Render the content based on active tab
   */
  const renderContent = () => {
    switch (activeTab) {
      case 'play':
        return <GameBoard onGameEnd={refreshStats} />
      case 'train':
        return <TrainingPanel onTrainingComplete={refreshStats} />
      case 'stats':
        return <Statistics stats={stats} onRefresh={refreshStats} />
      default:
        return <GameBoard onGameEnd={refreshStats} />
    }
  }

  return (
    <div className="app">
      <Header 
        activeTab={activeTab} 
        onTabChange={setActiveTab}
        stats={stats}
      />
      
      <main className="main-content">
        {renderContent()}
      </main>
      
      <footer className="footer">
        <p className="text-muted">
          MENACE - Machine Educable Noughts And Crosses Engine
        </p>
        <p className="text-muted" style={{ fontSize: '0.875rem' }}>
          A recreation of Donald Michie's 1961 machine learning experiment
        </p>
      </footer>
    </div>
  )
}

export default App
