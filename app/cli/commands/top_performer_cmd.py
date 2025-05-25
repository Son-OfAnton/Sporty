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
        league_name = next((l.name for l in leagues if l.id == league), f"League {league}")
        
        # Get the season (using current if not specified)
        if season is None:
            season = service.get_current_season()
        
        click.echo(f"\n{Fore.GREEN}Top Goal Scorers for {league_name} ({season}/{season+1}){Style.RESET_ALL}\n")
        
        # Get the top scorers
        top_scorers = service.get_top_scorers(league_id=league, season=season)
        
        if not top_scorers:
            click.echo(f"{Fore.YELLOW}No top scorer data available for this league and season.{Style.RESET_ALL}")
            return
        
        # Process and display top scorers
        display_top_scorers(top_scorers[:limit], detailed)
        
    except APIError as e:
        click.echo(f"{Fore.RED}API Error: {e.message}{Style.RESET_ALL}", err=True)
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
        headers = ["Rank", "Player", "Age", "Team", "Position", "Nationality", "Games", "Goals", "Assists", "Minutes", "Goals/Game"]
    else:
        headers = ["Rank", "Player", "Team", "Games", "Goals"]
    
    rows = []
    
    for idx, scorer_data in enumerate(top_scorers, 1):
        player = scorer_data.get("player", {})
        statistics = scorer_data.get("statistics", [])[0] if scorer_data.get("statistics") else {}
        
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
        goals_per_game = round(goals_total / games_played, 2) if games_played > 0 else 0
        
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
        click.echo(f"\n{Fore.CYAN}Tip: Use --detailed flag for more player information.{Style.RESET_ALL}")