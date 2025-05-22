"""
CLI commands for handling match data.
"""

import click
import logging
from datetime import datetime
from colorama import Fore, Style, init

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService
from app.cli.commands.utils import display_fixtures

logger = logging.getLogger(__name__)

@click.group()
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
    # Initialize colorama
    init()

    try:
        service = FootballService()

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

            display_fixtures(matches, format)

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

                display_fixtures(fixtures, format)

            # Summary
            total_matches = sum(len(fixtures)
                                for fixtures in matches_by_league.values())
            click.echo(
                f"\n{Fore.BLUE}{Style.BRIGHT}Total: {total_matches} matches in {len(matches_by_league)} leagues{Style.RESET_ALL}")

    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)