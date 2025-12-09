from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    budget = Column(Integer, default=200)

    # Relationship to players - use lazy="selectin" for async compatibility
    players = relationship("Player", back_populates="fantasy_team", lazy="selectin")

    def get_spent(self, players=None):
        """Calculate total spent. Uses provided players list or self.players if loaded."""
        player_list = players if players is not None else self.players
        return sum(p.draft_price or 0 for p in player_list)

    def get_remaining_budget(self, players=None):
        """Calculate remaining budget. Uses provided players list or self.players if loaded."""
        return self.budget - self.get_spent(players)

    def to_dict(self, include_players=False):
        # When players relationship is loaded, use it for calculations
        try:
            players_list = self.players
            spent = sum(p.draft_price or 0 for p in players_list)
        except Exception:
            # If players not loaded, default to 0
            players_list = []
            spent = 0

        result = {
            "id": self.id,
            "name": self.name,
            "budget": self.budget,
            "spent": spent,
            "remaining_budget": self.budget - spent,
        }
        if include_players:
            result["players"] = [p.to_dict() for p in players_list]
        return result


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    position = Column(String)
    team = Column(String)  # NFL team
    projected_points = Column(Float, nullable=True)
    drafted = Column(Boolean, default=False)
    draft_price = Column(Integer, nullable=True)
    drafted_by = Column(String, nullable=True)  # Keep for backwards compatibility
    fantasy_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    # Relationship to fantasy team
    fantasy_team = relationship("Team", back_populates="players")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "team": self.team,
            "projected_points": self.projected_points,
            "drafted": self.drafted,
            "draft_price": self.draft_price,
            "drafted_by": self.drafted_by,
            "fantasy_team_id": self.fantasy_team_id,
        }
