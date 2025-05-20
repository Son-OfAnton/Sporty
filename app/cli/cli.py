#!/usr/bin/env python3
"""
Sporty CLI - Main entry point for the Sporty command-line interface.
"""

import click
import logging
import sys
import os
from datetime import datetime

from app.utils.error_handlers import setup_error_handling

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
logger.info("Logging is configured correctly.")


def main():
    """
    Main entry point for the Sporty CLI.

    This function sets up the command-line interface and handles
    command execution.
    """
    # Check if the script is being run directly
    if __name__ == "__main__":
        cli()
    else:
        # If imported, set up error handling
        setup_error_handling()


@click.group()
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable debug logging."
)
def cli(debug):
    """Sporty CLI - Your sports companion app."""
    # Set up logging based on debug flag
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set up error handling
    setup_error_handling()


@cli.group()
def matches():
    """Get match information."""
    pass


@matches.command(name="scores")
@click.option(
    "--league", "-l",
    help="League ID to filter matches.",
    type=int,
    required=False
)
@click.option(
    "--team", "-t",
    help="Team ID to filter matches.",
    type=int,
    required=False
)
@click.option(
    "--country", "-c",
    help="Country name to filter leagues.",
    type=str,
    required=False
)
@click.option(
    "--date", "-d",
    help="Date to filter matches (YYYY-MM-DD format).",
    type=str,
    required=False
)
@click.option(
    "--from-date",
    help="Start date for date range (YYYY-MM-DD format).",
    type=str,
    required=False
)
@click.option(
    "--to-date",
    help="End date for date range (YYYY-MM-DD format).",
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
    "--live/--no-live",
    help="Show only matches currently in progress.",
    default=False
)
@click.option(
    "--timezone", "-tz",
    help="Timezone for match times (e.g. 'Europe/London').",
    type=str,
    default="UTC"
)
@click.option(
    "--format", "-f",
    help="Output format (table or detailed).",
    type=click.Choice(["table", "detailed"]),
    default="table"
)
def match_scores(league, team, country, date, from_date, to_date, season, live, timezone, format):
    """
    Display match scores based on various filters.

    Defaults to showing matches from the current season.
    Use --live to show only matches currently in progress.
    """
    from app.services.football_service import FootballService
    from app.utils.error_handlers import APIError
    from tabulate import tabulate
    from colorama import Fore, Style, init

    # Initialize colorama
    init()

    try:
        service = FootballService()

        # If no specific date is provided and not in live mode,
        # default to today's date
        if not live and not date and not from_date and not to_date:
            date = datetime.now().strftime("%Y-%m-%d")
            click.echo(
                f"No date specified, showing matches for today ({date})...")

        # Set up header text
        header_parts = []
        if live:
            header_parts.append("live")
        if season:
            header_parts.append(f"season {season}")
        else:
            current_season = service.get_current_season()
            header_parts.append(f"current season ({current_season})")
        if date:
            header_parts.append(f"on {date}")
        elif from_date and to_date:
            header_parts.append(f"from {from_date} to {to_date}")
        if country:
            header_parts.append(f"in {country}")
        if league:
            header_parts.append(f"in league {league}")
        if team:
            header_parts.append(f"for team {team}")

        header_text = "Fetching " + " ".join(header_parts) + " matches..."
        click.echo(header_text)

        if league:
            # Get matches for a specific league
            matches = service.get_matches(
                league_id=league,
                team_id=team,
                season=season,
                date=date,
                from_date=from_date,
                to_date=to_date,
                timezone=timezone,
                live=live
            )

            if not matches:
                click.echo(f"No matches found for the specified filters.")
                return

            _display_fixtures(matches, format)

        else:
            # Get matches across all leagues
            matches_by_league = service.get_matches_by_league(
                country=country,
                season=season,
                date=date,
                live=live,
                timezone=timezone
            )

            if not matches_by_league:
                click.echo("No matches found for the specified filters.")
                return

            # Display matches by league
            for league, fixtures in matches_by_league.items():
                # League header
                click.echo(
                    f"\n{Fore.GREEN}{Style.BRIGHT}▶ {league.name} ({league.country}){Style.RESET_ALL}")

                _display_fixtures(fixtures, format)

            # Summary
            total_matches = sum(len(fixtures)
                                for fixtures in matches_by_league.values())
            click.echo(
                f"\n{Fore.BLUE}{Style.BRIGHT}Total: {total_matches} matches in {len(matches_by_league)} leagues{Style.RESET_ALL}")

    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

# Create an alias for the live command for backward compatibility


@cli.group()
def live():
    """Get live match information (alias for 'matches scores --live')."""
    pass


@live.command(name="scores")
@click.option(
    "--league", "-l",
    help="League ID to filter matches.",
    type=int,
    required=False
)
@click.option(
    "--country", "-c",
    help="Country name to filter leagues.",
    type=str,
    required=False
)
@click.option(
    "--timezone", "-t",
    help="Timezone for match times (e.g. 'Europe/London').",
    type=str,
    default="UTC"
)
@click.option(
    "--format", "-f",
    help="Output format (table or detailed).",
    type=click.Choice(["table", "detailed"]),
    default="table"
)
@click.pass_context
def live_scores(ctx, league, country, timezone, format):
    """
    Display live scores for matches currently in progress.

    If a league ID is provided, only shows matches from that league.
    If a country is provided, shows matches from all leagues in that country.
    """
    # This is a wrapper around matches scores --live
    ctx.forward(match_scores, live=True)


def _display_fixtures(fixtures, format):
    """Helper function to display fixtures."""
    from tabulate import tabulate
    from colorama import Fore, Style

    if format == "table":
        # Prepare table data
        table_data = []
        for fixture in fixtures:
            # Set status color based on match status
            if fixture.status.short in ["1H", "2H", "ET"]:
                status_color = Fore.GREEN  # Live match
            elif fixture.status.short in ["HT", "BT"]:
                status_color = Fore.YELLOW  # Break time
            elif fixture.status.short == "FT":
                status_color = Fore.BLUE  # Finished
            elif fixture.status.short in ["PST", "CANC", "ABD", "SUSP"]:
                status_color = Fore.RED  # Problem with match
            elif fixture.status.short == "NS":
                status_color = Fore.CYAN  # Not started yet
            else:
                status_color = Fore.WHITE  # Other status

            status_text = f"{status_color}{fixture.status.short}{Style.RESET_ALL}"

            # Add elapsed time for live matches
            if hasattr(fixture, 'status') and hasattr(fixture.status, 'elapsed') and fixture.status.elapsed:
                status_text += f" {fixture.status.elapsed}'"

            # Format score based on status
            if fixture.status.short == "NS":
                # Match not started
                score_text = f"{Fore.WHITE}vs{Style.RESET_ALL}"
            else:
                # Match in progress or finished
                home_goals = fixture.home_team.goals if fixture.home_team.goals is not None else 0
                away_goals = fixture.away_team.goals if fixture.away_team.goals is not None else 0
                score_text = f"{Fore.WHITE}{Style.BRIGHT}{home_goals} - {away_goals}{Style.RESET_ALL}"

            # Format date/time for not started matches
            date_text = ""
            if fixture.status.short == "NS":
                date_text = fixture.date.strftime("%H:%M")

            table_data.append([
                status_text,
                f"{fixture.home_team.name} {Fore.WHITE}vs{Style.RESET_ALL} {fixture.away_team.name}",
                score_text,
                date_text
            ])

        # Display table with the appropriate headers
        headers = ["Status", "Match", "Score", "Time"]
        if all(row[3] == "" for row in table_data):
            # If no time column is used, don't show it
            table_data = [row[0:3] for row in table_data]
            headers = headers[0:3]

        click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

    elif format == "detailed":
        # Detailed view for each fixture
        for fixture in fixtures:
            click.echo("\n" + "─" * 60)

            # Match header
            click.echo(
                f"{Fore.BLUE}{Style.BRIGHT}{fixture.home_team.name} vs {fixture.away_team.name}{Style.RESET_ALL}")

            # Status
            if fixture.status.short in ["1H", "2H", "ET"]:
                status_color = Fore.GREEN  # Live match
            elif fixture.status.short in ["HT", "BT"]:
                status_color = Fore.YELLOW  # Break time
            elif fixture.status.short == "FT":
                status_color = Fore.BLUE  # Finished
            elif fixture.status.short in ["PST", "CANC", "ABD", "SUSP"]:
                status_color = Fore.RED  # Problem with match
            elif fixture.status.short == "NS":
                status_color = Fore.CYAN  # Not started yet
            else:
                status_color = Fore.WHITE  # Other status

            status_text = f"{status_color}{fixture.status.long}{Style.RESET_ALL}"
            if hasattr(fixture, 'status') and hasattr(fixture.status, 'elapsed') and fixture.status.elapsed:
                status_text += f" ({fixture.status.elapsed}')"
            click.echo(f"Status: {status_text}")

            # Date and time
            date_str = fixture.date.strftime("%Y-%m-%d %H:%M")
            click.echo(f"Date: {date_str}")

            # Venue
            if fixture.venue:
                click.echo(f"Venue: {fixture.venue}")

            # Referee
            if fixture.referee:
                click.echo(f"Referee: {fixture.referee}")

            # Score
            if fixture.status.short != "NS":
                home_goals = fixture.home_team.goals if fixture.home_team.goals is not None else 0
                away_goals = fixture.away_team.goals if fixture.away_team.goals is not None else 0
                click.echo(
                    f"Score: {Fore.WHITE}{Style.BRIGHT}{home_goals}-{away_goals}{Style.RESET_ALL}")

            # Teams
            click.echo(
                f"Home: {Fore.CYAN}{fixture.home_team.name}{Style.RESET_ALL}")
            click.echo(
                f"Away: {Fore.CYAN}{fixture.away_team.name}{Style.RESET_ALL}")

            # Additional score information if available
            if fixture.score and fixture.score.halftime and fixture.status.short != "NS":
                ht = fixture.score.halftime
                ht_home = ht.get("home", 0)
                ht_away = ht.get("away", 0)
                click.echo(f"Halftime: {ht_home}-{ht_away}")

            if fixture.score and fixture.score.fulltime and fixture.status.short == "FT":
                ft = fixture.score.fulltime
                ft_home = ft.get("home", 0)
                ft_away = ft.get("away", 0)
                click.echo(f"Fulltime: {ft_home}-{ft_away}")

            if fixture.score and fixture.score.extratime and any(v is not None for v in fixture.score.extratime.values()):
                et = fixture.score.extratime
                et_home = et.get("home", 0)
                et_away = et.get("away", 0)
                click.echo(f"Extra time: {et_home}-{et_away}")

            if fixture.score and fixture.score.penalty and any(v is not None for v in fixture.score.penalty.values()):
                pen = fixture.score.penalty
                pen_home = pen.get("home", 0)
                pen_away = pen.get("away", 0)
                click.echo(f"Penalties: {pen_home}-{pen_away}")


if __name__ == '__main__':
    main()
