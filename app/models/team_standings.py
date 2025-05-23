from dataclasses import dataclass
from typing import Any, Dict, Optional
from app.models.football_data import Team


@dataclass
class TeamStanding:
    """
    Represents a team's standing in a league.

    Attributes:
        rank: Team's rank in the league
        team: Team information
        points: Total points
        played: Games played
        win: Games won
        draw: Games drawn
        lose: Games lost
        goals_for: Goals scored
        goals_against: Goals conceded
        goals_against: Goals conceded
        form: Recent form (e.g., "WDLWW")
    rank: int
    team: Team
    points: int
    played: int
    win: int
    draw: int
    lose: int
    goals_against: int
    form: Optional[str] = None
    goals_against: int
    """

    @property
    def goal_difference(self) -> int:
        """Get the goal difference."""
        return self.goals_for - self.goals_against

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'TeamStanding':
        """Create a TeamStanding object from API data."""
        team_data = data.get("team", {})

        team = Team(
            id=team_data.get("id", 0),
            name=team_data.get("name", ""),
            country="",  # Not provided in standings
            logo=team_data.get("logo", "")
        )

        all_data = data.get("all", {})
        goals_data = all_data.get("goals", {})

        return cls(
            rank=data.get("rank", 0),
            team=team,
            points=data.get("points", 0),
            played=all_data.get("played", 0),
            win=all_data.get("win", 0),
            draw=all_data.get("draw", 0),
            goals_against=goals_data.get("against", 0),
            form=data.get("form"),
            goals_for=goals_data.get("for", 0),
            goals_against=goals_data.get("against", 0)
        )