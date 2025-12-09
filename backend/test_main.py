import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import io

from main import app
from models import Base, Player, Team
from database import get_session


# Test database setup - in-memory SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_async_session_maker = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_session():
    async with test_async_session_maker() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture
async def setup_database():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(setup_database):
    """Async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def session(setup_database):
    """Direct database session for setup/verification."""
    async with test_async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def sample_player(session):
    """Create a sample player for tests."""
    player = Player(
        name="Patrick Mahomes",
        position="QB",
        team="KC",
        projected_points=350.5
    )
    session.add(player)
    await session.commit()
    await session.refresh(player)
    return player


class TestHealthCheck:
    """Tests for the root health check endpoint."""

    @pytest.mark.asyncio
    async def test_root_returns_success(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Fantasy Football Draft Board API"}


class TestGetPlayers:
    """Tests for GET /api/players endpoint."""

    @pytest.mark.asyncio
    async def test_get_players_empty(self, client):
        response = await client.get("/api/players")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_players_with_data(self, client, sample_player):
        response = await client.get("/api/players")
        assert response.status_code == 200
        players = response.json()
        assert len(players) == 1
        assert players[0]["name"] == "Patrick Mahomes"
        assert players[0]["position"] == "QB"
        assert players[0]["team"] == "KC"
        assert players[0]["projected_points"] == 350.5
        assert players[0]["drafted"] is False

    @pytest.mark.asyncio
    async def test_get_players_multiple(self, client, session):
        # Add multiple players
        players_data = [
            Player(name="Josh Allen", position="QB", team="BUF", projected_points=340.0),
            Player(name="Christian McCaffrey", position="RB", team="SF", projected_points=320.0),
            Player(name="Tyreek Hill", position="WR", team="MIA", projected_points=280.0),
        ]
        for player in players_data:
            session.add(player)
        await session.commit()

        response = await client.get("/api/players")
        assert response.status_code == 200
        assert len(response.json()) == 3


class TestUploadPlayers:
    """Tests for POST /api/players/upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_csv_success(self, client):
        csv_content = "name,position,team,projected_points\nJosh Allen,QB,BUF,340.5\nTravis Kelce,TE,KC,220.0"
        files = {"file": ("players.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = await client.post("/api/players/upload", files=files)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully uploaded 2 players"

        # Verify players were added
        get_response = await client.get("/api/players")
        players = get_response.json()
        assert len(players) == 2

    @pytest.mark.asyncio
    async def test_upload_csv_title_case_columns(self, client):
        csv_content = "Name,Position,Team,Projected Points\nJoe Burrow,QB,CIN,330.0"
        files = {"file": ("players.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = await client.post("/api/players/upload", files=files)
        assert response.status_code == 200
        assert "1 players" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_upload_csv_missing_projected_points(self, client):
        csv_content = "name,position,team\nJamar Chase,WR,CIN"
        files = {"file": ("players.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = await client.post("/api/players/upload", files=files)
        assert response.status_code == 200

        # Verify player was added with null projected_points
        get_response = await client.get("/api/players")
        players = get_response.json()
        assert len(players) == 1
        assert players[0]["projected_points"] is None

    @pytest.mark.asyncio
    async def test_upload_non_csv_file_rejected(self, client):
        content = "not a csv file"
        files = {"file": ("players.txt", io.BytesIO(content.encode()), "text/plain")}

        response = await client.post("/api/players/upload", files=files)
        assert response.status_code == 400
        assert "Only CSV files are supported" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_empty_csv(self, client):
        csv_content = "name,position,team,projected_points\n"
        files = {"file": ("players.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = await client.post("/api/players/upload", files=files)
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully uploaded 0 players"


class TestDraftPlayer:
    """Tests for PATCH /api/players/{player_id}/draft endpoint."""

    @pytest.mark.asyncio
    async def test_draft_player_success(self, client, sample_player):
        response = await client.patch(
            f"/api/players/{sample_player.id}/draft",
            params={"draft_price": 50, "drafted_by": "Team A"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["drafted"] is True
        assert data["draft_price"] == 50
        assert data["drafted_by"] == "Team A"

    @pytest.mark.asyncio
    async def test_draft_player_not_found(self, client):
        response = await client.patch(
            "/api/players/9999/draft",
            params={"draft_price": 50, "drafted_by": "Team A"}
        )
        assert response.status_code == 404
        assert "Player not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_draft_player_updates_in_list(self, client, sample_player):
        # Draft the player
        await client.patch(
            f"/api/players/{sample_player.id}/draft",
            params={"draft_price": 75, "drafted_by": "Champions"}
        )

        # Verify in player list
        response = await client.get("/api/players")
        players = response.json()
        assert len(players) == 1
        assert players[0]["drafted"] is True
        assert players[0]["draft_price"] == 75
        assert players[0]["drafted_by"] == "Champions"


class TestClearPlayers:
    """Tests for DELETE /api/players endpoint."""

    @pytest.mark.asyncio
    async def test_clear_players_empty(self, client):
        response = await client.delete("/api/players")
        assert response.status_code == 200
        assert response.json()["message"] == "All players cleared"

    @pytest.mark.asyncio
    async def test_clear_players_with_data(self, client, sample_player):
        # Verify player exists
        get_response = await client.get("/api/players")
        assert len(get_response.json()) == 1

        # Clear players
        response = await client.delete("/api/players")
        assert response.status_code == 200

        # Verify players cleared
        get_response = await client.get("/api/players")
        assert get_response.json() == []

    @pytest.mark.asyncio
    async def test_clear_multiple_players(self, client, session):
        # Add multiple players
        for i in range(5):
            session.add(Player(name=f"Player {i}", position="QB", team="TST"))
        await session.commit()

        # Clear all
        response = await client.delete("/api/players")
        assert response.status_code == 200

        # Verify all cleared
        get_response = await client.get("/api/players")
        assert get_response.json() == []


class TestPlayerModel:
    """Tests for the Player model."""

    @pytest.mark.asyncio
    async def test_player_to_dict(self, sample_player):
        player_dict = sample_player.to_dict()
        assert player_dict["name"] == "Patrick Mahomes"
        assert player_dict["position"] == "QB"
        assert player_dict["team"] == "KC"
        assert player_dict["projected_points"] == 350.5
        assert player_dict["drafted"] is False
        assert player_dict["draft_price"] is None
        assert player_dict["drafted_by"] is None

    @pytest.mark.asyncio
    async def test_player_default_values(self, session):
        player = Player(name="Test Player", position="RB", team="NYG")
        session.add(player)
        await session.commit()
        await session.refresh(player)

        assert player.drafted is False
        assert player.draft_price is None
        assert player.drafted_by is None
        assert player.projected_points is None
        assert player.fantasy_team_id is None


# Team Tests

@pytest_asyncio.fixture
async def sample_team(session):
    """Create a sample team for tests."""
    team = Team(name="Test Team", budget=200)
    session.add(team)
    await session.commit()
    await session.refresh(team)
    return team


class TestGetTeams:
    """Tests for GET /api/teams endpoint."""

    @pytest.mark.asyncio
    async def test_get_teams_empty(self, client):
        response = await client.get("/api/teams")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_teams_with_data(self, client, sample_team):
        response = await client.get("/api/teams")
        assert response.status_code == 200
        teams = response.json()
        assert len(teams) == 1
        assert teams[0]["name"] == "Test Team"
        assert teams[0]["budget"] == 200
        assert teams[0]["spent"] == 0
        assert teams[0]["remaining_budget"] == 200
        assert teams[0]["players"] == []

    @pytest.mark.asyncio
    async def test_get_team_by_id(self, client, sample_team):
        response = await client.get(f"/api/teams/{sample_team.id}")
        assert response.status_code == 200
        team = response.json()
        assert team["name"] == "Test Team"
        assert team["id"] == sample_team.id

    @pytest.mark.asyncio
    async def test_get_team_not_found(self, client):
        response = await client.get("/api/teams/9999")
        assert response.status_code == 404
        assert "Team not found" in response.json()["detail"]


class TestCreateTeam:
    """Tests for POST /api/teams endpoint."""

    @pytest.mark.asyncio
    async def test_create_team_success(self, client):
        response = await client.post(
            "/api/teams",
            json={"name": "New Team", "budget": 250}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Team"
        assert data["budget"] == 250
        assert data["spent"] == 0
        assert data["remaining_budget"] == 250

    @pytest.mark.asyncio
    async def test_create_team_default_budget(self, client):
        response = await client.post(
            "/api/teams",
            json={"name": "Default Budget Team"}
        )
        assert response.status_code == 200
        assert response.json()["budget"] == 200

    @pytest.mark.asyncio
    async def test_create_team_duplicate_name(self, client, sample_team):
        response = await client.post(
            "/api/teams",
            json={"name": "Test Team"}
        )
        assert response.status_code == 400
        assert "Team name already exists" in response.json()["detail"]


class TestInitializeTeams:
    """Tests for POST /api/teams/initialize endpoint."""

    @pytest.mark.asyncio
    async def test_initialize_teams_success(self, client):
        response = await client.post("/api/teams/initialize")
        assert response.status_code == 200
        data = response.json()
        assert "Successfully initialized 12 teams" in data["message"]
        assert len(data["teams"]) == 12

        # Verify team names
        team_names = [t["name"] for t in data["teams"]]
        for i in range(1, 13):
            assert f"Team {i}" in team_names

    @pytest.mark.asyncio
    async def test_initialize_teams_already_exists(self, client, sample_team):
        response = await client.post("/api/teams/initialize")
        assert response.status_code == 400
        assert "Teams already initialized" in response.json()["detail"]


class TestUpdateTeam:
    """Tests for PATCH /api/teams/{team_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_team_name(self, client, sample_team):
        response = await client.patch(
            f"/api/teams/{sample_team.id}",
            json={"name": "Updated Team Name"}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Team Name"

    @pytest.mark.asyncio
    async def test_update_team_budget(self, client, sample_team):
        response = await client.patch(
            f"/api/teams/{sample_team.id}",
            json={"budget": 300}
        )
        assert response.status_code == 200
        assert response.json()["budget"] == 300

    @pytest.mark.asyncio
    async def test_update_team_not_found(self, client):
        response = await client.patch(
            "/api/teams/9999",
            json={"name": "New Name"}
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_team_duplicate_name(self, client, session):
        # Create two teams
        team1 = Team(name="Team One", budget=200)
        team2 = Team(name="Team Two", budget=200)
        session.add(team1)
        session.add(team2)
        await session.commit()
        await session.refresh(team2)

        # Try to rename team2 to team1's name
        response = await client.patch(
            f"/api/teams/{team2.id}",
            json={"name": "Team One"}
        )
        assert response.status_code == 400
        assert "Team name already exists" in response.json()["detail"]


class TestDeleteTeam:
    """Tests for DELETE /api/teams/{team_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_team_success(self, client, sample_team):
        response = await client.delete(f"/api/teams/{sample_team.id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"]

        # Verify team is gone
        get_response = await client.get(f"/api/teams/{sample_team.id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_team_not_found(self, client):
        response = await client.delete("/api/teams/9999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_team_with_players(self, client, session):
        # Create team and player
        team = Team(name="Team With Player", budget=200)
        session.add(team)
        await session.commit()
        await session.refresh(team)

        player = Player(
            name="Test Player",
            position="QB",
            team="TST",
            fantasy_team_id=team.id
        )
        session.add(player)
        await session.commit()

        # Try to delete team with player
        response = await client.delete(f"/api/teams/{team.id}")
        assert response.status_code == 400
        assert "Cannot delete team with drafted players" in response.json()["detail"]


class TestClearTeams:
    """Tests for DELETE /api/teams endpoint."""

    @pytest.mark.asyncio
    async def test_clear_teams_empty(self, client):
        response = await client.delete("/api/teams")
        assert response.status_code == 200
        assert response.json()["message"] == "All teams cleared"

    @pytest.mark.asyncio
    async def test_clear_teams_with_data(self, client, sample_team):
        response = await client.delete("/api/teams")
        assert response.status_code == 200

        # Verify teams cleared
        get_response = await client.get("/api/teams")
        assert get_response.json() == []

    @pytest.mark.asyncio
    async def test_clear_teams_unassigns_players(self, client, session):
        # Create team and assigned player
        team = Team(name="Team To Clear", budget=200)
        session.add(team)
        await session.commit()
        await session.refresh(team)

        player = Player(
            name="Assigned Player",
            position="RB",
            team="TST",
            fantasy_team_id=team.id
        )
        session.add(player)
        await session.commit()

        # Clear teams
        response = await client.delete("/api/teams")
        assert response.status_code == 200

        # Verify player is unassigned but still exists
        players_response = await client.get("/api/players")
        players = players_response.json()
        assert len(players) == 1
        assert players[0]["fantasy_team_id"] is None


class TestTeamModel:
    """Tests for the Team model."""

    @pytest.mark.asyncio
    async def test_team_to_dict(self, sample_team):
        team_dict = sample_team.to_dict()
        assert team_dict["name"] == "Test Team"
        assert team_dict["budget"] == 200
        assert team_dict["spent"] == 0
        assert team_dict["remaining_budget"] == 200

    @pytest.mark.asyncio
    async def test_team_budget_calculation(self, session):
        team = Team(name="Budget Test Team", budget=200)
        session.add(team)
        await session.commit()
        await session.refresh(team)

        # Add players with draft prices
        player1 = Player(
            name="Player 1",
            position="QB",
            team="TST",
            draft_price=50,
            fantasy_team_id=team.id
        )
        player2 = Player(
            name="Player 2",
            position="RB",
            team="TST",
            draft_price=30,
            fantasy_team_id=team.id
        )
        session.add(player1)
        session.add(player2)
        await session.commit()

        # Refresh team to get updated relationships
        await session.refresh(team)

        # Use to_dict which properly loads players
        team_dict = team.to_dict()
        assert team_dict["spent"] == 80
        assert team_dict["remaining_budget"] == 120


class TestDraftPlayerWithTeam:
    """Tests for drafting players with team assignment."""

    @pytest.mark.asyncio
    async def test_draft_player_with_team(self, client, sample_player, sample_team):
        response = await client.patch(
            f"/api/players/{sample_player.id}/draft",
            params={
                "draft_price": 60,
                "drafted_by": "Test Team",
                "team_id": sample_team.id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["drafted"] is True
        assert data["draft_price"] == 60
        assert data["fantasy_team_id"] == sample_team.id

    @pytest.mark.asyncio
    async def test_draft_player_invalid_team(self, client, sample_player):
        response = await client.patch(
            f"/api/players/{sample_player.id}/draft",
            params={
                "draft_price": 60,
                "drafted_by": "Test Team",
                "team_id": 9999
            }
        )
        assert response.status_code == 404
        assert "Team not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_team_shows_drafted_player(self, client, sample_player, sample_team):
        # Draft player to team
        await client.patch(
            f"/api/players/{sample_player.id}/draft",
            params={
                "draft_price": 45,
                "drafted_by": "Test Team",
                "team_id": sample_team.id
            }
        )

        # Verify team shows the player
        response = await client.get(f"/api/teams/{sample_team.id}")
        team_data = response.json()
        assert len(team_data["players"]) == 1
        assert team_data["players"][0]["name"] == "Patrick Mahomes"
        assert team_data["spent"] == 45
        assert team_data["remaining_budget"] == 155
