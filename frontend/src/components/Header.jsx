/**
 * Header Component
 * 
 * Displays the application title and navigation tabs.
 * Also shows a quick stats summary.
 * 
 * PROPS:
 * - activeTab: Which tab is currently selected
 * - onTabChange: Callback when a tab is clicked
 * - stats: Current MENACE statistics
 */

import './Header.css'

function Header({ activeTab, onTabChange, stats }) {
  const tabs = [
    { id: 'play', label: '🎮 Play', description: 'Play against MENACE' },
    { id: 'train', label: '🏋️ Train', description: 'Self-play training' },
    { id: 'stats', label: '📊 Stats', description: 'View statistics' },
  ]

  return (
    <header className="header">
      <div className="header-content">
        {/* Logo/Title */}
        <div className="header-brand">
          <h1 className="header-title">MENACE</h1>
          <p className="header-subtitle">Machine Educable Noughts And Crosses Engine</p>
        </div>

        {/* Navigation Tabs */}
        <nav className="header-nav">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
              title={tab.description}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Quick Stats */}
        <div className="header-stats">
          <div className="stat-item">
            <span className="stat-value">{stats.gamesPlayed}</span>
            <span className="stat-label">Games</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{Math.round(stats.winRate * 100)}%</span>
            <span className="stat-label">Win Rate</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{stats.matchboxCount}</span>
            <span className="stat-label">Matchboxes</span>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
