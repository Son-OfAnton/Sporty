"""
Football service for managing football data operations.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from app.api.client import FootballAPIClient
from app.utils.config import get_api_key
from app.utils.api_utils import parse_response
from app.utils.error_handlers import handle_api_error, APIError
from app.models.football_data import (
    League, Team, Player, Fixture, TeamStanding
)

logger = logging.getLogger(__name__)

class FootballService:
    """Service for football data operations."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the football service.
        
        Args:
            api_key: API key for authentication (if None, will be loaded from config)
        """
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise ValueError("API key is required. Set it using 'sporty config set-api-key'")
            
        self.client = FootballAPIClient(api_key=self.api_key)
        
    def get_leagues(self, country: Optional[str] = None, season: Optional[int] = None) -> List[League]:
        """
        Get leagues information.
        
        Args:
            country: Filter by country name
            season: Filter by season year
            
        Returns:
            List of League objects
        """
        response = self.client.get_leagues(country=country, season=season)
        leagues_data = parse_response(response, error_handler=handle_api_error)
        
        return [League.from_api(item) for item in leagues_data]
        
    def get_teams(self, league_id: int, season: int) -> List[Team]:
        """
        Get teams information for a specific league and season.
        
        Args:
            league_id: League ID
            season: Season year
            
        Returns:
            List of Team objects
        """
        response = self.client.get_teams(league_id=league_id, season=season)
        teams_data = parse_response(response, error_handler=handle_api_error)
        
        return [Team.from_api(item) for item in teams_data]
        
    def get_fixtures(
        self, 
        team_id: Optional[int] = None,
        league_id: Optional[int] = None, 
        season: Optional[int] = None,
        date: Optional[Union[str, datetime]] = None
    ) -> List[Fixture]:
        """
        Get fixtures information.
        
        Args:
            team_id: Filter by team ID
            league_id: Filter by league ID
            season: Filter by season year
            date: Filter by date (datetime or YYYY-MM-DD format)
            
        Returns:
            List of Fixture objects
        """
        # Convert datetime to string if needed
        date_str = None
        if date:
            if isinstance(date, datetime):
                date_str = date.strftime("%Y-%m-%d")
            else:
                date_str = date
                
        response = self.client.get_fixtures(
            team_id=team_id,
            league_id=league_id,
            season=season,
            date=date_str
        )
        fixtures_data = parse_response(response, error_handler=handle_api_error)
        
        return [Fixture.from_api(item) for item in fixtures_data]
        
    def get_players(self, team_id: int, season: int) -> List[Player]:
        """
        Get players information for a specific team and season.
        
        Args:
            team_id: Team ID
            season: Season year
            
        Returns:
            List of Player objects
        """
        response = self.client.get_players(team_id=team_id, season=season)
        players_data = parse_response(response, error_handler=handle_api_error)
        
        return [Player.from_api(item) for item in players_data]
        
    def get_standings(self, league_id: int, season: int) -> List[TeamStanding]:
        """
        Get standings information for a specific league and season.
        
        Args:
            league_id: League ID
            season: Season year
            
        Returns:
            List of TeamStanding objects
        """
        response = self.client.get_standings(league_id=league_id, season=season)
        standings_data = parse_response(response, error_handler=handle_api_error)
        
        # The standings response has a complex structure
        if not standings_data:
            return []
            
        # Navigate through the structure to get to the standings
        try:
            league_data = standings_data[0].get("league", {})
            standings = league_data.get("standings", [])
            
            # For most leagues, this is a list of lists
            if standings and isinstance(standings[0], list):
                # Use the first group
                standings = standings[0]
                
            return [TeamStanding.from_api(item) for item in standings]
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse standings: {e}")
            return []
            
    def get_current_season(self) -> int:
        """
        Get the current season year.
        
        Returns:
            Current season year
        """
        now = datetime.now()
        
        # For European leagues, the season spans two years (e.g., 2023-2024)
        # The season is usually named after the starting year
        if now.month >= 7:  # July or later
            return now.year
        else:
            return now.year - 1