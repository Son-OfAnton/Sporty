"""
CLI commands for handling team lineup data.
"""

import click
import logging
from colorama import Fore, Style, init
from tabulate import tabulate

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService
from app.cli.commands.utils import get_position_color, display_visual_formation

logger = logging.getLogger(__name__)

@click.command(name="lineup")
@click.argument("fixture_id", type=int)
@click.option(
    "--visual/--no-visual",
    default=True,
    help="Display visual representation of formation."
)
def fixture_lineup(fixture_id, visual):
    """
    Display detailed lineup information for a specific fixture.
    
    FIXTURE_ID: ID of the fixture to display lineups for
    """
    # Initialize colorama
    init()
    
    try:
        service = FootballService()
        
        # Get lineups
        lineups = service.get_fixture_lineups(fixture_id)
        
        if not lineups:
            click.echo("No lineup information available for this fixture.")
            return
            
        # Get the fixture basic information if possible
        try:
            fixtures = service.get_matches(
                league_id=None,
                team_id=None,
                season=None,
                date=None,
                from_date=None,
                to_date=None,
                timezone="UTC",
                live=False
            )
            
            fixture = next((f for f in fixtures if f.id == fixture_id), None)
            if fixture:
                match_datetime = fixture.date.strftime("%Y-%m-%d %H:%M")
                click.echo(f"\n{Fore.YELLOW}{Style.BRIGHT}{match_datetime} - {fixture.league.name}{Style.RESET_ALL}")
                click.echo(f"{Fore.GREEN}{fixture.home_team.name} vs {fixture.away_team.name}{Style.RESET_ALL}")
                click.echo(f"Status: {fixture.status.long}\n")
        except Exception as e:
            # If we can't get the fixture info, just continue with lineups
            pass
            
        # Display home team lineup
        home_lineup = None
        away_lineup = None
        
        # Try to determine which is home and away team
        if fixture:
            home_id = fixture.home_team.id
            away_id = fixture.away_team.id
            
            home_lineup = lineups.get(home_id)
            away_lineup = lineups.get(away_id)
        else:
            # If we don't have fixture info, just use the first and second teams
            team_ids = list(lineups.keys())
            if len(team_ids) >= 1:
                home_lineup = lineups.get(team_ids[0])
            if len(team_ids) >= 2:
                away_lineup = lineups.get(team_ids[1])
                
        # Display home team lineup
        if home_lineup:
            click.echo(f"{Fore.MAGENTA}{Style.BRIGHT}{home_lineup.team_name}{Style.RESET_ALL}")
            click.echo(f"Formation: {Fore.YELLOW}{home_lineup.formation}{Style.RESET_ALL}")
            click.echo(f"Coach: {home_lineup.coach}")
            
            # Display starting XI in a visual formation if requested
            if visual and home_lineup.formation:
                click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Formation:{Style.RESET_ALL}")
                display_visual_formation(home_lineup)
            
            # Starting XI
            click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Starting XI:{Style.RESET_ALL}")
            starters_table = []
            for player in sorted(home_lineup.starters, key=lambda x: (x.position or "", x.name)):
                # Colorize by position
                position_color = get_position_color(player.position)
                starters_table.append([
                    f"{player.number}" if player.number else "-",
                    f"{position_color}{player.name}{Style.RESET_ALL}",
                    f"{position_color}{player.position}{Style.RESET_ALL}" if player.position else "-",
                    player.grid or "-"
                ])
            
            click.echo(tabulate(starters_table, headers=["#", "Player", "Position", "Grid"], tablefmt="simple"))
            
            # Substitutes
            click.echo(f"\n{Fore.YELLOW}Substitutes:{Style.RESET_ALL}")
            subs_table = []
            for player in sorted(home_lineup.substitutes, key=lambda x: (x.position or "", x.name)):
                position_color = get_position_color(player.position)
                subs_table.append([
                    f"{player.number}" if player.number else "-",
                    f"{position_color}{player.name}{Style.RESET_ALL}",
                    f"{position_color}{player.position}{Style.RESET_ALL}" if player.position else "-"
                ])
            
            click.echo(tabulate(subs_table, headers=["#", "Player", "Position"], tablefmt="simple"))
        
        # Display away team lineup
        if away_lineup:
            click.echo(f"\n{Fore.MAGENTA}{Style.BRIGHT}{away_lineup.team_name}{Style.RESET_ALL}")
            click.echo(f"Formation: {Fore.YELLOW}{away_lineup.formation}{Style.RESET_ALL}")
            click.echo(f"Coach: {away_lineup.coach}")
            
            # Display starting XI in a visual formation if requested
            if visual and away_lineup.formation:
                click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Formation:{Style.RESET_ALL}")
                display_visual_formation(away_lineup)
            
            # Starting XI
            click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Starting XI:{Style.RESET_ALL}")
            starters_table = []
            for player in sorted(away_lineup.starters, key=lambda x: (x.position or "", x.name)):
                # Colorize by position
                position_color = get_position_color(player.position)
                starters_table.append([
                    f"{player.number}" if player.number else "-",
                    f"{position_color}{player.name}{Style.RESET_ALL}",
                    f"{position_color}{player.position}{Style.RESET_ALL}" if player.position else "-",
                    player.grid or "-"
                ])
            
            click.echo(tabulate(starters_table, headers=["#", "Player", "Position", "Grid"], tablefmt="simple"))
            
            # Substitutes
            click.echo(f"\n{Fore.YELLOW}Substitutes:{Style.RESET_ALL}")
            subs_table = []
            for player in sorted(away_lineup.substitutes, key=lambda x: (x.position or "", x.name)):
                position_color = get_position_color(player.position)
                subs_table.append([
                    f"{player.number}" if player.number else "-",
                    f"{position_color}{player.name}{Style.RESET_ALL}",
                    f"{position_color}{player.position}{Style.RESET_ALL}" if player.position else "-"
                ])
            
            click.echo(tabulate(subs_table, headers=["#", "Player", "Position"], tablefmt="simple"))
            
    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)