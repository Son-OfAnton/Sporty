"""
Football data models for the Sporty application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

@dataclass
class League:
    """
    Represents a football league.
    
    Attributes:
        id: League ID
        name: League name
        country: Country name
        logo: URL to the league logo
        season: Current season
    """
    id: int
    name: str
    country: str
    logo: str
    season: Optional[int] = None
    type: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'League':
        """Create a League object from API data."""
        league_data = data.get("league", {})
        return cls(
            id=league_data.get("id"),
            name=league_data.get("name"),
            country=league_data.get("country"),
            logo=league_data.get("logo"),
            season=data.get("season"),
            type=league_data.get("type")
        )

@dataclass
class Team:
    """
    Represents a football team.
    
    Attributes:
        id: Team ID
        name: Team name
        country: Country name
        logo: URL to the team logo
        founded: Year the team was founded
        venue_name: Name of the team's venue
    """
    id: int
    name: str
    country: str
    logo: str
    founded: Optional[int] = None
    venue_name: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Team':
        """Create a Team object from API data."""
        team_data = data.get("team", {})
        venue = data.get("venue", {})
        
        return cls(
            id=team_data.get("id"),
            name=team_data.get("name"),
            country=team_data.get("country"),
            logo=team_data.get("logo"),
            founded=team_data.get("founded"),
            venue_name=venue.get("name") if venue else None
        )

@dataclass
class Player:
    """
    Represents a football player.
    
    Attributes:
        id: Player ID
        name: Player name
        age: Player age
        nationality: Player nationality
        position: Player position
        photo: URL to the player's photo
    """
    id: int
    name: str
    age: Optional[int] = None
    nationality: Optional[str] = None
    position: Optional[str] = None
    photo: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Player':
        """Create a Player object from API data."""
        player_data = data.get("player", {})
        
        return cls(
            id=player_data.get("id"),
            name=player_data.get("name"),
            age=player_data.get("age"),
            nationality=player_data.get("nationality"),
            position=player_data.get("position"),
            photo=player_data.get("photo")
        )

@dataclass
class FixtureStatus:
    """Fixture status information."""
    long: str
    short: str
    elapsed: Optional[int] = None

@dataclass
class FixtureTeam:
    """Team information for a fixture."""
    id: int
    name: str
    logo: str
    goals: Optional[int] = None

@dataclass
class Fixture:
    """
    Represents a football match fixture.
    
    Attributes:
        id: Fixture ID
        date: Date of the fixture
        status: Status of the fixture
        home_team: Home team information
        away_team: Away team information
        league: League information
    """
    id: int
    date: datetime
    status: FixtureStatus
    home_team: FixtureTeam
    away_team: FixtureTeam
    league: League
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Fixture':
        """Create a Fixture object from API data."""
        fixture_data = data.get("fixture", {})
        teams_data = data.get("teams", {})
        goals_data = data.get("goals", {})
        status_data = fixture_data.get("status", {})
        
        # Create FixtureStatus
        status = FixtureStatus(
            long=status_data.get("long"),
            short=status_data.get("short"),
            elapsed=status_data.get("elapsed")
        )
        
        # Create FixtureTeams
        home_team = FixtureTeam(
            id=teams_data.get("home", {}).get("id"),
            name=teams_data.get("home", {}).get("name"),
            logo=teams_data.get("home", {}).get("logo"),
            goals=goals_data.get("home")
        )
        
        away_team = FixtureTeam(
            id=teams_data.get("away", {}).get("id"),
            name=teams_data.get("away", {}).get("name"),
            logo=teams_data.get("away", {}).get("logo"),
            goals=goals_data.get("away")
        )
        
        # Parse date
        date_str = fixture_data.get("date")
        date = datetime.fromisoformat(date_str) if date_str else datetime.now()
        
        # Create League
        league = League(
            id=data.get("league", {}).get("id"),
            name=data.get("league", {}).get("name"),
            country=data.get("league", {}).get("country"),
            logo=data.get("league", {}).get("logo"),
            season=data.get("league", {}).get("season")
        )
        
        return cls(
            id=fixture_data.get("id"),
            date=date,
            status=status,
            home_team=home_team,
            away_team=away_team,
            league=league
        )

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
    """
    rank: int
    team: Team
    points: int
    played: int
    win: int
    draw: int
    lose: int
    goals_for: int
    goals_against: int
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'TeamStanding':
        """Create a TeamStanding object from API data."""
        team_data = data.get("team", {})
        
        team = Team(
            id=team_data.get("id"),
            name=team_data.get("name"),
            country="",  # Not provided in standings
            logo=team_data.get("logo")
        )
        
        all_data = data.get("all", {})
        goals_data = all_data.get("goals", {})
        
        return cls(
            rank=data.get("rank"),
            team=team,
            points=data.get("points"),
            played=all_data.get("played"),
            win=all_data.get("win"),
            draw=all_data.get("draw"),
            lose=all_data.get("lose"),
            goals_for=goals_data.get("for"),
            goals_against=goals_data.get("against")
        )