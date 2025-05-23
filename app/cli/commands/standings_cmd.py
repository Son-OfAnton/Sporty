"""
CLI commands for handling league standings data.
"""

import click
import logging
import datetime
from tabulate import tabulate
from colorama import Fore, Style, init

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService

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
def league_standings(league, name, country, season):
    """
    Display current league standings for a specific league and season.

    Displays team rankings, points, wins, draws, losses, and goal statistics.
    
    Specify league either by ID or by name.
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
            matching_leagues = [l for l in leagues if name.lower() in l.name.lower()]
            
            if not matching_leagues:
                click.echo(f"No leagues found matching '{name}'. Please try a different name or use league ID.")
                return
            
            # If multiple matches, let the user select one
            if len(matching_leagues) > 1:
                click.echo(f"\nMultiple leagues match '{name}':")
                for idx, l in enumerate(matching_leagues):
                    click.echo(f"{idx+1}. {l.name} ({l.country}) [ID: {l.id}]")
                
                idx = click.prompt("Enter the number of the league to view", type=int, default=1)
                try:
                    league = matching_leagues[idx-1].id
                    click.echo(f"Selected: {matching_leagues[idx-1].name} (ID: {league})")
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
            
        click.echo(f"Fetching standings for league ID {league} in season {season}...\n")
        
        # Get standings
        standings_list = service.get_standings(league_id=league, season=season)
        
        if not standings_list:
            click.echo("No standings found for the specified league and season.")
            return
            
        # Format data for tabulate
        headers = ["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]
        table_data = []
        
        for standing in standings_list:
            # Calculate goal difference
            gd = standing.goal_difference
            gd_str = f"{gd:+d}" if gd != 0 else "0"
            
            # Add row to table
            row = [
                # Position with color for top 4, relegation zone, etc.
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
        
        # Display current date and time info
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"\n{Fore.BLUE}Standings as of: {current_time}{Style.RESET_ALL}")
            
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
            
        click.echo(f"Fetching available leagues{' for ' + country if country else ''} in season {season}...\n")
        
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