"""
CLI commands for fetching team season statistics.
"""

import click
import logging
from colorama import Fore, Style, init
from tabulate import tabulate

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService

logger = logging.getLogger(__name__)

@click.command(name="stats")
@click.argument("team_id", type=int)
@click.option(
    "--season", "-s",
    help="Season year (e.g., 2023 for 2023/2024). Defaults to current season.",
    type=int,
    required=False
)
@click.option(
    "--league", "-l",
    help="League ID to filter statistics. If not provided, shows stats across all competitions.",
    type=int,
    required=False
)
@click.option(
    "--include-live/--exclude-live",
    help="Whether to include live matches in the statistics.",
    default=True
)
def team_stats(team_id, season, league, include_live):
    """
    Display aggregated statistics for a team in a specific season.
    
    TEAM_ID: ID of the team to display statistics for
    """
    # Initialize colorama
    init()
    
    try:
        service = FootballService()
        
        # If no season specified, use current season
        if not season:
            season = service.get_current_season()
            
        # First, get team info
        team = service.get_team(team_id)
        if not team:
            click.echo(f"Team with ID {team_id} not found.")
            return
        
        # Get team statistics
        stats = service.get_team_statistics(team_id=team_id, season=season, league_id=league)
        if not stats:
            click.echo(f"No statistics found for {team.name} in season {season}" + 
                      (f" for league {league}" if league else "") + ".")
            return
            
        # Display header
        league_name = stats.league.name if stats.league else "All Competitions"
        click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Season Statistics for {team.name}{Style.RESET_ALL}")
        click.echo(f"Season: {season}")
        click.echo(f"League: {league_name}")
        
        # Display overall stats
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Overall Performance:{Style.RESET_ALL}")
        
        overall_table = [
            ["Matches Played", stats.fixtures.played.total],
            ["Wins", f"{Fore.GREEN}{stats.fixtures.wins.total}{Style.RESET_ALL}"],
            ["Draws", f"{Fore.YELLOW}{stats.fixtures.draws.total}{Style.RESET_ALL}"],
            ["Losses", f"{Fore.RED}{stats.fixtures.losses.total}{Style.RESET_ALL}"],
            ["Win Rate", f"{(stats.fixtures.wins.total / stats.fixtures.played.total * 100):.1f}%" if stats.fixtures.played.total > 0 else "N/A"]
        ]
        click.echo(tabulate(overall_table, tablefmt="simple"))
        
        # Display goals stats
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Goals:{Style.RESET_ALL}")
        
        goals_table = [
            ["Goals Scored", stats.goals.for_goals.total],
            ["Goals Conceded", stats.goals.against.total],
            ["Goal Difference", f"{stats.goals.for_goals.total - stats.goals.against.total:+d}"],
            ["Clean Sheets", stats.clean_sheet.total],
            ["Failed to Score", stats.failed_to_score.total],
            ["Avg Goals Scored", f"{stats.goals.for_goals.average:.2f} per match"],
            ["Avg Goals Conceded", f"{stats.goals.against.average:.2f} per match"]
        ]
        click.echo(tabulate(goals_table, tablefmt="simple"))
        
        # Display scoring distribution
        if stats.goals.for_goals.minute:
            click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Goal Timing:{Style.RESET_ALL}")
            
            minute_ranges = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90", "91-105", "106-120"]
            timing_data = []
            
            for minute_range in minute_ranges:
                goals = stats.goals.for_goals.minute.get(minute_range, {}).get("total", 0)
                percentage = stats.goals.for_goals.minute.get(minute_range, {}).get("percentage", "0%")
                
                # Create a simple bar chart
                if goals > 0:
                    bar = Fore.GREEN + "█" * min(goals, 20) + Style.RESET_ALL
                    timing_data.append([minute_range, goals, percentage, bar])
            
            if timing_data:
                click.echo(tabulate(timing_data, 
                                   headers=["Minute", "Goals", "Percentage", "Distribution"], 
                                   tablefmt="simple"))
        
        # Display home/away split
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Home vs Away Performance:{Style.RESET_ALL}")
        
        home_away_table = [
            ["", "Home", "Away", "Total"],
            ["Played", stats.fixtures.played.home, stats.fixtures.played.away, stats.fixtures.played.total],
            ["Wins", stats.fixtures.wins.home, stats.fixtures.wins.away, stats.fixtures.wins.total],
            ["Draws", stats.fixtures.draws.home, stats.fixtures.draws.away, stats.fixtures.draws.total],
            ["Losses", stats.fixtures.losses.home, stats.fixtures.losses.away, stats.fixtures.losses.total],
            ["Goals For", stats.goals.for_goals.home, stats.goals.for_goals.away, stats.goals.for_goals.total],
            ["Goals Against", stats.goals.against.home, stats.goals.against.away, stats.goals.against.total]
        ]
        click.echo(tabulate(home_away_table, tablefmt="simple"))
        
        # Display lineups if available
        if stats.lineups:
            click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Most Used Formations:{Style.RESET_ALL}")
            
            lineups_table = []
            for lineup in stats.lineups:
                lineups_table.append([
                    lineup.formation,
                    lineup.played,
                    f"{(lineup.played / stats.fixtures.played.total * 100):.1f}%" if stats.fixtures.played.total > 0 else "N/A"
                ])
            
            # Sort by most used
            lineups_table.sort(key=lambda x: x[1], reverse=True)
            
            click.echo(tabulate(lineups_table, 
                               headers=["Formation", "Played", "Percentage"], 
                               tablefmt="simple"))
        
        # Display cards
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Discipline:{Style.RESET_ALL}")
        
        cards_table = [
            ["Yellow Cards", f"{Fore.YELLOW}■{Style.RESET_ALL}", stats.cards.yellow.total],
            ["Red Cards", f"{Fore.RED}■{Style.RESET_ALL}", stats.cards.red.total]
        ]
        click.echo(tabulate(cards_table, tablefmt="simple"))
        
        if stats.cards.yellow.minute or stats.cards.red.minute:
            click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Card Timing:{Style.RESET_ALL}")
            
            card_timing_table = []
            
            # Yellow cards by minute
            for minute_range in minute_ranges:
                yellow_cards = stats.cards.yellow.minute.get(minute_range, {}).get("total", 0)
                red_cards = stats.cards.red.minute.get(minute_range, {}).get("total", 0)
                
                if yellow_cards > 0 or red_cards > 0:
                    yellow_bar = Fore.YELLOW + "■" * min(yellow_cards, 10) + Style.RESET_ALL
                    red_bar = Fore.RED + "■" * min(red_cards, 5) + Style.RESET_ALL
                    card_timing_table.append([minute_range, yellow_cards, yellow_bar, red_cards, red_bar])
            
            if card_timing_table:
                click.echo(tabulate(card_timing_table, 
                                   headers=["Minute", "Yellow", "", "Red", ""], 
                                   tablefmt="simple"))
        
        # Display biggest results
        click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}Biggest Results:{Style.RESET_ALL}")
        
        biggest_table = [
            ["Biggest Win:", f"{stats.biggest.wins.home} (Home)" if stats.biggest.wins.home else "None", 
                          f"{stats.biggest.wins.away} (Away)" if stats.biggest.wins.away else "None"],
            ["Biggest Loss:", f"{stats.biggest.losses.home} (Home)" if stats.biggest.losses.home else "None", 
                            f"{stats.biggest.losses.away} (Away)" if stats.biggest.losses.away else "None"],
            ["Biggest Streak Wins:", stats.biggest.streak.wins],
            ["Biggest Streak Draws:", stats.biggest.streak.draws],
            ["Biggest Streak Losses:", stats.biggest.streak.losses]
        ]
        click.echo(tabulate(biggest_table, tablefmt="simple"))
        
    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        logger.exception("Error in team_stats command")
        click.echo(f"Error: {str(e)}", err=True)