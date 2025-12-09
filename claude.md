# Fantasy Football Auction Draft Board - AI Context

## Project Overview

This is a full-stack web application for managing fantasy football auction drafts. It allows users to upload player lists via CSV, track draft status in real-time, and manage auction prices and team assignments.

## Architecture

**Stack:**
- Frontend: React 18 + Vite
- Backend: Python FastAPI
- Database: SQLite with SQLAlchemy ORM
- Deployment: Docker + Docker Compose

**Communication:**
- REST API between frontend and backend
- Frontend runs on port 5173
- Backend runs on port 8000
- CORS enabled for local development

## Project Structure

```
draft-board/
├── backend/
│   ├── main.py              # FastAPI app with all endpoints
│   ├── models.py            # SQLAlchemy Player model
│   ├── database.py          # Database configuration and session management
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Backend container configuration
│   └── .dockerignore        # Docker ignore patterns
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component with all UI logic
│   │   ├── App.css         # All styles for the application
│   │   └── main.jsx        # React entry point
│   ├── package.json        # Node dependencies and scripts
│   ├── Dockerfile          # Frontend container configuration
│   └── .dockerignore       # Docker ignore patterns
├── docker-compose.yml       # Multi-container orchestration
├── sample_players.csv       # Example player data
├── README.md               # User documentation
├── claude.md               # This file - AI context
└── .gitignore              # Git ignore patterns
```

## Key Components

### Backend (FastAPI)

**Database Model (models.py):**
- `Player` model with fields: id, name, position, team, projected_points, drafted, draft_price, drafted_by
- SQLite database stored as `draft_board.db`

**API Endpoints (main.py):**
- `GET /` - Health check
- `GET /api/players` - List all players
- `POST /api/players/upload` - Upload CSV file with player data
- `PATCH /api/players/{player_id}/draft` - Mark player as drafted with price and team
- `DELETE /api/players` - Clear all players from database

**Database (database.py):**
- Async SQLite engine with aiosqlite
- Session management with dependency injection
- Auto-creates tables on startup

### Frontend (React)

**App.jsx:**
- Single-page application with all logic in one component
- State management using React hooks (useState, useEffect)
- Features:
  - CSV file upload
  - Player list display in table format
  - Position filtering
  - Show/hide drafted players toggle
  - Draft action with price/team input via browser prompts
  - Real-time statistics (total, drafted, available)
  - Clear all players functionality

**App.css:**
- Modern gradient background (purple theme)
- Responsive design with mobile breakpoints
- Card-based layout with shadows
- Color-coded status badges (green=available, red=drafted)
- Hover effects and transitions

## Data Flow

1. **Upload Players:**
   - User selects CSV file
   - Frontend sends file to `POST /api/players/upload`
   - Backend parses CSV, creates Player records
   - Database stores players
   - Frontend refreshes player list

2. **Draft Player:**
   - User clicks "Draft" button
   - Browser prompts for price and team name
   - Frontend sends `PATCH /api/players/{id}/draft`
   - Backend updates player record (drafted=true, draft_price, drafted_by)
   - Frontend refreshes player list

3. **Filter/Display:**
   - Frontend filters players client-side by position and drafted status
   - No backend calls needed for filtering

## CSV Format

Expected columns:
- `name` (required): Player full name
- `position` (required): QB, RB, WR, TE, etc.
- `team` (required): NFL team abbreviation
- `projected_points` (optional): Numeric projected fantasy points

Column names are case-insensitive (handles both lowercase and title case).

## Development Guidelines

### Making Changes

**Backend:**
- All API logic is in `main.py`
- Database models in `models.py`
- Async/await used throughout
- FastAPI auto-generates OpenAPI docs at `/docs`

**Frontend:**
- All UI logic in single `App.jsx` file
- Uses functional components and hooks
- Fetch API for HTTP requests
- No state management library (uses React useState)

**Database:**
- SQLite file persists in Docker volume `backend-data`
- Schema auto-creates on first run
- No migrations setup (simple SQLAlchemy create_all)

### Common Tasks

**Add new API endpoint:**
1. Add route function in `backend/main.py`
2. Use `async def` with FastAPI decorators
3. Inject session with `Depends(get_session)`
4. Return JSON-serializable data

**Add new player field:**
1. Add column to `Player` model in `models.py`
2. Update `to_dict()` method
3. Update CSV parsing in upload endpoint
4. Update frontend table display in `App.jsx`
5. Delete existing database to recreate schema

**Modify UI:**
1. Edit `App.jsx` for logic/structure
2. Edit `App.css` for styling
3. Vite provides hot module reload

**Add environment variables:**
1. Add to `docker-compose.yml` under `environment:`
2. Access in Python with `os.getenv()`
3. Access in React with `import.meta.env.VITE_*`

## Running the Application

**Docker (Recommended):**
```bash
docker-compose up --build
```

**Manual:**
```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

## Testing Notes

- No automated tests currently implemented
- Manual testing via UI and `/docs` endpoint
- Sample data provided in `sample_players.csv`

## Known Limitations

- Uses browser `prompt()` for draft inputs (not ideal UX)
- No authentication or multi-user support
- No undo functionality for drafts
- Single draft session only (no draft history)
- No real-time updates between multiple users
- No data validation beyond basic CSV parsing

## Future Enhancement Ideas

- Replace prompts with modal dialogs
- Add player search functionality
- Export draft results to CSV
- Draft history/undo feature
- Team budget tracking
- Real-time updates with WebSockets
- User authentication
- Multiple draft sessions
- Player notes/comments
- Auto-draft functionality
- Integration with fantasy football APIs

## Technology Decisions

**Why FastAPI:** Modern async Python framework, auto-generated API docs, easy to use
**Why React + Vite:** Fast dev experience, widely used, component-based
**Why SQLite:** Simple setup, no external database needed, sufficient for use case
**Why Docker:** Consistent environment, easy deployment, no local setup required
**Why single-file components:** Simple project, easier to understand for small scale

## Error Handling

- Backend returns appropriate HTTP status codes
- Frontend logs errors to console
- CSV upload validates file extension
- Missing CSV columns handled with fallbacks
- Database errors bubble up to FastAPI exception handlers

## Security Considerations

- CORS restricted to localhost origins
- No input sanitization (trust local usage)
- No rate limiting
- No file size limits on uploads
- SQL injection protected by SQLAlchemy ORM
- No authentication needed (single-user local app)
