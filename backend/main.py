from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
import csv
import io

from database import init_db, get_session
from models import Player, Team


class TeamCreate(BaseModel):
    name: str
    budget: int = 200


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    budget: Optional[int] = None

app = FastAPI(title="Fantasy Football Draft Board API")

# CORS middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Fantasy Football Draft Board API"}

@app.get("/api/players")
async def get_players(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Player))
    players = result.scalars().all()
    return [player.to_dict() for player in players]

@app.post("/api/players/upload")
async def upload_players(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    contents = await file.read()
    csv_data = io.StringIO(contents.decode('utf-8'))
    csv_reader = csv.DictReader(csv_data)

    players_added = 0
    for row in csv_reader:
        player = Player(
            name=row.get('name', row.get('Name', '')),
            position=row.get('position', row.get('Position', '')),
            team=row.get('team', row.get('Team', '')),
            projected_points=float(row.get('projected_points', row.get('Projected Points', 0))) if row.get('projected_points') or row.get('Projected Points') else None
        )
        session.add(player)
        players_added += 1

    await session.commit()
    return {"message": f"Successfully uploaded {players_added} players"}

@app.patch("/api/players/{player_id}/draft")
async def draft_player(
    player_id: int,
    draft_price: int,
    drafted_by: str,
    team_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # If team_id provided, verify the team exists
    if team_id is not None:
        team_result = await session.execute(select(Team).where(Team.id == team_id))
        team = team_result.scalar_one_or_none()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        player.fantasy_team_id = team_id

    player.drafted = True
    player.draft_price = draft_price
    player.drafted_by = drafted_by
    await session.commit()

    return player.to_dict()

@app.delete("/api/players")
async def clear_players(session: AsyncSession = Depends(get_session)):
    await session.execute(select(Player))
    result = await session.execute(select(Player))
    players = result.scalars().all()
    for player in players:
        await session.delete(player)
    await session.commit()
    return {"message": "All players cleared"}


# Team endpoints

@app.get("/api/teams")
async def get_teams(session: AsyncSession = Depends(get_session)):
    """Get all teams with their drafted players."""
    result = await session.execute(
        select(Team).options(selectinload(Team.players))
    )
    teams = result.scalars().all()
    return [team.to_dict(include_players=True) for team in teams]


@app.get("/api/teams/{team_id}")
async def get_team(team_id: int, session: AsyncSession = Depends(get_session)):
    """Get a specific team by ID."""
    result = await session.execute(
        select(Team).where(Team.id == team_id).options(selectinload(Team.players))
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return team.to_dict(include_players=True)


@app.post("/api/teams")
async def create_team(team_data: TeamCreate, session: AsyncSession = Depends(get_session)):
    """Create a new team."""
    # Check if team name already exists
    result = await session.execute(select(Team).where(Team.name == team_data.name))
    existing_team = result.scalar_one_or_none()

    if existing_team:
        raise HTTPException(status_code=400, detail="Team name already exists")

    team = Team(name=team_data.name, budget=team_data.budget)
    session.add(team)
    await session.commit()
    await session.refresh(team)

    return team.to_dict()


@app.post("/api/teams/initialize")
async def initialize_teams(session: AsyncSession = Depends(get_session)):
    """Initialize 12 default teams for the league."""
    # Check if teams already exist
    result = await session.execute(select(Team))
    existing_teams = result.scalars().all()

    if existing_teams:
        raise HTTPException(status_code=400, detail="Teams already initialized. Clear teams first.")

    teams_created = []
    for i in range(1, 13):
        team = Team(name=f"Team {i}", budget=200)
        session.add(team)
        teams_created.append(team)

    await session.commit()

    # Refresh all teams to get their IDs
    for team in teams_created:
        await session.refresh(team)

    return {
        "message": "Successfully initialized 12 teams",
        "teams": [team.to_dict() for team in teams_created]
    }


@app.patch("/api/teams/{team_id}")
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a team's name or budget."""
    result = await session.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team_data.name is not None:
        # Check if new name conflicts with existing team
        name_check = await session.execute(
            select(Team).where(Team.name == team_data.name, Team.id != team_id)
        )
        if name_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Team name already exists")
        team.name = team_data.name

    if team_data.budget is not None:
        team.budget = team_data.budget

    await session.commit()
    await session.refresh(team)

    return team.to_dict()


@app.delete("/api/teams/{team_id}")
async def delete_team(team_id: int, session: AsyncSession = Depends(get_session)):
    """Delete a team (only if no players drafted)."""
    result = await session.execute(
        select(Team).where(Team.id == team_id).options(selectinload(Team.players))
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.players:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete team with drafted players. Undraft players first."
        )

    await session.delete(team)
    await session.commit()

    return {"message": f"Team '{team.name}' deleted"}


@app.delete("/api/teams")
async def clear_teams(session: AsyncSession = Depends(get_session)):
    """Clear all teams and unassign players from teams."""
    # First, unassign all players from teams
    result = await session.execute(select(Player).where(Player.fantasy_team_id.isnot(None)))
    players = result.scalars().all()
    for player in players:
        player.fantasy_team_id = None

    # Then delete all teams
    result = await session.execute(select(Team))
    teams = result.scalars().all()
    for team in teams:
        await session.delete(team)

    await session.commit()
    return {"message": "All teams cleared"}
