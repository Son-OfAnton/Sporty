"""
CLI commands for displaying top performers in leagues.
"""

import click
import logging
from typing import Optional, Dict, Any, List
from tabulate import tabulate
from colorama import Fore, Style, init as colorama_init

from app.services.football_service import FootballService
from app.utils.error_handlers import APIError

logger = logging.getLogger(__name__)


@click.group()
def top_performer():
    """Get top performers across different metrics."""
    pass


@top_performer.command(name="goals")
@click.option(
    "--league", "-l",
    help="League ID to get top scorers for.",
    type=int,
    required=True
)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
@click.option(
    "--limit", "-n",
    help="Number of top scorers to display.",
    type=int,
    default=10
)
@click.option(
    "--detailed/--simple",
    help="Show detailed player information.",
    default=False
)
def top_goal_scorers(league: int, season: Optional[int], limit: int, detailed: bool):
    """
    Display the top goal scorers for a specific league and season.

    Examples:

    \b
    # Show top 10 goal scorers for Premier League (league ID 39) in current season
    sporty top-performer goals --league 39

    \b
    # Show top 5 goal scorers for La Liga (league ID 140) in 2022 season
    sporty top-performer goals --league 140 --season 2022 --limit 5

    \b
    # Show detailed information for top goal scorers
    sporty top-performer goals --league 39 --detailed
    """
    # Initialize colorama
    colorama_init()

    try:
        service = FootballService()

        # Get the league information for display
        leagues = service.get_leagues(season=season)
        league_name = next(
            (l.name for l in leagues if l.id == league), f"League {league}")

        # Get the season (using current if not specified)
        if season is None:
            season = service.get_current_season()

        click.echo(
            f"\n{Fore.GREEN}Top Goal Scorers for {league_name} ({season}/{season+1}){Style.RESET_ALL}\n")

        # Get the top scorers
        top_scorers = service.get_top_scorers(league_id=league, season=season)

        if not top_scorers:
            click.echo(
                f"{Fore.YELLOW}No top scorer data available for this league and season.{Style.RESET_ALL}")
            return

        # Process and display top scorers
        display_top_scorers(top_scorers[:limit], detailed)

    except APIError as e:
        click.echo(
            f"{Fore.RED}API Error: {e.message}{Style.RESET_ALL}", err=True)
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}", err=True)
        logger.exception("Error fetching top scorers")


def display_top_scorers(top_scorers: List[Dict[str, Any]], detailed: bool = False):
    """
    Format and display top scorers data.

    Args:
        top_scorers: List of top scorer data from API
        detailed: Whether to show detailed information
    """
    # Initialize colorama
    colorama_init()

    if not top_scorers:
        click.echo(f"{Fore.YELLOW}No data available.{Style.RESET_ALL}")
        return

    # Prepare table headers and rows
    if detailed:
        headers = ["Rank", "Player", "Age", "Team", "Position",
                   "Nationality", "Games", "Goals", "Assists", "Minutes", "Goals/Game"]
    else:
        headers = ["Rank", "Player", "Team", "Games", "Goals"]

    rows = []

    for idx, scorer_data in enumerate(top_scorers, 1):
        player = scorer_data.get("player", {})
        statistics = scorer_data.get("statistics", [])[
            0] if scorer_data.get("statistics") else {}

        # Extract player information
        player_name = player.get("name", "Unknown")
        player_age = player.get("age", "N/A")
        player_nationality = player.get("nationality", "Unknown")
        player_photo = player.get("photo", "")

        # Extract team information
        team = statistics.get("team", {})
        team_name = team.get("name", "Unknown")

        # Extract performance statistics
        games = statistics.get("games", {})
        goals = statistics.get("goals", {})

        games_played = games.get("appearences", 0)
        position = games.get("position", "Unknown")
        minutes = games.get("minutes", 0)
        goals_total = goals.get("total", 0)
        assists = statistics.get("goals", {}).get("assists", 0)

        # Calculate goals per game (avoiding division by zero)
        goals_per_game = round(goals_total / games_played,
                               2) if games_played > 0 else 0

        # Format the player name with color
        formatted_name = f"{Fore.CYAN}{Style.BRIGHT}{player_name}{Style.RESET_ALL}"

        # Start building the row
        if detailed:
            row = [
                idx,
                formatted_name,
                player_age,
                team_name,
                position,
                player_nationality,
                games_played,
                f"{Fore.YELLOW}{goals_total}{Style.RESET_ALL}",
                assists,
                minutes,
                goals_per_game
            ]
        else:
            row = [
                idx,
                formatted_name,
                team_name,
                games_played,
                f"{Fore.YELLOW}{goals_total}{Style.RESET_ALL}"
            ]

        # Add row to output
        rows.append(row)

    # Display the table
    click.echo(tabulate(rows, headers=headers, tablefmt="pretty"))

    # Add helpful hint about detailed view
    if not detailed:
        click.echo(
            f"\n{Fore.CYAN}Tip: Use --detailed flag for more player information.{Style.RESET_ALL}")


@top_performer.command(name="assists")
@click.option(
    "--league", "-l",
    help="League ID to get top assisters for.",
    type=int,
    required=True
)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
@click.option(
    "--limit", "-n",
    help="Number of top assisters to display.",
    type=int,
    default=10
)
@click.option(
    "--detailed/--simple",
    help="Show detailed player information.",
    default=False
)
def top_assisters(league: int, season: Optional[int], limit: int, detailed: bool):
    """
    Display the top assisters for a specific league and season.

    Examples:

    \b
    # Show top 10 assisters for Premier League (league ID 39) in current season
    sporty top-performer assists --league 39

    \b
    # Show top 5 assisters for La Liga (league ID 140) in 2022 season
    sporty top-performer assists --league 140 --season 2022 --limit 5

    \b
    # Show detailed information for top assisters
    sporty top-performer assists --league 39 --detailed
    """
    # Initialize colorama
    colorama_init()

    try:
        service = FootballService()

        # Get the league information for display
        leagues = service.get_leagues(season=season)
        league_name = next(
            (l.name for l in leagues if l.id == league), f"League {league}")

        # Get the season (using current if not specified)
        if season is None:
            season = service.get_current_season()

        click.echo(
            f"\n{Fore.GREEN}Top Assisters for {league_name} ({season}/{season+1}){Style.RESET_ALL}\n")

        # Get the top scorers data (which also contains assists)
        top_scorers = service.get_top_scorers(league_id=league, season=season)

        if not top_scorers:
            click.echo(
                f"{Fore.YELLOW}No top assister data available for this league and season.{Style.RESET_ALL}")
            return

        # Sort by assists instead of goals
        top_assisters = sorted(
            top_scorers,
            key=lambda x: x.get("statistics", [{}])[0].get(
                "goals", {}).get("assists", 0)
            if x.get("statistics") and len(x.get("statistics", [])) > 0 else 0,
            reverse=True
        )

        # Process and display top assisters
        display_top_assisters(top_assisters[:limit], detailed)

    except APIError as e:
        click.echo(
            f"{Fore.RED}API Error: {e.message}{Style.RESET_ALL}", err=True)
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}", err=True)
        logger.exception("Error fetching top assisters")


def display_top_assisters(top_assisters: List[Dict[str, Any]], detailed: bool = False):
    """
    Format and display top assisters data.

    Args:
        top_assisters: List of top assister data from API
        detailed: Whether to show detailed information
    """
    # Initialize colorama
    colorama_init()

    if not top_assisters:
        click.echo(f"{Fore.YELLOW}No data available.{Style.RESET_ALL}")
        return

    # Prepare table headers and rows
    if detailed:
        headers = ["Rank", "Player", "Age", "Team", "Position", "Nationality",
                   "Games", "Assists", "Goals", "Minutes", "Assists/Game"]
    else:
        headers = ["Rank", "Player", "Team", "Games", "Assists"]

    rows = []

    for idx, assister_data in enumerate(top_assisters, 1):
        player = assister_data.get("player", {})
        statistics = assister_data.get("statistics", [])[
            0] if assister_data.get("statistics") else {}

        # Extract player information
        player_name = player.get("name", "Unknown")
        player_age = player.get("age", "N/A")
        player_nationality = player.get("nationality", "Unknown")
        player_photo = player.get("photo", "")

        # Extract team information
        team = statistics.get("team", {})
        team_name = team.get("name", "Unknown")

        # Extract performance statistics
        games = statistics.get("games", {})
        goals = statistics.get("goals", {})

        games_played = games.get("appearences", 0)
        position = games.get("position", "Unknown")
        minutes = games.get("minutes", 0)
        goals_total = goals.get("total", 0)
        assists = goals.get("assists", 0)

        # Calculate assists per game (avoiding division by zero)
        assists_per_game = round(
            assists / games_played, 2) if games_played > 0 else 0

        # Format the player name with color
        formatted_name = f"{Fore.CYAN}{Style.BRIGHT}{player_name}{Style.RESET_ALL}"

        # Start building the row
        if detailed:
            row = [
                idx,
                formatted_name,
                player_age,
                team_name,
                position,
                player_nationality,
                games_played,
                f"{Fore.YELLOW}{assists}{Style.RESET_ALL}",
                goals_total,
                minutes,
                assists_per_game
            ]
        else:
            row = [
                idx,
                formatted_name,
                team_name,
                games_played,
                f"{Fore.YELLOW}{assists}{Style.RESET_ALL}"
            ]

        # Add row to output
        rows.append(row)

    # Display the table
    click.echo(tabulate(rows, headers=headers, tablefmt="pretty"))

    # Add helpful hint about detailed view
    if not detailed:
        click.echo(
            f"\n{Fore.CYAN}Tip: Use --detailed flag for more player information.{Style.RESET_ALL}")


@top_performer.command(name="cards")
@click.option(
    "--league", "-l",
    help="League ID to get players with most cards for.",
    type=int,
    required=True
)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
@click.option(
    "--card-type", "-c",
    help="Type of card to filter by.",
    type=click.Choice(["yellow", "red", "both"]),
    default="both"
)
@click.option(
    "--limit", "-n",
    help="Number of players to display.",
    type=int,
    default=10
)
@click.option(
    "--detailed/--simple",
    help="Show detailed player information.",
    default=False
)
def top_cards(league: int, season: Optional[int], card_type: str, limit: int, detailed: bool):
    """
    Display players with most yellow and/or red cards for a specific league and season.

    Examples:

    \b
    # Show players with most cards (both yellow and red) for Premier League (league ID 39)
    sporty top-performer cards --league 39

    \b
    # Show players with most yellow cards only
    sporty top-performer cards --league 39 --card-type yellow

    \b
    # Show players with most red cards only
    sporty top-performer cards --league 39 --card-type red

    \b
    # Show detailed information for top 5 carded players in La Liga (league ID 140) for 2022 season
    sporty top-performer cards --league 140 --season 2022 --limit 5 --detailed
    """
    # Initialize colorama
    colorama_init()

    try:
        service = FootballService()

        # Get the league information for display
        leagues = service.get_leagues(season=season)
        league_name = next(
            (l.name for l in leagues if l.id == league), f"League {league}")

        # Get the season (using current if not specified)
        if season is None:
            season = service.get_current_season()

        # Determine the title based on card type
        if card_type == "yellow":
            title = f"{Fore.YELLOW}Players with Most Yellow Cards"
        elif card_type == "red":
            title = f"{Fore.RED}Players with Most Red Cards"
        else:
            title = f"{Fore.YELLOW}Players with Most Cards {Fore.RESET}(Yellow & Red)"

        click.echo(
            f"\n{title} for {Fore.GREEN}{league_name} ({season}/{season+1}){Style.RESET_ALL}\n")

        # Get the top cards data
        top_cards_data = service.get_top_cards(league_id=league, season=season)

        if not top_cards_data:
            click.echo(
                f"{Fore.YELLOW}No card data available for this league and season.{Style.RESET_ALL}")
            return

        # Sort and filter based on card type
        if card_type == "yellow":
            # Sort by yellow cards
            sorted_data = sorted(
                top_cards_data,
                key=lambda x: x.get("statistics", [{}])[0].get(
                    "cards", {}).get("yellow", 0)
                if x.get("statistics") and len(x.get("statistics", [])) > 0 else 0,
                reverse=True
            )
        elif card_type == "red":
            # Sort by red cards
            sorted_data = sorted(
                top_cards_data,
                key=lambda x: x.get("statistics", [{}])[
                    0].get("cards", {}).get("red", 0)
                if x.get("statistics") and len(x.get("statistics", [])) > 0 else 0,
                reverse=True
            )
        else:
            # Sort by total cards (yellow + red)
            sorted_data = sorted(
                top_cards_data,
                key=lambda x: (
                    x.get("statistics", [{}])[0].get("cards", {}).get("yellow", 0) +
                    x.get("statistics", [{}])[0].get("cards", {}).get("red", 0)
                ) if x.get("statistics") and len(x.get("statistics", [])) > 0 else 0,
                reverse=True
            )

        # Process and display top cards data
        display_top_cards(sorted_data[:limit], card_type, detailed)

    except APIError as e:
        click.echo(
            f"{Fore.RED}API Error: {e.message}{Style.RESET_ALL}", err=True)
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}", err=True)
        logger.exception("Error fetching players with most cards")


def display_top_cards(top_cards_data: List[Dict[str, Any]], card_type: str = "both", detailed: bool = False):
    """
    Format and display top cards data.

    Args:
        top_cards_data: List of player data with card statistics
        card_type: Type of card to display ("yellow", "red", or "both")
        detailed: Whether to show detailed information
    """
    # Initialize colorama
    colorama_init()

    if not top_cards_data:
        click.echo(f"{Fore.YELLOW}No data available.{Style.RESET_ALL}")
        return

    # Prepare table headers and rows
    if detailed:
        if card_type == "yellow":
            headers = ["Rank", "Player", "Age", "Team", "Position", "Games",
                       f"{Fore.YELLOW}Yellow Cards{Style.RESET_ALL}", "Minutes"]
        elif card_type == "red":
            headers = ["Rank", "Player", "Age", "Team", "Position",
                       "Games", f"{Fore.RED}Red Cards{Style.RESET_ALL}", "Minutes"]
        else:
            headers = ["Rank", "Player", "Age", "Team", "Position", "Games",
                       f"{Fore.YELLOW}Yellow{Style.RESET_ALL}", f"{Fore.RED}Red{Style.RESET_ALL}", "Total", "Minutes"]
    else:
        if card_type == "yellow":
            headers = ["Rank", "Player", "Team", "Games",
                       f"{Fore.YELLOW}Yellow Cards{Style.RESET_ALL}"]
        elif card_type == "red":
            headers = ["Rank", "Player", "Team", "Games",
                       f"{Fore.RED}Red Cards{Style.RESET_ALL}"]
        else:
            headers = ["Rank", "Player", "Team", "Games",
                       f"{Fore.YELLOW}Yellow{Style.RESET_ALL}", f"{Fore.RED}Red{Style.RESET_ALL}", "Total"]

    rows = []

    for idx, player_data in enumerate(top_cards_data, 1):
        player = player_data.get("player", {})
        statistics = player_data.get("statistics", [])[
            0] if player_data.get("statistics") else {}

        # Extract player information
        player_name = player.get("name", "Unknown")
        player_age = player.get("age", "N/A")

        # Extract team information
        team = statistics.get("team", {})
        team_name = team.get("name", "Unknown")

        # Extract performance statistics
        games = statistics.get("games", {})
        cards = statistics.get("cards", {})

        games_played = games.get("appearences", 0)
        position = games.get("position", "Unknown")
        minutes = games.get("minutes", 0)
        yellow_cards = cards.get("yellow", 0)
        red_cards = cards.get("red", 0)
        total_cards = yellow_cards + red_cards

        # Format the player name with color
        formatted_name = f"{Fore.CYAN}{Style.BRIGHT}{player_name}{Style.RESET_ALL}"

        # Different row format based on card type and detail level
        if detailed:
            if card_type == "yellow":
                row = [
                    idx,
                    formatted_name,
                    player_age,
                    team_name,
                    position,
                    games_played,
                    f"{Fore.YELLOW}{yellow_cards}{Style.RESET_ALL}",
                    minutes
                ]
            elif card_type == "red":
                row = [
                    idx,
                    formatted_name,
                    player_age,
                    team_name,
                    position,
                    games_played,
                    f"{Fore.RED}{red_cards}{Style.RESET_ALL}",
                    minutes
                ]
            else:
                row = [
                    idx,
                    formatted_name,
                    player_age,
                    team_name,
                    position,
                    games_played,
                    f"{Fore.YELLOW}{yellow_cards}{Style.RESET_ALL}",
                    f"{Fore.RED}{red_cards}{Style.RESET_ALL}",
                    f"{Fore.WHITE}{Style.BRIGHT}{total_cards}{Style.RESET_ALL}",
                    minutes
                ]
        else:
            if card_type == "yellow":
                row = [
                    idx,
                    formatted_name,
                    team_name,
                    games_played,
                    f"{Fore.YELLOW}{yellow_cards}{Style.RESET_ALL}"
                ]
            elif card_type == "red":
                row = [
                    idx,
                    formatted_name,
                    team_name,
                    games_played,
                    f"{Fore.RED}{red_cards}{Style.RESET_ALL}"
                ]
            else:
                row = [
                    idx,
                    formatted_name,
                    team_name,
                    games_played,
                    f"{Fore.YELLOW}{yellow_cards}{Style.RESET_ALL}",
                    f"{Fore.RED}{red_cards}{Style.RESET_ALL}",
                    f"{Fore.WHITE}{Style.BRIGHT}{total_cards}{Style.RESET_ALL}"
                ]

        rows.append(row)

    # Display the table
    click.echo(tabulate(rows, headers=headers, tablefmt="pretty"))

    # Add helpful hint about detailed view
    if not detailed:
        click.echo(
            f"\n{Fore.CYAN}Tip: Use --detailed flag for more player information.{Style.RESET_ALL}")


@top_performer.command(name="appearances")
@click.option(
    "--league", "-l",
    help="League ID to get players with most appearances for.",
    type=int,
    required=True
)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
@click.option(
    "--limit", "-n",
    help="Number of players to display.",
    type=int,
    default=10
)
@click.option(
    "--detailed/--simple",
    help="Show detailed player information.",
    default=False
)
def top_appearances(league: int, season: Optional[int], limit: int, detailed: bool):
    """
    Display players with most match appearances for a specific league and season.

    Examples:

    \b
    # Show top 10 players with most appearances for Premier League (league ID 39)
    sporty top-performer appearances --league 39

    \b
    # Show top 5 players with most appearances for La Liga (league ID 140) in 2022 season with detailed info
    sporty top-performer appearances --league 140 --season 2022 --limit 5 --detailed
    """
    # Initialize colorama
    colorama_init()

    try:
        service = FootballService()

        # Get the league information for display
        leagues = service.get_leagues(season=season)
        league_name = next(
            (l.name for l in leagues if l.id == league), f"League {league}")

        # Get the season (using current if not specified)
        if season is None:
            season = service.get_current_season()

        click.echo(
            f"\n{Fore.GREEN}Players with Most Appearances for {league_name} ({season}/{season+1}){Style.RESET_ALL}\n")

        # Get the top appearances data
        top_appearances_data = service.get_most_appearances(
            league_id=league, season=season)

        if not top_appearances_data:
            click.echo(
                f"{Fore.YELLOW}No appearance data available for this league and season.{Style.RESET_ALL}")
            return

        # Players should already be sorted by appearances from the API
        # But let's ensure it's sorted correctly
        sorted_data = sorted(
            top_appearances_data,
            key=lambda x: x.get("statistics", [{}])[0].get(
                "games", {}).get("appearences", 0)
            if x.get("statistics") and len(x.get("statistics", [])) > 0 else 0,
            reverse=True
        )

        # Process and display top appearances data
        display_most_appearances(sorted_data[:limit], detailed)

    except APIError as e:
        click.echo(
            f"{Fore.RED}API Error: {e.message}{Style.RESET_ALL}", err=True)
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}", err=True)
        logger.exception("Error fetching players with most appearances")


def display_most_appearances(appearances_data: List[Dict[str, Any]], detailed: bool = False):
    """
    Format and display data for players with most appearances.

    Args:
        appearances_data: List of player data with appearance statistics
        detailed: Whether to show detailed information
    """
    # Initialize colorama
    colorama_init()

    if not appearances_data:
        click.echo(f"{Fore.YELLOW}No data available.{Style.RESET_ALL}")
        return

    # Prepare table headers and rows
    if detailed:
        headers = ["Rank", "Player", "Age", "Team", "Position", "Nationality",
                   f"{Fore.CYAN}Matches{Style.RESET_ALL}", "Started", "Minutes", "Min/Match"]
    else:
        headers = ["Rank", "Player", "Team", "Position",
                   f"{Fore.CYAN}Matches{Style.RESET_ALL}", "Minutes"]

    rows = []

    for idx, player_data in enumerate(appearances_data, 1):
        # Extract basic player information
        player = player_data.get("player", {})

        # Get the first item in statistics array (usually contains the league stats)
        statistics = player_data.get("statistics", [])[0] if player_data.get(
            "statistics") and len(player_data.get("statistics", [])) > 0 else {}

        # Extract player information
        player_name = player.get("name", "Unknown")
        player_age = player.get("age", "N/A")
        player_nationality = player.get("nationality", "Unknown")

        # Extract team information
        team = statistics.get("team", {})
        team_name = team.get("name", "Unknown")

        # Extract performance statistics
        games = statistics.get("games", {})

        # Ensure "appearences" is spelled correctly (API might use "appearances" instead)
        matches_played = games.get("appearences", games.get("appearances", 0))
        matches_started = games.get("lineups", 0)
        position = games.get("position", "Unknown")
        minutes = games.get("minutes", 0)

        # Calculate minutes per match (avoiding division by zero)
        minutes_per_match = round(
            minutes / matches_played, 1) if matches_played > 0 else 0

        # Format the player name with color
        formatted_name = f"{Fore.CYAN}{Style.BRIGHT}{player_name}{Style.RESET_ALL}"

        # Format matches played with color
        formatted_matches = f"{Fore.CYAN}{Style.BRIGHT}{matches_played}{Style.RESET_ALL}"

        # Start building the row
        if detailed:
            row = [
                idx,
                formatted_name,
                player_age,
                team_name,
                position,
                player_nationality,
                formatted_matches,
                matches_started,
                minutes,
                minutes_per_match
            ]
        else:
            row = [
                idx,
                formatted_name,
                team_name,
                position,
                formatted_matches,
                minutes
            ]

        # Add row to output
        rows.append(row)

    # Display the table
    click.echo(tabulate(rows, headers=headers, tablefmt="pretty"))

    # Add helpful hint about detailed view
    if not detailed:
        click.echo(
            f"\n{Fore.CYAN}Tip: Use --detailed flag for more player information.{Style.RESET_ALL}")
        click.echo(
            f"{Fore.YELLOW}Note: This command may take longer to run as it processes all players in the league.{Style.RESET_ALL}")


@top_performer.command(name="passes")
@click.option(
    "--league", "-l",
    help="League ID to get players with most passes for.",
    type=int,
    required=True
)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
@click.option(
    "--limit", "-n",
    help="Number of players to display.",
    type=int,
    default=10
)
@click.option(
    "--detailed/--simple",
    help="Show detailed player information.",
    default=False
)
@click.option(
    "--min-accuracy", "-a",
    help="Minimum pass accuracy percentage to qualify.",
    type=float,
    default=0.0
)
def most_passes(league: int, season: Optional[int], limit: int, detailed: bool, min_accuracy: float):
    """
    Display players who have completed the most passes in a league and season.

    Examples:

    \b
    # Show top 10 passers for Premier League (league ID 39)
    sporty top-performer passes --league 39

    \b
    # Show top 5 passers for La Liga (league ID 140) in 2022 season
    sporty top-performer passes --league 140 --season 2022 --limit 5

    \b
    # Show detailed information for players with most passes
    sporty top-performer passes --league 39 --detailed

    \b
    # Show only players with at least 80% pass accuracy
    sporty top-performer passes --league 39 --min-accuracy 80
    """
    # Initialize colorama
    colorama_init()

    try:
        service = FootballService()

        # Get the league information for display
        leagues = service.get_leagues(season=season)
        league_name = next(
            (l.name for l in leagues if l.id == league), f"League {league}")

        # Get the season (using current if not specified)
        if season is None:
            season = service.get_current_season()

        click.echo(
            f"\n{Fore.GREEN}Players with Most Passes in {league_name} ({season}/{season+1}){Style.RESET_ALL}\n")
        click.echo(
            f"{Fore.YELLOW}Fetching players data... This may take a moment...{Style.RESET_ALL}")

        # Get players with most passes
        passing_data = service.get_most_passes(league_id=league, season=season)

        if not passing_data:
            click.echo(
                f"{Fore.YELLOW}No passing data available for this league and season.{Style.RESET_ALL}")
            return

        # Filter by minimum pass accuracy if specified
        if min_accuracy > 0:
            filtered_players = []
            for player in passing_data:
                try:
                    stats = player.get("statistics", [])[0] if player.get(
                        "statistics") and len(player.get("statistics", [])) > 0 else {}
                    passes = stats.get("passes", {})

                    # Get accuracy (may be stored as percentage or decimal)
                    accuracy = passes.get("accuracy", 0)

                    # Convert to percentage if stored as decimal
                    if isinstance(accuracy, (int, float)) and accuracy <= 1.0:
                        accuracy = accuracy * 100

                    if isinstance(accuracy, (int, float)) and accuracy >= min_accuracy:
                        filtered_players.append(player)
                except Exception:
                    # Skip problematic players
                    continue

            passing_data = filtered_players

            if not passing_data:
                click.echo(
                    f"{Fore.YELLOW}No players found with at least {min_accuracy}% pass accuracy.{Style.RESET_ALL}")
                return

        # Process and display players with most passes
        display_most_passes(passing_data[:limit], detailed)

    except APIError as e:
        click.echo(
            f"{Fore.RED}API Error: {e.message}{Style.RESET_ALL}", err=True)
    except Exception as e:
        click.echo(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}", err=True)
        logger.exception("Error fetching players with most passes")


def display_most_passes(passing_data: List[Dict[str, Any]], detailed: bool = False):
    """
    Format and display data for players with most passes.

    Args:
        passing_data: List of player data with passing statistics
        detailed: Whether to show detailed information
    """
    # Initialize colorama
    colorama_init()

    if not passing_data:
        click.echo(f"{Fore.YELLOW}No data available.{Style.RESET_ALL}")
        return

    # Prepare table headers and rows
    if detailed:
        headers = ["Rank", "Player", "Age", "Team", "Position", "Nationality",
                   f"{Fore.GREEN}Total Passes{Style.RESET_ALL}", "Accuracy %", "Key Passes", "Minutes", "Passes/90min"]
    else:
        headers = ["Rank", "Player", "Team", "Position",
                   f"{Fore.GREEN}Total Passes{Style.RESET_ALL}", "Accuracy %"]

    rows = []

    for idx, player_data in enumerate(passing_data, 1):
        # Extract basic player information
        player = player_data.get("player", {})

        # Get the first item in statistics array (usually contains the league stats)
        statistics = player_data.get("statistics", [])[0] if player_data.get(
            "statistics") and len(player_data.get("statistics", [])) > 0 else {}

        # Extract player information
        player_name = player.get("name", "Unknown")
        player_age = player.get("age", "N/A")
        player_nationality = player.get("nationality", "Unknown")

        # Extract team information
        team = statistics.get("team", {})
        team_name = team.get("name", "Unknown")

        # Extract performance statistics
        games = statistics.get("games", {})
        passes = statistics.get("passes", {})

        # Get passing data
        position = games.get("position", "Unknown")
        total_passes = passes.get("total", 0) or 0
        key_passes = passes.get("key", 0) or 0

        # Get accuracy (may be stored as percentage or decimal)
        accuracy = passes.get("accuracy", 0) or 0

        # Convert to percentage if stored as decimal
        if isinstance(accuracy, (int, float)) and accuracy <= 1.0:
            accuracy = round(accuracy * 100, 1)

        # Get minutes
        minutes = games.get("minutes", 0) or 0

        # Calculate passes per 90 minutes (avoiding division by zero)
        passes_per_90 = 0
        if minutes > 0:
            passes_per_90 = round((total_passes / minutes) * 90, 1)

        # Format the player name with color
        formatted_name = f"{Fore.CYAN}{Style.BRIGHT}{player_name}{Style.RESET_ALL}"

        # Format total passes with color
        formatted_passes = f"{Fore.GREEN}{Style.BRIGHT}{total_passes}{Style.RESET_ALL}"

        # Start building the row
        if detailed:
            row = [
                idx,
                formatted_name,
                player_age,
                team_name,
                position,
                player_nationality,
                formatted_passes,
                accuracy,
                key_passes,
                minutes,
                passes_per_90
            ]
        else:
            row = [
                idx,
                formatted_name,
                team_name,
                position,
                formatted_passes,
                accuracy
            ]

        # Add row to output
        rows.append(row)

    # Display the table
    click.echo(tabulate(rows, headers=headers, tablefmt="pretty"))

    # Add helpful hint about detailed view
    if not detailed:
        click.echo(
            f"\n{Fore.CYAN}Tip: Use --detailed flag for more player information.{Style.RESET_ALL}")
        click.echo(
            f"{Fore.YELLOW}Note: This command may take longer to run as it processes all players in the league.{Style.RESET_ALL}")
