"""
CLI commands for handling league standings data.
"""

import click
import logging
import datetime
from typing import Dict, Any, Optional, List
from tabulate import tabulate
from colorama import Fore, Style, init

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService
from app.models.football_data import TeamStanding

logger = logging.getLogger(__name__)


@click.group()
def standings():
    """Get league standings information."""
    pass


@standings.command(name="league")
@click.option(
    "--league", "-l",
    help="League ID to get standings for.",
    type=int,
    required=False
)
@click.option(
    "--name", "-n",
    help="League name (e.g., 'Premier League', 'La Liga'). Will try to find the matching league ID.",
    type=str,
    required=False
)
@click.option(
    "--country", "-c",
    help="Country name to filter leagues when using --name option.",
    type=str,
    required=False
)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
@click.option(
    "--filter", "-f",
    help="Filter standings by home/away/all matches.",
    type=click.Choice(["all", "home", "away"]),
    default="all"
)
def league_standings(league, name, country, season, filter):
    """
    Display current league standings for a specific league and season.

    Displays team rankings, points, wins, draws, losses, and goal statistics.

    Specify league either by ID or by name.

    Filter option allows you to see standings based on only home matches,
    only away matches, or all matches (default).
    """
    # Initialize colorama
    init()

    try:
        service = FootballService()

        # If season is not specified, use the current season
        if season is None:
            season = service.get_current_season()

        # If league ID is not provided, but name is, try to find matching league
        if league is None and name:
            click.echo(f"Searching for league '{name}'...")
            leagues = service.get_leagues(country=country, season=season)

            # Find leagues with matching names (case insensitive partial match)
            matching_leagues = [
                l for l in leagues if name.lower() in l.name.lower()]

            if not matching_leagues:
                click.echo(
                    f"No leagues found matching '{name}'. Please try a different name or use league ID.")
                return

            # If multiple matches, let the user select one
            if len(matching_leagues) > 1:
                click.echo(f"\nMultiple leagues match '{name}':")
                for idx, l in enumerate(matching_leagues):
                    click.echo(f"{idx+1}. {l.name} ({l.country}) [ID: {l.id}]")

                idx = click.prompt(
                    "Enter the number of the league to view", type=int, default=1)
                try:
                    league = matching_leagues[idx-1].id
                    click.echo(
                        f"Selected: {matching_leagues[idx-1].name} (ID: {league})")
                except IndexError:
                    click.echo("Invalid selection. Please try again.")
                    return
            else:
                # Only one match found
                league = matching_leagues[0].id
                click.echo(f"Found: {matching_leagues[0].name} (ID: {league})")

        # Verify we now have a league ID
        if league is None:
            click.echo("Please specify a league ID or name.")
            return

        filter_text = ""
        if filter == "home":
            filter_text = " (HOME MATCHES ONLY)"
        elif filter == "away":
            filter_text = " (AWAY MATCHES ONLY)"

        click.echo(
            f"Fetching standings for league ID {league} in season {season}{filter_text}...\n")

        # Get standings
        standings_list = service.get_standings(league_id=league, season=season)

        if not standings_list:
            click.echo(
                "No standings found for the specified league and season.")
            return

        # Get the raw API response to access home and away data
        raw_response = service.client._make_request(
            "standings", {"league": league, "season": season})
        standings_data = raw_response.get('response', [])

        # Format data for tabulate
        headers = ["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]
        table_data = []

        # If we have raw data and a valid filter, use it to create a filtered view
        if standings_data and filter in ["home", "away"]:
            # Extract the standings array from the first league
            try:
                league_data = standings_data[0].get("league", {})
                standings_array = league_data.get("standings", [])

                # Handle nested standings (some leagues have multiple groups)
                if standings_array and isinstance(standings_array[0], list):
                    standings_array = standings_array[0]

                # Process and display the filtered standings
                filtered_standings_rows = _process_filtered_standings(
                    standings_array, filter)

                if not filtered_standings_rows:
                    click.echo(
                        f"Unable to get {filter} standings data for this league.")
                    # Fall back to the original standings
                    _display_standard_standings(standings_list)
                else:
                    # Display the filtered standings
                    click.echo(tabulate(filtered_standings_rows,
                               headers=headers, tablefmt="pretty"))

            except (IndexError, KeyError) as e:
                logger.error(f"Error processing filtered standings: {e}")
                # Fall back to standard standings display
                click.echo(
                    f"Error processing {filter} standings. Displaying standard standings instead.")
                _display_standard_standings(standings_list)
        else:
            # Display standard standings
            _display_standard_standings(standings_list)

        # Display current date and time info
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        click.echo(
            f"\n{Fore.BLUE}Standings as of: {current_time}{Style.RESET_ALL}")
        if filter != "all":
            click.echo(
                f"{Fore.YELLOW}Note: Standings are based on {filter} matches only.{Style.RESET_ALL}")

    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@standings.command(name="list-leagues")
@click.option(
    "--country", "-c",
    help="Filter leagues by country name.",
    type=str,
    required=False
)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
def list_leagues(country, season):
    """
    List available leagues and their IDs.

    Use this to find league IDs to use with the 'standings league' command.
    """
    try:
        service = FootballService()

        # If season is not specified, use the current season
        if season is None:
            season = service.get_current_season()

        click.echo(
            f"Fetching available leagues{' for ' + country if country else ''} in season {season}...\n")

        leagues = service.get_leagues(country=country, season=season)

        if not leagues:
            click.echo("No leagues found with the specified criteria.")
            return

        # Format data for tabulate
        headers = ["ID", "League", "Country", "Type"]
        table_data = []

        for league in leagues:
            table_data.append([
                league.id,
                league.name,
                league.country,
                league.type or "N/A"
            ])

        # Display the table
        click.echo(tabulate(table_data, headers=headers, tablefmt="pretty"))
        click.echo(f"\nTotal: {len(leagues)} leagues found")

    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


def _format_position(position: int) -> str:
    """Format the position with appropriate color based on ranking."""
    if position <= 4:
        # Champions League positions (usually top 4) - green
        return f"{Fore.GREEN}{Style.BRIGHT}{position}{Style.RESET_ALL}"
    elif position <= 6:
        # Europa League positions (usually 5-6) - blue
        return f"{Fore.BLUE}{Style.BRIGHT}{position}{Style.RESET_ALL}"
    elif position >= 18:
        # Relegation positions (usually bottom 3 in a 20-team league) - red
        return f"{Fore.RED}{Style.BRIGHT}{position}{Style.RESET_ALL}"
    else:
        # Regular positions - normal text
        return str(position)


def _display_standard_standings(standings_list: List[TeamStanding]) -> None:
    """Display standard standings table."""
    headers = ["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]
    table_data = []

    for standing in standings_list:
        # Calculate goal difference
        gd = standing.goal_difference
        gd_str = f"{gd:+d}" if gd != 0 else "0"

        # Add row to table
        row = [
            # Position with color
            _format_position(standing.rank),
            standing.team.name,
            standing.played,
            standing.win,
            standing.draw,
            standing.lose,
            standing.goals_for,
            standing.goals_against,
            gd_str,
            f"{Fore.CYAN}{Style.BRIGHT}{standing.points}{Style.RESET_ALL}"
        ]

        table_data.append(row)

    # Display the table
    click.echo(tabulate(table_data, headers=headers, tablefmt="pretty"))


def _process_filtered_standings(standings_array: List[Dict[str, Any]], filter_type: str) -> List[List[Any]]:
    """
    Process standings array and return rows for display, filtered by home or away.

    Args:
        standings_array: List of standings data dictionaries from the API
        filter_type: Either "home" or "away"

    Returns:
        List of rows ready for tabulate display
    """
    if not standings_array:
        return []

    # Process standings based on filter type
    table_rows = []

    # Sort the standings by home/away points
    sorted_standings = sorted(
        standings_array,
        key=lambda x: x.get(filter_type, {}).get("points", 0),
        reverse=True
    )

    for i, standing_data in enumerate(sorted_standings):
        # Get team data
        team_data = standing_data.get("team", {})

        # Get filtered statistics
        filtered_stats = standing_data.get(filter_type, {})
        if not filtered_stats:
            continue

        # Calculate points if not provided by API
        points = filtered_stats.get("points")
        if points is None:
            points = filtered_stats.get(
                "win", 0) * 3 + filtered_stats.get("draw", 0)

        # Get goals data
        goals_data = filtered_stats.get("goals", {})

        # Calculate goal difference for filtered stats
        goals_for = goals_data.get("for", 0)
        goals_against = goals_data.get("against", 0)
        goal_diff = goals_for - goals_against
        gd_str = f"{goal_diff:+d}" if goal_diff != 0 else "0"

        # Format row
        row = [
            _format_position(i + 1),
            team_data.get("name", "Unknown"),
            filtered_stats.get("played", 0),
            filtered_stats.get("win", 0),
            filtered_stats.get("draw", 0),
            filtered_stats.get("lose", 0),
            goals_for,
            goals_against,
            gd_str,
            f"{Fore.CYAN}{Style.BRIGHT}{points}{Style.RESET_ALL}"
        ]
        table_rows.append(row)
    return table_rows
