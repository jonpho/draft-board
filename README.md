# Fantasy Football Auction Draft Board

A full-stack web application for managing fantasy football auction drafts with player upload and real-time draft tracking.

## Features

- Upload player lists via CSV file
- Track player availability and draft status
- Filter players by position
- Record draft prices and team assignments
- View draft statistics in real-time
- Toggle between showing/hiding drafted players
- Responsive design for mobile and desktop

## Tech Stack

**Frontend:**
- React
- Vite
- CSS3

**Backend:**
- Python 3.x
- FastAPI
- SQLAlchemy (with SQLite)

## Project Structure

```
draft-board/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── database.py          # Database configuration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   └── App.css         # Styles
│   └── package.json        # Node dependencies
├── sample_players.csv       # Example CSV file
└── README.md
```

## Getting Started

### Prerequisites

**Option 1: Docker (Recommended)**
- Docker
- Docker Compose

**Option 2: Manual Setup**
- Python 3.8+
- Node.js 20.x+
- npm

### Option 1: Running with Docker (Recommended)

The easiest way to run the application is with Docker Compose:

1. Make sure Docker and Docker Compose are installed on your system

2. From the project root directory, run:
```bash
docker-compose up --build
```

3. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

4. To stop the application:
```bash
docker-compose down
```

To run in detached mode (background):
```bash
docker-compose up -d
```

The database will persist in a Docker volume, so your data is saved between restarts.

### Option 2: Manual Setup

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. Open the application in your browser at `http://localhost:5173`

2. Upload a CSV file with your player list:
   - Click "Upload Players CSV"
   - Select a CSV file with columns: `name`, `position`, `team`, `projected_points`
   - A sample CSV file (`sample_players.csv`) is provided in the root directory

3. Use the draft board:
   - View all uploaded players in the table
   - Filter by position using the dropdown
   - Click "Draft" on any available player to mark them as drafted
   - Enter the draft price and team name when prompted
   - Toggle "Show Drafted Players" to hide/show already drafted players

4. Track your draft:
   - View real-time statistics (Total, Drafted, Available)
   - Drafted players are shown with reduced opacity
   - Clear all players using "Clear All Players" button when starting a new draft

## CSV Format

Your CSV file should have the following columns:

```csv
name,position,team,projected_points
Patrick Mahomes,QB,KC,342.5
Justin Jefferson,WR,MIN,285.4
Christian McCaffrey,RB,SF,320.1
```

**Required columns:**
- `name`: Player name
- `position`: Player position (QB, RB, WR, TE, etc.)
- `team`: NFL team abbreviation

**Optional columns:**
- `projected_points`: Projected fantasy points

## API Endpoints

- `GET /api/players` - Get all players
- `POST /api/players/upload` - Upload CSV file with players
- `PATCH /api/players/{player_id}/draft` - Mark player as drafted
- `DELETE /api/players` - Clear all players

## Development

To modify the application:

1. Backend changes: Edit files in `backend/` and the server will auto-reload
2. Frontend changes: Edit files in `frontend/src/` and the page will hot-reload

## License

MIT
