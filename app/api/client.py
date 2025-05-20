"""
Football API Client for interacting with the API-Football REST API.
https://www.api-football.com/
"""

import requests
import logging
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class FootballAPIClient:
    """Client for interacting with the API-Football REST API."""
    
    BASE_URL = "https://v3.football.api-sports.io/"
    
    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialize the Football API client.
        
        Args:
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers required for API requests.
        
        Returns:
            Dict containing the required headers
        """
        return {
            "x-apisports-key": self.api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        
    def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Make a request to the API.
        
        Args:
            endpoint: API endpoint to call
            params: Query parameters for the request
            method: HTTP method (GET, POST, etc.)
            
        Returns:
            Dict containing the API response
            
        Raises:
            requests.RequestException: If the request fails
        """
        url = urljoin(self.BASE_URL, endpoint)
        headers = self._get_headers()
        
        try:
            if method.upper() == "GET":
                response = requests.get(
                    url, 
                    headers=headers, 
                    params=params, 
                    timeout=self.timeout
                )
            elif method.upper() == "POST":
                response = requests.post(
                    url, 
                    headers=headers, 
                    json=params, 
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
            
    # API Methods
    def get_leagues(self, country: Optional[str] = None, season: Optional[int] = None) -> Dict[str, Any]:
        """
        Get leagues information.
        
        Args:
            country: Filter by country name
            season: Filter by season year
            
        Returns:
            Dict containing leagues information
        """
        params = {}
        if country:
            params["country"] = country
        if season:
            params["season"] = season
            
        return self._make_request("leagues", params)
        
    def get_teams(self, league_id: int, season: int) -> Dict[str, Any]:
        """
        Get teams information for a specific league and season.
        
        Args:
            league_id: League ID
            season: Season year
            
        Returns:
            Dict containing teams information
        """
        params = {
            "league": league_id,
            "season": season
        }
        
        return self._make_request("teams", params)
        
    def get_fixtures(
        self, 
        team_id: Optional[int] = None,
        league_id: Optional[int] = None, 
        season: Optional[int] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get fixtures information.
        
        Args:
            team_id: Filter by team ID
            league_id: Filter by league ID
            season: Filter by season year
            date: Filter by date (YYYY-MM-DD format)
            
        Returns:
            Dict containing fixtures information
        """
        params = {}
        if team_id:
            params["team"] = team_id
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if date:
            params["date"] = date
            
        return self._make_request("fixtures", params)
        
    def get_players(
        self, 
        team_id: int, 
        season: int
    ) -> Dict[str, Any]:
        """
        Get players information for a specific team and season.
        
        Args:
            team_id: Team ID
            season: Season year
            
        Returns:
            Dict containing players information
        """
        params = {
            "team": team_id,
            "season": season
        }
        
        return self._make_request("players", params)
        
    def get_standings(
        self, 
        league_id: int, 
        season: int
    ) -> Dict[str, Any]:
        """
        Get standings information for a specific league and season.
        
        Args:
            league_id: League ID
            season: Season year
            
        Returns:
            Dict containing standings information
        """
        params = {
            "league": league_id,
            "season": season
        }
        
        return self._make_request("standings", params)