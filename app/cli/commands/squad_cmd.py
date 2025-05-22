"""
CLI commands for handling team squad data.
"""

import click
import logging
from colorama import Fore, Style, init
from tabulate import tabulate

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService
from app.cli.commands.utils import get_position_color

logger = logging.getLogger(__name__)

@click.command(name="squad")
@click.argument("team_id", type=int)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
def team_squad(team_id, season):
    """
    Display all players in a team's squad for a specific season.
    
    TEAM_ID: ID of the team to display squad for
    """
    # Initialize colorama
    init()
    
    try:
        service = FootballService()
        
        # If no season specified, use current season
        if not season:
            season = service.get_current_season()
            click.echo(f"No season specified, using current season ({season})...")
            
        # First, get team info using get_team (not get_teams)
        team = service.get_team(team_id)
        if not team:
            click.echo(f"Team with ID {team_id} not found.")
            return
            
        click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}{team.name}{Style.RESET_ALL}")
        click.echo(f"Country: {team.country}")
        if team.founded:
            click.echo(f"Founded: {team.founded}")
        if team.venue_name:
            click.echo(f"Venue: {team.venue_name}")
        click.echo(f"Season: {season}")
        
        # Then, get squad players for that team and season
        players = service.get_players(team_id=team_id, season=season)
        
        if not players:
            click.echo("\nNo player data available for this team and season.")
            return
            
        # Group players by position
        goalkeepers = []
        defenders = []
        midfielders = []
        forwards = []
        others = []
        
        for player in players:
            if not player.position:
                others.append(player)
            elif player.position.lower() == "goalkeeper" or player.position.lower() == "gk":
                goalkeepers.append(player)
            elif "defender" in player.position.lower() or player.position.lower() in ["cb", "lb", "rb", "rwb", "lwb"]:
                defenders.append(player)
            elif "midfielder" in player.position.lower() or player.position.lower() in ["cm", "cdm", "cam", "rm", "lm", "dm", "am"]:
                midfielders.append(player)
            elif "forward" in player.position.lower() or "striker" in player.position.lower() or player.position.lower() in ["cf", "st", "rw", "lw"]:
                forwards.append(player)
            else:
                others.append(player)
        
        # Display squad by position
        if goalkeepers:
            click.echo(f"\n{Fore.YELLOW}{Style.BRIGHT}Goalkeepers:{Style.RESET_ALL}")
            _display_players(goalkeepers)
        
        if defenders:
            click.echo(f"\n{Fore.BLUE}{Style.BRIGHT}Defenders:{Style.RESET_ALL}")
            _display_players(defenders)
        
        if midfielders:
            click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Midfielders:{Style.RESET_ALL}")
            _display_players(midfielders)
        
        if forwards:
            click.echo(f"\n{Fore.RED}{Style.BRIGHT}Forwards:{Style.RESET_ALL}")
            _display_players(forwards)
            
        if others:
            click.echo(f"\n{Fore.WHITE}{Style.BRIGHT}Others:{Style.RESET_ALL}")
            _display_players(others)
            
        # Display total count
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Total: {len(players)} players{Style.RESET_ALL}")
        
    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


def _display_players(players):
    """Helper function to display a list of players."""
    from tabulate import tabulate
    
    table_data = []
    for player in sorted(players, key=lambda p: p.name):
        position_color = get_position_color(player.position)
        
        table_data.append([
            str(player.id),
            f"{position_color}{player.name}{Style.RESET_ALL}",
            player.age or "-",
            f"{position_color}{player.position}{Style.RESET_ALL}" if player.position else "-",
            player.nationality or "-"
        ])
    
    click.echo(tabulate(table_data, headers=["ID", "Name", "Age", "Position", "Nationality"], tablefmt="simple"))