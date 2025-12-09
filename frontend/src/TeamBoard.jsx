import { useState, useEffect } from 'react'
import './TeamBoard.css'

const API_URL = 'http://localhost:8000'

function TeamBoard() {
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingTeam, setEditingTeam] = useState(null)
  const [editName, setEditName] = useState('')

  useEffect(() => {
    fetchTeams()
  }, [])

  const fetchTeams = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_URL}/api/teams`)
      const data = await response.json()
      setTeams(data)
    } catch (error) {
      console.error('Error fetching teams:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInitializeTeams = async () => {
    try {
      const response = await fetch(`${API_URL}/api/teams/initialize`, {
        method: 'POST',
      })
      if (response.ok) {
        await fetchTeams()
      } else {
        const data = await response.json()
        alert(data.detail || 'Failed to initialize teams')
      }
    } catch (error) {
      console.error('Error initializing teams:', error)
    }
  }

  const handleClearTeams = async () => {
    if (!confirm('Are you sure you want to clear all teams? Players will be unassigned.')) return

    try {
      await fetch(`${API_URL}/api/teams`, {
        method: 'DELETE',
      })
      await fetchTeams()
    } catch (error) {
      console.error('Error clearing teams:', error)
    }
  }

  const handleEditTeam = (team) => {
    setEditingTeam(team.id)
    setEditName(team.name)
  }

  const handleSaveTeamName = async (teamId) => {
    try {
      const response = await fetch(`${API_URL}/api/teams/${teamId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: editName }),
      })
      if (response.ok) {
        setEditingTeam(null)
        await fetchTeams()
      } else {
        const data = await response.json()
        alert(data.detail || 'Failed to update team name')
      }
    } catch (error) {
      console.error('Error updating team:', error)
    }
  }

  const handleCancelEdit = () => {
    setEditingTeam(null)
    setEditName('')
  }

  // Group players by position
  const groupPlayersByPosition = (players) => {
    const groups = {}
    const positionOrder = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF']

    players.forEach((player) => {
      const pos = player.position || 'OTHER'
      if (!groups[pos]) {
        groups[pos] = []
      }
      groups[pos].push(player)
    })

    // Sort by position order
    const sortedGroups = {}
    positionOrder.forEach((pos) => {
      if (groups[pos]) {
        sortedGroups[pos] = groups[pos]
      }
    })
    // Add any remaining positions not in the order
    Object.keys(groups).forEach((pos) => {
      if (!sortedGroups[pos]) {
        sortedGroups[pos] = groups[pos]
      }
    })

    return sortedGroups
  }

  if (loading) {
    return <div className="team-board-loading">Loading teams...</div>
  }

  return (
    <div className="team-board">
      <div className="team-board-header">
        <h2>Team Board</h2>
        <div className="team-board-actions">
          {teams.length === 0 ? (
            <button onClick={handleInitializeTeams} className="initialize-button">
              Initialize 12 Teams
            </button>
          ) : (
            <button onClick={handleClearTeams} className="clear-teams-button">
              Clear All Teams
            </button>
          )}
          <button onClick={fetchTeams} className="refresh-button">
            Refresh
          </button>
        </div>
      </div>

      {teams.length === 0 ? (
        <div className="no-teams">
          <p>No teams configured yet.</p>
          <p>Click "Initialize 12 Teams" to create default teams for your league.</p>
        </div>
      ) : (
        <div className="teams-grid">
          {teams.map((team) => (
            <div key={team.id} className="team-card">
              <div className="team-header">
                {editingTeam === team.id ? (
                  <div className="team-name-edit">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveTeamName(team.id)
                        if (e.key === 'Escape') handleCancelEdit()
                      }}
                      autoFocus
                    />
                    <button onClick={() => handleSaveTeamName(team.id)} className="save-btn">
                      ✓
                    </button>
                    <button onClick={handleCancelEdit} className="cancel-btn">
                      ✕
                    </button>
                  </div>
                ) : (
                  <h3 onClick={() => handleEditTeam(team)} title="Click to edit name">
                    {team.name}
                  </h3>
                )}
                <div className="team-budget">
                  <span className={`budget-remaining ${team.remaining_budget < 20 ? 'low-budget' : ''}`}>
                    ${team.remaining_budget}
                  </span>
                  <span className="budget-total">/ ${team.budget}</span>
                </div>
              </div>

              <div className="team-players">
                {team.players.length === 0 ? (
                  <div className="no-players-message">No players drafted</div>
                ) : (
                  Object.entries(groupPlayersByPosition(team.players)).map(([position, players]) => (
                    <div key={position} className="position-group">
                      <div className="position-label">{position}</div>
                      <div className="position-players">
                        {players.map((player) => (
                          <div key={player.id} className="player-entry">
                            <span className="player-name">{player.name}</span>
                            <span className="player-price">${player.draft_price}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div className="team-footer">
                <span className="player-count">{team.players.length} players</span>
                <span className="total-spent">${team.spent} spent</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default TeamBoard
