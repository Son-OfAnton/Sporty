"""
CLI commands for handling match statistics data.
"""

import click
import logging
from colorama import Fore, Style, init
from tabulate import tabulate

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService

logger = logging.getLogger(__name__)

@click.command(name="stats")
@click.argument("fixture_id", type=int)
def fixture_statistics(fixture_id):
    """
    Display detailed statistics for a specific fixture.
    
    FIXTURE_ID: ID of the fixture to display statistics for
    """
    # Initialize colorama
    init()
    
    try:
        service = FootballService()
        
        # Get the fixture data first
        matches = service.get_matches(
            league_id=None,
            team_id=None,
            season=None,
            date=None,
            from_date=None,
            to_date=None,
            timezone="UTC",
            live=False
        )
        
        # Find the specific fixture
        fixture = next((f for f in matches if f.id == fixture_id), None)
        
        # If fixture not found by ID, try to fetch it specifically
        if not fixture:
            click.echo(f"Fetching fixture {fixture_id}...")
        else:
            # Display basic fixture info
            match_datetime = fixture.date.strftime("%Y-%m-%d %H:%M")
            click.echo(f"\n{Fore.YELLOW}{Style.BRIGHT}{match_datetime} - {fixture.league.name}{Style.RESET_ALL}")
            click.echo(f"{Fore.GREEN}{fixture.home_team.name} {fixture.score_display} {fixture.away_team.name}{Style.RESET_ALL}")
            click.echo(f"Status: {fixture.status.long}\n")
            
        # Get comprehensive statistics
        stats = service.get_match_statistics(fixture_id)
        
        # 1. Display Events (Goals, Cards, Substitutions)
        click.echo(f"{Fore.CYAN}{Style.BRIGHT}Match Events:{Style.RESET_ALL}")
        
        if not stats.events:
            click.echo("No events recorded for this match.")
        else:
            # Group events by type
            goals = [e for e in stats.events if e.type == "Goal"]
            cards = [e for e in stats.events if e.type == "Card"]
            subs = [e for e in stats.events if e.type == "Substitution"]
            
            # Display goals
            if goals:
                click.echo(f"\n{Fore.GREEN}Goals:{Style.RESET_ALL}")
                goals_table = []
                for goal in sorted(goals, key=lambda x: x.time):
                    assist = f" (Assist: {goal.assist_player_name})" if goal.assist_player_name else ""
                    goals_table.append([
                        f"{goal.time}'",
                        goal.team_name,
                        f"{goal.player_name}{assist}",
                        goal.detail
                    ])
                click.echo(tabulate(goals_table, headers=["Time", "Team", "Scorer", "Type"], tablefmt="simple"))
                
            # Display cards
            if cards:
                click.echo(f"\n{Fore.YELLOW}Cards:{Style.RESET_ALL}")
                cards_table = []
                for card in sorted(cards, key=lambda x: x.time):
                    card_color = Fore.YELLOW if "yellow" in card.detail.lower() else Fore.RED
                    cards_table.append([
                        f"{card.time}'",
                        card.team_name,
                        card.player_name,
                        f"{card_color}{card.detail}{Style.RESET_ALL}"
                    ])
                click.echo(tabulate(cards_table, headers=["Time", "Team", "Player", "Card"], tablefmt="simple"))
                
            # Display substitutions
            if subs:
                click.echo(f"\n{Fore.BLUE}Substitutions:{Style.RESET_ALL}")
                subs_table = []
                for sub in sorted(subs, key=lambda x: x.time):
                    # For substitutions, the comment typically contains the player going out
                    player_out = sub.comments or "Unknown"
                    subs_table.append([
                        f"{sub.time}'",
                        sub.team_name,
                        f"{Fore.GREEN}IN: {sub.player_name}{Style.RESET_ALL}",
                        f"{Fore.RED}OUT: {player_out}{Style.RESET_ALL}"
                    ])
                click.echo(tabulate(subs_table, headers=["Time", "Team", "In", "Out"], tablefmt="simple"))
        
        # 2. Display Team Statistics
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Team Statistics:{Style.RESET_ALL}")
        
        if not stats.team_statistics:
            click.echo("No team statistics available for this match.")
        else:
            # Get both teams' statistics
            teams = list(stats.team_statistics.values())
            if len(teams) == 2:
                # Create a side-by-side comparison
                stats_table = []
                
                # Get all unique stat types from both teams
                stat_types = set()
                for team in teams:
                    for stat in team.statistics:
                        stat_types.add(stat.type)
                
                # Sort stat types for consistent display
                sorted_stat_types = sorted(stat_types)
                
                # Create the side-by-side comparison
                for stat_type in sorted_stat_types:
                    row = [stat_type]
                    
                    for team in teams:
                        # Find this statistic for this team
                        team_stat = next((s for s in team.statistics if s.type == stat_type), None)
                        if team_stat:
                            row.append(str(team_stat.value))
                        else:
                            row.append("N/A")
                    
                    stats_table.append(row)
                
                # Display the table
                click.echo(tabulate(stats_table, headers=["Statistic", teams[0].team_name, teams[1].team_name], tablefmt="simple"))
            else:
                # Display stats for each team individually
                for team in teams:
                    click.echo(f"\n{Fore.GREEN}{team.team_name}:{Style.RESET_ALL}")
                    stats_table = []
                    for stat in sorted(team.statistics, key=lambda x: x.type):
                        stats_table.append([stat.type, stat.value])
                    click.echo(tabulate(stats_table, headers=["Statistic", "Value"], tablefmt="simple"))
        
        # 3. Display Lineups
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Team Lineups:{Style.RESET_ALL}")
        
        if not stats.lineups:
            click.echo("No lineup information available for this match.")
        else:
            for team_id, lineup in stats.lineups.items():
                click.echo(f"\n{Fore.GREEN}{lineup.team_name}{Style.RESET_ALL}")
                click.echo(f"Formation: {lineup.formation}")
                click.echo(f"Coach: {lineup.coach}\n")
                
                # Starting XI
                click.echo(f"{Fore.YELLOW}Starting XI:{Style.RESET_ALL}")
                starters_table = []
                for player in sorted(lineup.starters, key=lambda x: (x.position or "", x.grid or "", x.name)):
                    starters_table.append([
                        f"{player.number}" if player.number else "-",
                        player.name,
                        player.position or "-",
                        player.grid or "-"
                    ])
                click.echo(tabulate(starters_table, headers=["#", "Player", "Position", "Grid"], tablefmt="simple"))
                
                # Substitutes
                click.echo(f"\n{Fore.YELLOW}Substitutes:{Style.RESET_ALL}")
                subs_table = []
                for player in sorted(lineup.substitutes, key=lambda x: (x.position or "", x.name)):
                    subs_table.append([
                        f"{player.number}" if player.number else "-",
                        player.name,
                        player.position or "-"
                    ])
                click.echo(tabulate(subs_table, headers=["#", "Player", "Position"], tablefmt="simple"))
        
    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)