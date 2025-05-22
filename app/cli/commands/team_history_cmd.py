"""
CLI commands for fetching team match history.
"""

import click
import logging
from datetime import datetime, timedelta
from colorama import Fore, Style, init
from tabulate import tabulate

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService
from app.cli.commands.utils import display_fixtures

logger = logging.getLogger(__name__)

@click.command(name="history")
@click.argument("team_id", type=int)
@click.option(
    "--days", "-d",
    help="Number of days in the past to fetch results for (default: 30).",
    type=int,
    default=30
)
@click.option(
    "--from-date",
    help="Start date for results (YYYY-MM-DD format). Overrides --days if specified.",
    type=str
)
@click.option(
    "--to-date",
    help="End date for results (YYYY-MM-DD format). Defaults to today if not specified.",
    type=str
)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). If specified, ignores date options and shows all season matches.",
    type=int
)
@click.option(
    "--format", "-f",
    help="Output format (table or detailed).",
    type=click.Choice(["table", "detailed"]),
    default="table"
)
@click.option(
    "--timezone", "-tz",
    help="Timezone for match times (e.g. 'Europe/London').",
    type=str,
    default="UTC"
)
@click.option(
    "--limit", "-l",
    help="Maximum number of matches to display.",
    type=int
)
def team_history(team_id, days, from_date, to_date, season, format, timezone, limit):
    """
    Display past match results for a specific team.
    
    TEAM_ID: ID of the team to display history for
    """
    # Initialize colorama
    init()
    
    try:
        service = FootballService()
        
        # First, get team info
        team = service.get_team(team_id)
        if not team:
            click.echo(f"Team with ID {team_id} not found.")
            return
        
        click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Match History for {team.name}{Style.RESET_ALL}")
        
        # Determine date range or use season
        if season:
            click.echo(f"Season: {season}")
            matches = service.get_team_season_matches(team_id=team_id, season=season, timezone=timezone)
        else:
            # Calculate date range
            end_date = datetime.now()
            if to_date:
                try:
                    end_date = datetime.strptime(to_date, "%Y-%m-%d")
                except ValueError:
                    click.echo(f"Invalid to-date format. Please use YYYY-MM-DD format.")
                    return
            
            start_date = end_date - timedelta(days=days)
            if from_date:
                try:
                    start_date = datetime.strptime(from_date, "%Y-%m-%d")
                except ValueError:
                    click.echo(f"Invalid from-date format. Please use YYYY-MM-DD format.")
                    return
                    
            # Format dates for display and API
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            click.echo(f"Period: {start_date_str} to {end_date_str}")
            
            # Get matches for the specified date range
            matches = service.get_team_matches_by_date_range(
                team_id=team_id,
                from_date=start_date_str,
                to_date=end_date_str,
                timezone=timezone
            )
        
        if not matches:
            click.echo(f"No matches found for the specified criteria.")
            return
            
        # Apply limit if specified
        if limit and limit > 0 and len(matches) > limit:
            matches = matches[:limit]
            click.echo(f"Showing {limit} of {len(matches)} matches.")
        
        # Sort matches by date (most recent first)
        matches.sort(key=lambda m: m.date, reverse=True)
        
        # Display match results
        click.echo("\nMatch Results:")
        
        # Display fixtures using the shared utility function
        display_fixtures(matches, format)
        
        # Display statistics
        wins = sum(1 for m in matches if 
            (m.home_team.id == team_id and m.home_team.winner) or 
            (m.away_team.id == team_id and m.away_team.winner))
        draws = sum(1 for m in matches if m.status.short == "FT" and not m.home_team.winner and not m.away_team.winner)
        losses = sum(1 for m in matches if 
            (m.home_team.id == team_id and m.away_team.winner) or 
            (m.away_team.id == team_id and m.home_team.winner))
        played = wins + draws + losses
        
        # Calculate goals
        goals_for = sum(m.home_team.goals if m.home_team.id == team_id else m.away_team.goals 
                        for m in matches if m.status.short == "FT" and
                        (m.home_team.goals is not None) and (m.away_team.goals is not None))
        goals_against = sum(m.away_team.goals if m.home_team.id == team_id else m.home_team.goals 
                        for m in matches if m.status.short == "FT" and
                        (m.home_team.goals is not None) and (m.away_team.goals is not None))
        
        # Display summary stats
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Summary Stats:{Style.RESET_ALL}")
        stats_table = [
            ["Matches Played", played],
            ["Wins", f"{Fore.GREEN}{wins}{Style.RESET_ALL}"],
            ["Draws", f"{Fore.YELLOW}{draws}{Style.RESET_ALL}"],
            ["Losses", f"{Fore.RED}{losses}{Style.RESET_ALL}"],
            ["Goals For", goals_for],
            ["Goals Against", goals_against],
            ["Goal Difference", f"{goals_for - goals_against:+d}"]
        ]
        click.echo(tabulate(stats_table, tablefmt="simple"))
        
    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        logger.exception("Error in team_history command")
        click.echo(f"Error: {str(e)}", err=True)