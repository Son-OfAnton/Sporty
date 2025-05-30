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
    FixtureEvent, FixtureStatistics, League, MatchStatistics, Team, Player, Fixture, TeamLineup, TeamStanding, TeamStatistics
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

    def get_teams(self, league_id: int, season: Optional[int] = None) -> List[Team]:
        """
        Get teams information for a specific league and season.

        Args:
            league_id: League ID
            season: Season year (defaults to current season)

        Returns:
            List of Team objects
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        response = self.client.get_teams(league=league_id, season=season)
        teams_data = parse_response(response, error_handler=handle_api_error)

        return [Team.from_api(item) for item in teams_data]

    def get_team(self, team_id: int) -> Optional[Team]:
        """
        Get information for a specific team by ID.

        Args:
            team_id: Team ID

        Returns:
            Team object or None if team not found
        """
        response = self.client.get_team(team_id=team_id)
        team_data = parse_response(response, error_handler=handle_api_error)

        if not team_data:
            return None

        return Team.from_api(team_data[0])

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

    def get_players(self, team_id: int, season: Optional[int] = None) -> List[Player]:
        """
        Get players information for a specific team and season.

        Args:
            team_id: Team ID
            season: Season year (defaults to current season)

        Returns:
            List of Player objects
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        response = self.client.get_players(team_id=team_id, season=season)
        players_data = parse_response(response, error_handler=handle_api_error)

        # Debug log to see the structure
        logger.debug(
            f"Players data structure: {players_data[:1] if players_data else []}")

        player_list = []
        for item in players_data:
            # Extract player info from the response
            player_info = item.get("player", {})

            if not player_info:
                # Fallback to direct data if not nested
                logger.warning(f"Unexpected player data format: {item}")
                player_list.append(Player.from_api(item))
                continue

            # The statistics field may contain position information
            statistics = item.get("statistics", [])
            position = player_info.get("position")

            # If position is not in player_info, try to get it from statistics
            if not position and statistics:
                first_stat = statistics[0] if statistics else {}
                games = first_stat.get("games", {})
                position = games.get("position")

            # Create a modified player info with the position
            modified_player_info = player_info.copy()
            if position:
                modified_player_info["position"] = position

            # Add the player to our list
            player_list.append(Player.from_api(
                {"player": modified_player_info}))

        return player_list

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

    def get_team_matches_by_date_range(
        self,
        team_id: int,
        from_date: str,
        to_date: str,
        timezone: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Fixture]:
        """
        Get team matches for a specific date range.

        Args:
            team_id: Team ID
            from_date: Start date (YYYY-MM-DD format)
            to_date: End date (YYYY-MM-DD format)
            timezone: Timezone for match times
            status: Filter by match status (defaults to all)

        Returns:
            List of Fixture objects for the team in the date range
        """
        response = self.client.get_fixtures(
            team_id=team_id,
            from_date=from_date,
            to_date=to_date,
            timezone=timezone,
            status=status
        )

        fixtures_data = parse_response(
            response, error_handler=handle_api_error)
        fixtures = [Fixture.from_api(item) for item in fixtures_data]

        logger.info(
            f"Found {len(fixtures)} matches for team {team_id} from {from_date} to {to_date}")
        return fixtures

    def get_team_season_matches(
        self,
        team_id: int,
        season: Optional[int] = None,
        timezone: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Fixture]:
        """
        Get all team matches for a specific season.

        Args:
            team_id: Team ID
            season: Season year (defaults to current season)
            timezone: Timezone for match times
            status: Filter by match status (defaults to all)

        Returns:
            List of Fixture objects for the team in the season
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        response = self.client.get_fixtures(
            team_id=team_id,
            season=season,
            timezone=timezone,
            status=status
        )

        fixtures_data = parse_response(
            response, error_handler=handle_api_error)
        fixtures = [Fixture.from_api(item) for item in fixtures_data]

        logger.info(
            f"Found {len(fixtures)} matches for team {team_id} in season {season}")
        return fixtures

    def get_team_statistics(
        self,
        team_id: int,
        season: Optional[int] = None,
        league_id: Optional[int] = None
    ) -> Optional[TeamStatistics]:
        """
        Get comprehensive statistics for a team in a specific season.

        Args:
            team_id: Team ID
            season: Season year (defaults to current season)
            league_id: League ID (if None, get overall statistics across all competitions)

        Returns:
            TeamStatistics object with comprehensive team statistics or None if not found
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        # Prepare parameters
        params = {
            "team": team_id,
            "season": season
        }

        if league_id:
            params["league"] = league_id

        # Make API request
        response = self.client.get_team_statistics(**params)

        # Parse response
        stats_data = parse_response(response, error_handler=handle_api_error)

        # If no data returned, return None
        if not stats_data:
            return None

        # API returns statistics as a single object, not a list
        if isinstance(stats_data, dict):
            return TeamStatistics.from_api(stats_data)

        # If it's a list (should not happen), take the first item
        if stats_data and isinstance(stats_data, list):
            return TeamStatistics.from_api(stats_data[0])

        return None

    def get_top_scorers(self, league_id: int, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get top goal scorers for a specific league and season.

        Args:
            league_id: League ID
            season: Season year (defaults to current season)

        Returns:
            List of player statistics with goal scoring information
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        response = self.client.get_top_scorers(
            league_id=league_id, season=season)
        top_scorers_data = parse_response(
            response, error_handler=handle_api_error)

        # Process the top scorers data
        # The API returns player data with statistics
        return top_scorers_data

    def get_top_yellow_cards(self, league_id: int, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get players with most yellow cards for a specific league and season.

        Args:
            league_id: League ID
            season: Season year (defaults to current season)

        Returns:
            List of player statistics with yellow card information
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        response = self.client.get_top_yellow_cards(
            league_id=league_id, season=season)
        top_yellow_cards_data = parse_response(
            response, error_handler=handle_api_error)

        # Process the top yellow cards data
        return top_yellow_cards_data

    def get_top_red_cards(self, league_id: int, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get players with most red cards for a specific league and season.

        Args:
            league_id: League ID
            season: Season year (defaults to current season)

        Returns:
            List of player statistics with red card information
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        response = self.client.get_top_red_cards(
            league_id=league_id, season=season)
        top_red_cards_data = parse_response(
            response, error_handler=handle_api_error)

        # Process the top red cards data
        return top_red_cards_data

    def get_top_cards(self, league_id: int, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get players with most cards (both yellow and red) for a specific league and season.

        Args:
            league_id: League ID
            season: Season year (defaults to current season)

        Returns:
            List of player statistics with combined card information
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        # Get both yellow and red cards data
        yellow_cards_data = self.get_top_yellow_cards(
            league_id=league_id, season=season)
        red_cards_data = self.get_top_red_cards(
            league_id=league_id, season=season)

        # Combine both datasets
        # Use a dictionary to track players we've seen to avoid duplicates
        players_map = {}

        # Process yellow cards first
        for player_data in yellow_cards_data:
            player_id = player_data.get("player", {}).get("id")
            if player_id:
                players_map[player_id] = player_data

        # Then add or update with red cards data
        for player_data in red_cards_data:
            player_id = player_data.get("player", {}).get("id")
            if not player_id:
                continue

            if player_id in players_map:
                # Player already exists from yellow cards data
                # We need to combine the statistics
                existing_stats = players_map[player_id].get(
                    "statistics", [{}])[0] if players_map[player_id].get("statistics") else {}
                new_stats = player_data.get("statistics", [{}])[
                    0] if player_data.get("statistics") else {}

                # Make sure we have cards data in both
                existing_cards = existing_stats.get("cards", {})
                new_cards = new_stats.get("cards", {})

                # Update the existing player's data to include red cards
                # Since this was from yellow cards originally, it might not have red cards info
                if "red" not in existing_cards and "red" in new_cards:
                    existing_cards["red"] = new_cards["red"]

                # Update the statistics in the player data
                if players_map[player_id].get("statistics") and len(players_map[player_id]["statistics"]) > 0:
                    players_map[player_id]["statistics"][0]["cards"] = existing_cards
            else:
                # Player isn't in our map yet, add them
                players_map[player_id] = player_data

        # Convert back to a list
        combined_cards_data = list(players_map.values())

        return combined_cards_data

    def get_most_appearances(self, league_id: int, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get players with most match appearances for a specific league and season.

        Args:
            league_id: League ID
            season: Season year (defaults to current season)

        Returns:
            List of player statistics with appearance information, sorted by most appearances
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        # Since API doesn't have a specific endpoint for top appearances,
        # we'll fetch all players and sort/filter them manually
        all_players = []
        current_page = 1
        max_pages = 5  # Limit to reasonable number of pages to avoid excessive API calls

        # Fetch players data from multiple pages if available
        while current_page <= max_pages:
            try:
                logger.info(
                    f"Fetching players data for league {league_id}, season {season}, page {current_page}")
                response = self.client.get_league_players(
                    league_id=league_id,
                    season=season,
                    page=current_page
                )

                # Parse the response
                players_data = parse_response(
                    response, error_handler=handle_api_error)

                if not players_data:
                    # No more data available
                    break

                # Add to our collection
                all_players.extend(players_data)

                # Get pagination info if available
                pagination = response.get("paging", {})
                total_pages = pagination.get("total", 1)

                if current_page >= total_pages:
                    # No more pages available
                    break

                # Move to next page
                current_page += 1

            except APIError as e:
                logger.error(f"Error fetching players data: {e}")
                break

        # Now sort the players by number of appearances in descending order
        # Filter out players missing statistics or games and compute appearance counts
        valid_players = []
        for player in all_players:
            stats_list = player.get("statistics")
            if not isinstance(stats_list, list) or not stats_list:
                continue
            games = stats_list[0].get("games", {}) or {}
            # Handle both correct and misspelled keys
            appearances = games.get("appearances", games.get("appearences"))
            if not isinstance(appearances, int):
                continue
            # Store temporary count for sorting
            player['_appearances_count'] = appearances
            valid_players.append(player)

        # Sort players by appearances descending
        sorted_players = sorted(
            valid_players,
            key=lambda x: x['_appearances_count'],
            reverse=True
        )

        # Remove temporary key before returning
        for player in sorted_players:
            player.pop('_appearances_count', None)

        return sorted_players

    def get_most_passes(self, league_id: int, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get players who completed the most passes for a specific league and season.

        Args:
            league_id: League ID
            season: Season year (defaults to current season)

        Returns:
            List of player statistics with passing information, sorted by most passes completed
        """
        # If no season is specified, use the current season
        if season is None:
            season = self.get_current_season()

        # Since API doesn't have a specific endpoint for top passers,
        # we'll fetch all players and sort/filter them manually
        all_players = []
        current_page = 1
        max_pages = 5  # Limit to reasonable number of pages to avoid excessive API calls

        # Fetch players data from multiple pages if available
        while current_page <= max_pages:
            try:
                logger.info(
                    f"Fetching players data for league {league_id}, season {season}, page {current_page}")
                response = self.client.get_top_passes(
                    league_id=league_id,
                    season=season
                )

                # Parse the response
                players_data = parse_response(
                    response, error_handler=handle_api_error)

                if not players_data:
                    # No more data available
                    break

                # Add to our collection
                all_players.extend(players_data)

                # Get pagination info if available
                pagination = response.get("paging", {})
                total_pages = pagination.get("total", 1)

                if current_page >= total_pages or "page" not in response.get("parameters", {}):
                    # No more pages available or no pagination information
                    break

                # Move to next page
                current_page += 1

            except APIError as e:
                logger.error(f"Error fetching players passing data: {e}")
                break

        # Filter out players with invalid or missing statistics
        valid_players = []
        for player in all_players:
            try:
                # Check if player has valid statistics
                stats = player.get("statistics", [])
                if not stats or not isinstance(stats, list):
                    continue

                # Get passing data
                passes = stats[0].get("passes", {})
                if not passes or not isinstance(passes, dict):
                    continue

                # Check if we have valid total passes data
                total_passes = passes.get("total")

                # Skip players with None or invalid total passes
                if total_passes is None or not isinstance(total_passes, (int, float)):
                    continue

                # This player has valid data, keep it
                valid_players.append(player)
            except Exception as e:
                # Skip problematic players
                logger.warning(f"Skipping player with invalid data: {str(e)}")
                continue

        # Now sort the valid players by number of total passes in descending order
        sorted_players = sorted(
            valid_players,
            key=lambda x: (
                # Get passes from statistics
                x.get("statistics", [{}])[0].get("passes", {}).get("total", 0)
            ),
            reverse=True  # Descending order
        )

        # Log the result
        logger.info(
            f"Found {len(sorted_players)} players with valid passing data out of {len(all_players)} total players")

        return sorted_players
