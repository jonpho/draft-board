import { useState, useEffect } from 'react'
import './App.css'
import TeamBoard from './TeamBoard'

const API_URL = 'http://localhost:8000'

function App() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState('')
  const [filterPosition, setFilterPosition] = useState('ALL')
  const [showDrafted, setShowDrafted] = useState(true)
  const [activeView, setActiveView] = useState('draft') // 'draft' or 'teams'

  useEffect(() => {
    fetchPlayers()
  }, [])

  const fetchPlayers = async () => {
    try {
      const response = await fetch(`${API_URL}/api/players`)
      const data = await response.json()
      setPlayers(data)
    } catch (error) {
      console.error('Error fetching players:', error)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setLoading(true)
    setUploadMessage('')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_URL}/api/players/upload`, {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      setUploadMessage(data.message)
      await fetchPlayers()
    } catch (error) {
      setUploadMessage('Error uploading file: ' + error.message)
    } finally {
      setLoading(false)
      event.target.value = ''
    }
  }

  const handleDraftPlayer = async (playerId) => {
    const draftPrice = prompt('Enter draft price:')
    const draftedBy = prompt('Enter team name:')

    if (!draftPrice || !draftedBy) return

    try {
      await fetch(`${API_URL}/api/players/${playerId}/draft`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          draft_price: parseInt(draftPrice),
          drafted_by: draftedBy,
        }),
      })
      await fetchPlayers()
    } catch (error) {
      console.error('Error drafting player:', error)
    }
  }

  const handleClearPlayers = async () => {
    if (!confirm('Are you sure you want to clear all players?')) return

    try {
      await fetch(`${API_URL}/api/players`, {
        method: 'DELETE',
      })
      await fetchPlayers()
      setUploadMessage('All players cleared')
    } catch (error) {
      console.error('Error clearing players:', error)
    }
  }

  const filteredPlayers = players.filter((player) => {
    const positionMatch = filterPosition === 'ALL' || player.position === filterPosition
    const draftedMatch = showDrafted || !player.drafted
    return positionMatch && draftedMatch
  })

  const positions = ['ALL', ...new Set(players.map((p) => p.position))]

  return (
    <div className="app">
      <header className="header">
        <h1>Fantasy Football Auction Draft Board</h1>
        <nav className="nav-tabs">
          <button
            className={`nav-tab ${activeView === 'draft' ? 'active' : ''}`}
            onClick={() => setActiveView('draft')}
          >
            Draft Board
          </button>
          <button
            className={`nav-tab ${activeView === 'teams' ? 'active' : ''}`}
            onClick={() => setActiveView('teams')}
          >
            Team Board
          </button>
        </nav>
      </header>

      {activeView === 'teams' ? (
        <TeamBoard />
      ) : (
        <>
          <div className="controls">
            <div className="upload-section">
              <label htmlFor="file-upload" className="upload-button">
                Upload Players CSV
              </label>
              <input
                id="file-upload"
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                disabled={loading}
                style={{ display: 'none' }}
              />
              {loading && <span className="loading">Uploading...</span>}
              {uploadMessage && <span className="message">{uploadMessage}</span>}
            </div>

            <div className="filter-section">
              <label>
                Position:
                <select value={filterPosition} onChange={(e) => setFilterPosition(e.target.value)}>
                  {positions.map((pos) => (
                    <option key={pos} value={pos}>
                      {pos}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <input
                  type="checkbox"
                  checked={showDrafted}
                  onChange={(e) => setShowDrafted(e.target.checked)}
                />
                Show Drafted Players
              </label>

              <button onClick={handleClearPlayers} className="clear-button">
                Clear All Players
              </button>
            </div>
          </div>

          <div className="stats">
            <div className="stat">
              <strong>Total Players:</strong> {players.length}
            </div>
            <div className="stat">
              <strong>Drafted:</strong> {players.filter((p) => p.drafted).length}
            </div>
            <div className="stat">
              <strong>Available:</strong> {players.filter((p) => !p.drafted).length}
            </div>
          </div>

          <div className="players-container">
            <table className="players-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Position</th>
                  <th>Team</th>
                  <th>Projected Points</th>
                  <th>Status</th>
                  <th>Draft Price</th>
                  <th>Drafted By</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredPlayers.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="no-players">
                      {players.length === 0
                        ? 'No players uploaded. Upload a CSV file to get started.'
                        : 'No players match the current filters.'}
                    </td>
                  </tr>
                ) : (
                  filteredPlayers.map((player) => (
                    <tr key={player.id} className={player.drafted ? 'drafted' : 'available'}>
                      <td className="player-name">{player.name}</td>
                      <td>{player.position}</td>
                      <td>{player.team}</td>
                      <td>{player.projected_points?.toFixed(1) || 'N/A'}</td>
                      <td>
                        <span className={`status ${player.drafted ? 'drafted' : 'available'}`}>
                          {player.drafted ? 'Drafted' : 'Available'}
                        </span>
                      </td>
                      <td>{player.draft_price ? `$${player.draft_price}` : '-'}</td>
                      <td>{player.drafted_by || '-'}</td>
                      <td>
                        {!player.drafted && (
                          <button
                            onClick={() => handleDraftPlayer(player.id)}
                            className="draft-button"
                          >
                            Draft
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

export default App
