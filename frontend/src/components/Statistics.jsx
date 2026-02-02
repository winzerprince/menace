/**
 * Statistics Component
 * 
 * Displays MENACE's learning progress with charts and detailed stats.
 * 
 * VISUALIZATION:
 * - Win/Loss/Draw pie chart
 * - Bead growth line chart (tracks learning over time)
 * - Stats overview cards
 * - Matchbox explorer (future)
 * 
 * We use Recharts library for charting - it's React-friendly
 * and has good default styling.
 */

import { useState, useEffect } from 'react'
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Area, ComposedChart
} from 'recharts'
import './Statistics.css'

// Colors for the pie chart
const COLORS = {
  wins: '#22c55e',   // Green
  losses: '#ef4444', // Red
  draws: '#f59e0b',  // Amber
  beads: '#3b82f6',  // Blue
  matchboxes: '#8b5cf6', // Purple
  winRate: '#22c55e', // Green
}

function Statistics({ stats, onRefresh }) {
  const [matchboxes, setMatchboxes] = useState([])
  const [history, setHistory] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  
  // Fetch matchbox data
  const fetchMatchboxes = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/menace/matchboxes')
      if (response.ok) {
        const data = await response.json()
        setMatchboxes(data.matchboxes || [])
      }
    } catch (error) {
      console.error('Failed to fetch matchboxes:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  // Fetch learning history for the bead growth chart
  const fetchHistory = async () => {
    try {
      const response = await fetch('/api/menace/history')
      if (response.ok) {
        const data = await response.json()
        setHistory(data.history || [])
      }
    } catch (error) {
      console.error('Failed to fetch history:', error)
    }
  }
  
  useEffect(() => {
    fetchMatchboxes()
    fetchHistory()
    onRefresh?.()
  }, [])
  
  // Prepare pie chart data
  const pieData = [
    { name: 'Wins', value: stats.wins, color: COLORS.wins },
    { name: 'Losses', value: stats.losses, color: COLORS.losses },
    { name: 'Draws', value: stats.draws, color: COLORS.draws },
  ].filter(item => item.value > 0)
  
  // Calculate percentages
  const total = stats.gamesPlayed || 1
  const winPercent = ((stats.wins / total) * 100).toFixed(1)
  const lossPercent = ((stats.losses / total) * 100).toFixed(1)
  const drawPercent = ((stats.draws / total) * 100).toFixed(1)
  
  return (
    <div className="statistics-container">
      {/* Overview Cards */}
      <div className="stats-overview">
        <div className="stat-card total">
          <div className="stat-icon">🎮</div>
          <div className="stat-content">
            <span className="stat-number">{stats.gamesPlayed}</span>
            <span className="stat-title">Total Games</span>
          </div>
        </div>
        
        <div className="stat-card wins">
          <div className="stat-icon">🏆</div>
          <div className="stat-content">
            <span className="stat-number">{stats.wins}</span>
            <span className="stat-title">Wins ({winPercent}%)</span>
          </div>
        </div>
        
        <div className="stat-card losses">
          <div className="stat-icon">💔</div>
          <div className="stat-content">
            <span className="stat-number">{stats.losses}</span>
            <span className="stat-title">Losses ({lossPercent}%)</span>
          </div>
        </div>
        
        <div className="stat-card draws">
          <div className="stat-icon">🤝</div>
          <div className="stat-content">
            <span className="stat-number">{stats.draws}</span>
            <span className="stat-title">Draws ({drawPercent}%)</span>
          </div>
        </div>
      </div>
      
      {/* Charts Row */}
      <div className="charts-row">
        {/* Win/Loss Pie Chart */}
        <div className="card chart-card">
          <h3>Game Results</h3>
          {stats.gamesPlayed > 0 ? (
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="no-data">No games played yet</p>
          )}
        </div>
        
        {/* Learning Stats */}
        <div className="card chart-card">
          <h3>Learning Progress</h3>
          <div className="learning-stats">
            <div className="learning-stat">
              <span className="learning-label">Matchboxes Learned</span>
              <span className="learning-value">{stats.matchboxCount}</span>
              <span className="learning-description">
                Unique game states MENACE has encountered
              </span>
            </div>
            
            <div className="learning-stat">
              <span className="learning-label">Total Beads</span>
              <span className="learning-value">{stats.totalBeads.toLocaleString()}</span>
              <span className="learning-description">
                Sum of all beads across all matchboxes
              </span>
            </div>
            
            <div className="learning-stat">
              <span className="learning-label">Win Rate</span>
              <span className="learning-value" style={{ color: COLORS.wins }}>
                {(stats.winRate * 100).toFixed(1)}%
              </span>
              <span className="learning-description">
                {stats.winRate >= 0.5 ? 'Above average!' : 'Keep training!'}
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Bead Growth Chart - Shows learning over time */}
      <div className="card bead-chart-section">
        <div className="chart-header">
          <h3>📈 Learning Over Time</h3>
          <p className="chart-description">
            Watch how MENACE's "confidence" (total beads) grows as it learns.
            Rising beads = winning moves being reinforced!
          </p>
        </div>
        
        {history.length > 1 ? (
          <div className="bead-chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={history} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis 
                  dataKey="games" 
                  label={{ value: 'Games Played', position: 'bottom', offset: 0 }}
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  yAxisId="beads"
                  label={{ value: 'Total Beads', angle: -90, position: 'insideLeft' }}
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  yAxisId="matchboxes"
                  orientation="right"
                  label={{ value: 'Matchboxes', angle: 90, position: 'insideRight' }}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--color-bg-card)', 
                    border: '1px solid var(--color-border)',
                    borderRadius: '8px'
                  }}
                  formatter={(value, name) => {
                    if (name === 'total_beads') return [value.toLocaleString(), 'Total Beads']
                    if (name === 'matchbox_count') return [value, 'Matchboxes']
                    if (name === 'win_rate') return [(value * 100).toFixed(1) + '%', 'Win Rate']
                    return [value, name]
                  }}
                />
                <Legend />
                <Area 
                  yAxisId="beads"
                  type="monotone" 
                  dataKey="total_beads" 
                  stroke={COLORS.beads}
                  fill={COLORS.beads}
                  fillOpacity={0.2}
                  name="Total Beads"
                  strokeWidth={2}
                />
                <Line 
                  yAxisId="matchboxes"
                  type="monotone" 
                  dataKey="matchbox_count" 
                  stroke={COLORS.matchboxes}
                  name="Matchboxes"
                  strokeWidth={2}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
            
            {/* Win Rate Chart */}
            <h4 style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>Win Rate Progression</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={history} margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis 
                  dataKey="games" 
                  label={{ value: 'Games Played', position: 'bottom', offset: 0 }}
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  domain={[0, 1]}
                  tickFormatter={(v) => (v * 100) + '%'}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip 
                  formatter={(value) => [(value * 100).toFixed(1) + '%', 'Win Rate']}
                  contentStyle={{ 
                    backgroundColor: 'var(--color-bg-card)', 
                    border: '1px solid var(--color-border)',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="win_rate" 
                  stroke={COLORS.winRate}
                  name="Win Rate"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <p className="no-data">
            Play some games to see learning progress! 
            {history.length === 1 && " (Need at least 2 data points)"}
          </p>
        )}
      </div>
      
      {/* Matchbox Explorer */}
      <div className="card matchbox-section">
        <div className="matchbox-header">
          <h3>Matchbox Explorer</h3>
          <button 
            className="btn-secondary"
            onClick={() => {
              fetchMatchboxes()
              fetchHistory()
            }}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
        
        {matchboxes.length > 0 ? (
          <div className="matchbox-list">
            {matchboxes.slice(0, 10).map((mb, index) => (
              <div key={index} className="matchbox-item">
                <div className="matchbox-board">
                  {mb.board_state.split('').map((cell, i) => (
                    <span 
                      key={i} 
                      className={`cell ${cell}`}
                    >
                      {cell === '_' ? '·' : cell}
                    </span>
                  ))}
                </div>
                <div className="matchbox-info">
                  <span className="matchbox-uses">
                    Used {mb.times_used} times
                  </span>
                  <span className="matchbox-beads">
                    {mb.total_beads} beads
                  </span>
                  {mb.top_move !== null && (
                    <span className="matchbox-top-move">
                      Favorite: position {mb.top_move}
                    </span>
                  )}
                </div>
              </div>
            ))}
            {matchboxes.length > 10 && (
              <p className="text-muted">
                ... and {matchboxes.length - 10} more matchboxes
              </p>
            )}
          </div>
        ) : (
          <p className="no-data">
            No matchboxes yet. Play some games or run training!
          </p>
        )}
      </div>
      
      {/* Refresh Button */}
      <div className="refresh-section">
        <button 
          className="btn-secondary"
          onClick={() => {
            onRefresh?.()
            fetchMatchboxes()
            fetchHistory()
          }}
          disabled={isLoading}
        >
          Refresh All Statistics
        </button>
      </div>
    </div>
  )
}

export default Statistics
