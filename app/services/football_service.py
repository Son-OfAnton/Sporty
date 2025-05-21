"""
Football service for managing football data operations.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from app.api.client import FootballAPIClient
from app.utils.api_utils import parse_response
from app.utils.error_handlers import handle_api_error, APIError
from app.models.football_data import (
    FixtureEvent, FixtureStatistics, League, MatchStatistics, Team, Player, Fixture, TeamLineup, TeamStanding
)

logger = logging.getLogger(__name__)


class FootballService:
    """Service for football data operations."""

    def __init__(self):
        """
        Initialize the football service.

        Args:
            api_key: API key for authentication (if None, will be loaded from config)
        """

        self.client = FootballAPIClient()

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
        fixtures_data = parse_response(
            response, error_handler=handle_api_error)

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
        response = self.client.get_standings(
            league_id=league_id, season=season)
        standings_data = parse_response(
            response, error_handler=handle_api_error)

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

    def get_live_scores(
        self,
        league_id: Optional[int] = None,
        timezone: Optional[str] = None
    ) -> List[Fixture]:
        """
        Get live scores for matches currently in progress.

        Args:
            league_id: Optional league ID to filter matches
            timezone: Timezone for match times (default: UTC)

        Returns:
            List of Fixture objects for matches currently in progress

        Notes:
            This method retrieves only matches that are currently being played.
            The fixture objects include score information and match status.
        """
        response = self.client.get_live_scores(
            league_id=league_id,
            timezone=timezone
        )

        fixtures_data = parse_response(
            response, error_handler=handle_api_error)

        # Convert to Fixture objects
        fixtures = [Fixture.from_api(item) for item in fixtures_data]

        # Log the number of live matches found
        logger.info(f"Found {len(fixtures)} live matches" +
                    (f" in league {league_id}" if league_id else ""))

        return fixtures

    def get_live_matches_by_league(
        self,
        country: Optional[str] = None,
        season: Optional[int] = None,
        timezone: Optional[str] = None
    ) -> Dict[League, List[Fixture]]:
        """
        Get live scores grouped by league.

        Args:
            country: Optional country name to filter leagues
            season: Optional season year to filter leagues
            timezone: Timezone for match times (default: UTC)

        Returns:
            Dict mapping League objects to lists of Fixture objects

        Notes:
            This method first fetches all leagues, then retrieves
            live matches for each league. This can be useful for
            displaying a dashboard of live scores across multiple leagues.
        """
        # First, get all leagues
        leagues = self.get_leagues(country=country, season=season)

        # Dictionary to store results
        result: Dict[League, List[Fixture]] = {}

        # For each league, get live matches
        for league in leagues:
            try:
                live_matches = self.get_live_scores(
                    league_id=league.id,
                    timezone=timezone
                )

                # Only add leagues that have live matches
                if live_matches:
                    result[league] = live_matches

            except Exception as e:
                logger.error(
                    f"Error getting live matches for league {league.id}: {e}")

        return result

    def get_matches(
        self,
        league_id: Optional[int] = None,
        team_id: Optional[int] = None,
        season: Optional[int] = None,
        date: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        live: bool = False,
        status: Optional[str] = None,
        timezone: Optional[str] = None
    ) -> List[Fixture]:
        """
        Get matches based on various filters.

        Args:
            league_id: Filter by league ID
            team_id: Filter by team ID
            season: Filter by season year (defaults to current season)
            date: Filter by specific date (YYYY-MM-DD format)
            from_date: Filter by start date (YYYY-MM-DD format)
            to_date: Filter by end date (YYYY-MM-DD format)
            live: Whether to get only live matches
            status: Filter by match status
            timezone: Timezone for match times

        Returns:
            List of Fixture objects matching the criteria
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        # If live is True, we use get_live_scores()
        if live:
            return self.get_live_scores(
                league_id=league_id,
                timezone=timezone
            )

        # Otherwise, use the more general get_fixtures()
        response = self.client.get_fixtures(
            team_id=team_id,
            league_id=league_id,
            season=season,
            date=date,
            from_date=from_date,
            to_date=to_date,
            timezone=timezone,
            status=status
        )

        fixtures_data = parse_response(
            response, error_handler=handle_api_error)

        # Convert to Fixture objects
        fixtures = [Fixture.from_api(item) for item in fixtures_data]

        # Log the number of matches found
        logger.info(f"Found {len(fixtures)} matches" +
                    (f" in league {league_id}" if league_id else "") +
                    (f" for season {season}" if season else ""))

        return fixtures

    def get_matches_by_league(
        self,
        country: Optional[str] = None,
        season: Optional[int] = None,
        date: Optional[str] = None,
        live: bool = False,
        timezone: Optional[str] = None
    ) -> Dict[League, List[Fixture]]:
        """
        Get matches grouped by league.

        Args:
            country: Optional country name to filter leagues
            season: Optional season year to filter leagues
            date: Optional date to filter matches
            live: Whether to get only live matches
            timezone: Timezone for match times

        Returns:
            Dict mapping League objects to lists of Fixture objects
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        # If live is True, we delegate to get_live_matches_by_league()
        if live:
            return self.get_live_matches_by_league(
                country=country,
                season=season,
                timezone=timezone
            )

        # First, get all leagues
        leagues = self.get_leagues(country=country, season=season)

        # Dictionary to store results
        result: Dict[League, List[Fixture]] = {}

        # For each league, get matches
        for league in leagues:
            try:
                matches = self.get_matches(
                    league_id=league.id,
                    season=season,
                    date=date,
                    timezone=timezone,
                    live=False
                )

                # Only add leagues that have matches
                if matches:
                    result[league] = matches

            except Exception as e:
                logger.error(
                    f"Error getting matches for league {league.id}: {e}")

        return result

    def get_fixture_events(
        self,
        fixture_id: int
    ) -> List[FixtureEvent]:
        """
        Get event details (goals, cards, substitutions) for a specific fixture.
        
        Args:
            fixture_id: ID of the fixture
            
        Returns:
            List of FixtureEvent objects
        """
        response = self.client.get_fixture_events(fixture_id=fixture_id)
        events_data = parse_response(response, error_handler=handle_api_error)
        
        return [FixtureEvent.from_api(item) for item in events_data]
        
    def get_fixture_statistics(
        self,
        fixture_id: int
    ) -> Dict[int, FixtureStatistics]:
        """
        Get detailed statistics for a specific fixture.
        
        Args:
            fixture_id: ID of the fixture
            
        Returns:
            Dict of FixtureStatistics objects, keyed by team ID
        """
        response = self.client.get_fixture_statistics(fixture_id=fixture_id)
        stats_data = parse_response(response, error_handler=handle_api_error)
        
        result: Dict[int, FixtureStatistics] = {}
        for item in stats_data:
            stats = FixtureStatistics.from_api(item)
            result[stats.team_id] = stats
            
        return result
        
    def get_fixture_lineups(
        self,
        fixture_id: int
    ) -> Dict[int, TeamLineup]:
        """
        Get lineups for a specific fixture.
        
        Args:
            fixture_id: ID of the fixture
            
        Returns:
            Dict of TeamLineup objects, keyed by team ID
        """
        response = self.client.get_fixture_lineups(fixture_id=fixture_id)
        lineups_data = parse_response(response, error_handler=handle_api_error)
        
        result: Dict[int, TeamLineup] = {}
        for item in lineups_data:
            lineup = TeamLineup.from_api(item)
            result[lineup.team_id] = lineup
            
        return result
        
    def get_match_statistics(
        self,
        fixture_id: int
    ) -> MatchStatistics:
        """
        Get comprehensive statistics for a match.
        
        Args:
            fixture_id: ID of the fixture
            
        Returns:
            MatchStatistics object containing events, team statistics, and lineups
        """
        try:
            events = self.get_fixture_events(fixture_id)
        except Exception as e:
            logger.warning(f"Failed to get fixture events: {e}")
            events = []
            
        try:
            team_statistics = self.get_fixture_statistics(fixture_id)
        except Exception as e:
            logger.warning(f"Failed to get fixture statistics: {e}")
            team_statistics = {}
            
        try:
            lineups = self.get_fixture_lineups(fixture_id)
        except Exception as e:
            logger.warning(f"Failed to get fixture lineups: {e}")
            lineups = {}
            
        return MatchStatistics(
            events=events,
            team_statistics=team_statistics,
            lineups=lineups
        )
