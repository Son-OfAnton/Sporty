"""
Football API Client for interacting with the API-Football REST API.
https://www.api-football.com/
"""

import os
import requests
import logging
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urljoin

logger = logging.getLogger(__name__)
logger.propagate = True


class FootballAPIClient:
    """Client for interacting with the API-Football REST API."""

    BASE_URL = os.getenv("BASE_URL", "https://v3.football.api-sports.io/")
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        raise ValueError(
            "API key not found. Please set the API_FOOTBALL_API_KEY environment variable.")

    def __init__(self, timeout: int = 30):
        """
        Initialize the Football API client.

        Args:
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_key = self.API_KEY
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
        logger.info(f"URL: {url}")
        logger.info(f"Headers: {headers}")

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
        date: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        timezone: Optional[str] = None,
        status: Optional[str] = None,
        round: Optional[str] = None,
        live: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get fixtures information.

        Args:
            team_id: Filter by team ID
            league_id: Filter by league ID
            season: Filter by season year
            date: Filter by specific date (YYYY-MM-DD format)
            from_date: Filter by start date (YYYY-MM-DD format)
            to_date: Filter by end date (YYYY-MM-DD format)
            timezone: Timezone for match times
            status: Filter by fixture status
            round: Filter by competition round
            live: Filter live matches ("all" for all live matches)

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
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if timezone:
            params["timezone"] = timezone
        if status:
            params["status"] = status
        if round:
            params["round"] = round
        if live:
            params["live"] = live

        return self._make_request("fixtures", params)

    def get_live_scores(
        self,
        league_id: Optional[int] = None,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get live scores for current matches.

        Args:
            league_id: Optional league ID to filter matches
            timezone: Timezone for match times (default: UTC)

        Returns:
            Dict containing live match information
        """
        # This is a specialized version of get_fixtures for live matches
        return self.get_fixtures(
            league_id=league_id,
            timezone=timezone,
            live="all"
        )

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
