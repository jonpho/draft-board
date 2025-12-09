import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import App from './App'

// Mock fetch globally
global.fetch = vi.fn()

const mockPlayers = [
  {
    id: 1,
    name: 'Patrick Mahomes',
    position: 'QB',
    team: 'KC',
    projected_points: 350.5,
    drafted: false,
    draft_price: null,
    drafted_by: null,
  },
  {
    id: 2,
    name: 'Christian McCaffrey',
    position: 'RB',
    team: 'SF',
    projected_points: 320.0,
    drafted: false,
    draft_price: null,
    drafted_by: null,
  },
  {
    id: 3,
    name: 'Tyreek Hill',
    position: 'WR',
    team: 'MIA',
    projected_points: 280.0,
    drafted: true,
    draft_price: 55,
    drafted_by: 'Team A',
  },
]

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default mock for fetching empty players
    global.fetch.mockResolvedValue({
      json: () => Promise.resolve([]),
    })
  })

  describe('Initial Render', () => {
    it('renders the header', async () => {
      render(<App />)
      expect(screen.getByText('Fantasy Football Auction Draft Board')).toBeInTheDocument()
    })

    it('renders upload button', async () => {
      render(<App />)
      expect(screen.getByText('Upload Players CSV')).toBeInTheDocument()
    })

    it('renders filter controls', async () => {
      render(<App />)
      expect(screen.getByText('Position:')).toBeInTheDocument()
      expect(screen.getByText('Show Drafted Players')).toBeInTheDocument()
    })

    it('renders clear all button', async () => {
      render(<App />)
      expect(screen.getByText('Clear All Players')).toBeInTheDocument()
    })

    it('shows empty state message when no players', async () => {
      render(<App />)
      await waitFor(() => {
        expect(screen.getByText('No players uploaded. Upload a CSV file to get started.')).toBeInTheDocument()
      })
    })

    it('fetches players on mount', async () => {
      render(<App />)
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/players')
      })
    })
  })

  describe('Player Display', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve(mockPlayers),
      })
    })

    it('displays player data in table', async () => {
      render(<App />)
      await waitFor(() => {
        expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
        expect(screen.getByText('Christian McCaffrey')).toBeInTheDocument()
        expect(screen.getByText('Tyreek Hill')).toBeInTheDocument()
      })
    })

    it('shows correct player count in stats', async () => {
      render(<App />)
      await waitFor(() => {
        expect(screen.getByText('3')).toBeInTheDocument() // Total
      })
    })

    it('displays projected points correctly', async () => {
      render(<App />)
      await waitFor(() => {
        expect(screen.getByText('350.5')).toBeInTheDocument()
        expect(screen.getByText('320.0')).toBeInTheDocument()
      })
    })

    it('shows drafted player status and price', async () => {
      render(<App />)
      await waitFor(() => {
        expect(screen.getByText('$55')).toBeInTheDocument()
        expect(screen.getByText('Team A')).toBeInTheDocument()
      })
    })

    it('shows draft button only for undrafted players', async () => {
      render(<App />)
      await waitFor(() => {
        const draftButtons = screen.getAllByText('Draft')
        expect(draftButtons).toHaveLength(2) // Only 2 undrafted players
      })
    })
  })

  describe('Position Filter', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve(mockPlayers),
      })
    })

    it('shows all positions in filter dropdown', async () => {
      render(<App />)
      await waitFor(() => {
        const select = screen.getByRole('combobox')
        expect(within(select).getByText('ALL')).toBeInTheDocument()
        expect(within(select).getByText('QB')).toBeInTheDocument()
        expect(within(select).getByText('RB')).toBeInTheDocument()
        expect(within(select).getByText('WR')).toBeInTheDocument()
      })
    })

    it('filters players by position', async () => {
      const user = userEvent.setup()
      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
      })

      const select = screen.getByRole('combobox')
      await user.selectOptions(select, 'QB')

      expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
      expect(screen.queryByText('Christian McCaffrey')).not.toBeInTheDocument()
      expect(screen.queryByText('Tyreek Hill')).not.toBeInTheDocument()
    })
  })

  describe('Show Drafted Filter', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve(mockPlayers),
      })
    })

    it('shows drafted players by default', async () => {
      render(<App />)
      await waitFor(() => {
        expect(screen.getByText('Tyreek Hill')).toBeInTheDocument()
      })
    })

    it('hides drafted players when checkbox is unchecked', async () => {
      const user = userEvent.setup()
      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Tyreek Hill')).toBeInTheDocument()
      })

      const checkbox = screen.getByRole('checkbox')
      await user.click(checkbox)

      expect(screen.queryByText('Tyreek Hill')).not.toBeInTheDocument()
      expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
    })
  })

  describe('Draft Player', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve(mockPlayers),
      })
    })

    it('prompts for price and team when drafting', async () => {
      const user = userEvent.setup()
      global.prompt
        .mockReturnValueOnce('50')
        .mockReturnValueOnce('Champions')

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
      })

      const draftButtons = screen.getAllByText('Draft')
      await user.click(draftButtons[0])

      expect(global.prompt).toHaveBeenCalledWith('Enter draft price:')
      expect(global.prompt).toHaveBeenCalledWith('Enter team name:')
    })

    it('sends PATCH request when drafting', async () => {
      const user = userEvent.setup()
      global.prompt
        .mockReturnValueOnce('50')
        .mockReturnValueOnce('Champions')

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
      })

      const draftButtons = screen.getAllByText('Draft')
      await user.click(draftButtons[0])

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/players/1/draft',
          expect.objectContaining({
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
          })
        )
      })
    })

    it('does not draft if price is cancelled', async () => {
      const user = userEvent.setup()
      global.prompt.mockReturnValueOnce(null)

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
      })

      const initialFetchCount = global.fetch.mock.calls.length

      const draftButtons = screen.getAllByText('Draft')
      await user.click(draftButtons[0])

      // Should not make any additional fetch calls
      expect(global.fetch.mock.calls.length).toBe(initialFetchCount)
    })
  })

  describe('Clear Players', () => {
    beforeEach(() => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve(mockPlayers),
      })
    })

    it('shows confirmation dialog before clearing', async () => {
      const user = userEvent.setup()
      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
      })

      const clearButton = screen.getByText('Clear All Players')
      await user.click(clearButton)

      expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to clear all players?')
    })

    it('sends DELETE request when confirmed', async () => {
      const user = userEvent.setup()
      global.confirm.mockReturnValue(true)

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
      })

      const clearButton = screen.getByText('Clear All Players')
      await user.click(clearButton)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/players',
          expect.objectContaining({ method: 'DELETE' })
        )
      })
    })

    it('does not clear if cancelled', async () => {
      const user = userEvent.setup()
      global.confirm.mockReturnValue(false)

      render(<App />)

      await waitFor(() => {
        expect(screen.getByText('Patrick Mahomes')).toBeInTheDocument()
      })

      const initialFetchCount = global.fetch.mock.calls.length

      const clearButton = screen.getByText('Clear All Players')
      await user.click(clearButton)

      // Should not make DELETE request
      expect(global.fetch.mock.calls.length).toBe(initialFetchCount)
    })
  })

  describe('File Upload', () => {
    it('has file input accepting CSV', () => {
      render(<App />)
      const fileInput = document.getElementById('file-upload')
      expect(fileInput).toHaveAttribute('accept', '.csv')
    })

    it('shows upload message on success', async () => {
      global.fetch
        .mockResolvedValueOnce({ json: () => Promise.resolve([]) }) // Initial fetch
        .mockResolvedValueOnce({ json: () => Promise.resolve({ message: 'Successfully uploaded 5 players' }) }) // Upload
        .mockResolvedValueOnce({ json: () => Promise.resolve(mockPlayers) }) // Refresh

      render(<App />)

      const file = new File(['name,position,team\nTest,QB,NYG'], 'players.csv', { type: 'text/csv' })
      const fileInput = document.getElementById('file-upload')

      await waitFor(() => {
        fireEvent.change(fileInput, { target: { files: [file] } })
      })

      await waitFor(() => {
        expect(screen.getByText('Successfully uploaded 5 players')).toBeInTheDocument()
      })
    })

    it('sends POST request with file', async () => {
      global.fetch
        .mockResolvedValueOnce({ json: () => Promise.resolve([]) })
        .mockResolvedValueOnce({ json: () => Promise.resolve({ message: 'Success' }) })
        .mockResolvedValueOnce({ json: () => Promise.resolve([]) })

      render(<App />)

      const file = new File(['name,position,team\nTest,QB,NYG'], 'players.csv', { type: 'text/csv' })
      const fileInput = document.getElementById('file-upload')

      await waitFor(() => {
        fireEvent.change(fileInput, { target: { files: [file] } })
      })

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/players/upload',
          expect.objectContaining({ method: 'POST' })
        )
      })
    })
  })

  describe('Stats Display', () => {
    it('shows correct drafted count', async () => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve(mockPlayers),
      })

      render(<App />)

      await waitFor(() => {
        const stats = screen.getByText('Drafted:').parentElement
        expect(stats).toHaveTextContent('1') // 1 drafted player
      })
    })

    it('shows correct available count', async () => {
      global.fetch.mockResolvedValue({
        json: () => Promise.resolve(mockPlayers),
      })

      render(<App />)

      await waitFor(() => {
        const stats = screen.getByText('Available:').parentElement
        expect(stats).toHaveTextContent('2') // 2 available players
      })
    })
  })

  describe('Table Headers', () => {
    it('displays all table column headers', async () => {
      render(<App />)

      expect(screen.getByText('Name')).toBeInTheDocument()
      expect(screen.getByText('Position')).toBeInTheDocument()
      expect(screen.getByText('Team')).toBeInTheDocument()
      expect(screen.getByText('Projected Points')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Draft Price')).toBeInTheDocument()
      expect(screen.getByText('Drafted By')).toBeInTheDocument()
      expect(screen.getByText('Action')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles fetch error gracefully', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      global.fetch.mockRejectedValue(new Error('Network error'))

      render(<App />)

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalled()
      })

      consoleSpy.mockRestore()
    })
  })
})
