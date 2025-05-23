"""
CLI commands for handling league standings data.
"""

import click
import logging
import datetime
import json
from typing import Dict, Any, Optional, List
from tabulate import tabulate
from colorama import Fore, Style, init

from app.utils.error_handlers import APIError
from app.services.football_service import FootballService
from app.models.football_data import TeamStanding

logger = logging.getLogger(__name__)

# Available sort criteria and directions
SORT_CRITERIA = ['points', 'goals_for', 'goals_against', 'goal_diff', 'played', 'wins', 'draws', 'losses']
SORT_DIRECTIONS = ['asc', 'desc']

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
@click.option(
    "--filter", "-f",
    help="Filter standings by home/away/all matches.",
    type=click.Choice(["all", "home", "away"]),
    default="all"
)
@click.option(
    "--sort-by", "-sb",
    help="Sort standings by a specific criterion.",
    type=click.Choice(SORT_CRITERIA),
    default="points"
)
@click.option(
    "--sort-dir", "-sd",
    help="Sort direction (ascending or descending).",
    type=click.Choice(SORT_DIRECTIONS),
    default="desc"
)
@click.option(
    "--debug-api", "-d",
    is_flag=True,
    help="Print API response structure for debugging.",
    hidden=True
)
def league_standings(league, name, country, season, filter, sort_by, sort_dir, debug_api):
    """
    Display current league standings for a specific league and season.

    Displays team rankings, points, wins, draws, losses, and goal statistics.
    
    Specify league either by ID or by name.
    
    Filter option allows you to see standings based on only home matches,
    only away matches, or all matches (default).
    
    Sort options let you order the table by different criteria like goals scored
    or goals conceded, in either ascending or descending order.
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
            
        filter_text = ""
        if filter == "home":
            filter_text = " (HOME MATCHES ONLY)"
        elif filter == "away":
            filter_text = " (AWAY MATCHES ONLY)"
            
        # Add sorting information to the output
        sort_text = f" - Sorted by {sort_by.replace('_', ' ')} ({sort_dir})"
            
        click.echo(f"Fetching standings for league ID {league} in season {season}{filter_text}{sort_text}...\n")
        
        # Get standings
        standings_list = service.get_standings(league_id=league, season=season)
        
        if not standings_list:
            click.echo("No standings found for the specified league and season.")
            return
            
        # Get the raw API response to access home and away data
        raw_response = service.client._make_request("standings", {"league": league, "season": season})
        
        # Debug API response if requested
        if debug_api and raw_response:
            click.echo("\n--- DEBUG: API Response Structure ---")
            if "response" in raw_response and raw_response["response"]:
                first_league = raw_response["response"][0]["league"]
                standings_array = first_league["standings"]
                
                # If standings is a list of lists, take the first one
                if isinstance(standings_array[0], list):
                    standings_array = standings_array[0]
                    
                first_team = standings_array[0]
                
                click.echo(f"First team in standings: {first_team['team']['name']}")
                
                # Show home/away data structure
                if "home" in first_team:
                    click.echo("\nHome data structure:")
                    click.echo(json.dumps(first_team["home"], indent=2))
                    
                if "away" in first_team:
                    click.echo("\nAway data structure:")
                    click.echo(json.dumps(first_team["away"], indent=2))
            
            click.echo("--- END DEBUG ---\n")
        
        standings_data = raw_response.get('response', [])
        
        # Format data for tabulate
        headers = ["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]
        table_data = []
        
        # If we have raw data and a valid filter, use it to create a filtered view
        if standings_data and filter in ["home", "away"]:
            # Extract the standings array from the first league
            try:
                league_data = standings_data[0].get("league", {})
                standings_array = league_data.get("standings", [])
                
                # Handle nested standings (some leagues have multiple groups)
                if standings_array and isinstance(standings_array[0], list):
                    standings_array = standings_array[0]
                
                # Process and display the filtered standings
                filtered_standings_rows = _process_filtered_standings(
                    standings_array, filter, debug_api, sort_by, sort_dir
                )
                
                if not filtered_standings_rows:
                    click.echo(f"Unable to get {filter} standings data for this league.")
                    # Fall back to the original standings
                    _display_standard_standings(standings_list, sort_by, sort_dir)
                else:
                    # Display the filtered standings
                    click.echo(tabulate(filtered_standings_rows, headers=headers, tablefmt="pretty"))
                
            except (IndexError, KeyError) as e:
                logger.error(f"Error processing filtered standings: {e}")
                # Fall back to standard standings display
                click.echo(f"Error processing {filter} standings. Displaying standard standings instead.")
                _display_standard_standings(standings_list, sort_by, sort_dir)
        else:
            # Display standard standings
            _display_standard_standings(standings_list, sort_by, sort_dir)
        
        # Display current date and time info
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"\n{Fore.BLUE}Standings as of: {current_time}{Style.RESET_ALL}")
        if filter != "all":
            click.echo(f"{Fore.YELLOW}Note: Standings are based on {filter} matches only.{Style.RESET_ALL}")
            
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


def _display_standard_standings(standings_list: List[TeamStanding], sort_by: str = "points", sort_dir: str = "desc") -> None:
    """
    Display standard standings table with custom sorting.
    
    Args:
        standings_list: List of TeamStanding objects
        sort_by: Field to sort by (points, goals_for, goals_against, etc.)
        sort_dir: Sort direction (asc or desc)
    """
    headers = ["Pos", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]
    table_data = []
    
    # Convert TeamStanding objects to dictionaries for easier sorting
    standings_dicts = []
    for standing in standings_list:
        standings_dicts.append({
            "rank": standing.rank,
            "team_name": standing.team.name,
            "played": standing.played,
            "wins": standing.win,
            "draws": standing.draw,
            "losses": standing.lose,
            "goals_for": standing.goals_for,
            "goals_against": standing.goals_against,
            "goal_diff": standing.goal_difference,
            "points": standing.points,
            "original_standing": standing
        })
    
    # Map sort_by parameter to actual dictionary key
    sort_key_mapping = {
        'points': 'points',
        'goals_for': 'goals_for',
        'goals_against': 'goals_against',
        'goal_diff': 'goal_diff',
        'played': 'played',
        'wins': 'wins',
        'draws': 'draws',
        'losses': 'losses'
    }
    
    # Get the actual sort key
    sort_key = sort_key_mapping.get(sort_by, 'points')
    
    # Sort the standings
    reverse_sort = (sort_dir == "desc")
    sorted_standings = sorted(standings_dicts, key=lambda x: x[sort_key], reverse=reverse_sort)
    
    # Create the table data
    for i, standing_dict in enumerate(sorted_standings):
        # Calculate goal difference
        gd = standing_dict["goal_diff"]
        gd_str = f"{gd:+d}" if gd != 0 else "0"
        
        # Add row to table
        row = [
            # Position with color based on new ranking after sort
            _format_position(i + 1),
            standing_dict["team_name"],
            standing_dict["played"],
            standing_dict["wins"],
            standing_dict["draws"],
            standing_dict["losses"],
            standing_dict["goals_for"],
            standing_dict["goals_against"],
            gd_str,
            f"{Fore.CYAN}{Style.BRIGHT}{standing_dict['points']}{Style.RESET_ALL}"
        ]
        
        table_data.append(row)
    
    # Display the table
    click.echo(tabulate(table_data, headers=headers, tablefmt="pretty"))


def _process_filtered_standings(
    standings_array: List[Dict[str, Any]], 
    filter_type: str, 
    debug: bool = False,
    sort_by: str = "points",
    sort_dir: str = "desc"
) -> List[List[Any]]:
    """
    Process standings array and return rows for display, filtered by home or away.
    
    Args:
        standings_array: List of standings data dictionaries from the API
        filter_type: Either "home" or "away"
        debug: Whether to print debug information
        sort_by: Field to sort by (points, goals_for, goals_against, etc.)
        sort_dir: Sort direction (asc or desc)
        
    Returns:
        List of rows ready for tabulate display
    """
    if not standings_array:
        return []
    
    # Process standings based on filter type
    table_rows = []
    
    # Debug first item to understand structure
    if debug and standings_array:
        first_item = standings_array[0]
        click.echo(f"\nTeam: {first_item['team']['name']}")
        click.echo(f"All data available for this team: {list(first_item.keys())}")
        if filter_type in first_item:
            click.echo(f"\n{filter_type.upper()} data for first team:")
            for key, value in first_item[filter_type].items():
                click.echo(f"  {key}: {value}")
    
    # Process each team's filtered data
    processed_standings = []
    for standing_data in standings_array:
        # Get team data
        team_data = standing_data.get("team", {})
        
        # Get filtered statistics
        filtered_stats = standing_data.get(filter_type, {})
        
        if not filtered_stats:
            continue
        
        # Get stats directly from the filtered data
        wins = filtered_stats.get("win", 0)
        draws = filtered_stats.get("draw", 0)
        losses = filtered_stats.get("lose", 0)
        
        # Calculate points using the formula: points = wins * 3 + draws
        points = (wins * 3) + draws
        
        # Get goals data
        goals_data = filtered_stats.get("goals", {})
        
        # Calculate goal difference
        goals_for = goals_data.get("for", 0)
        goals_against = goals_data.get("against", 0)
        goal_diff = goals_for - goals_against
        
        # Create a processed standing object
        processed_standing = {
            "team_name": team_data.get("name", "Unknown"),
            "team_id": team_data.get("id", 0),
            "played": filtered_stats.get("played", 0),
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_diff": goal_diff,
            "points": points
        }
        
        processed_standings.append(processed_standing)
    
    # Map sort_by parameter to actual dictionary key
    sort_key_mapping = {
        'points': 'points',
        'goals_for': 'goals_for',
        'goals_against': 'goals_against',
        'goal_diff': 'goal_diff',
        'played': 'played',
        'wins': 'wins',
        'draws': 'draws',
        'losses': 'losses'
    }
    
    # Get the actual sort key
    sort_key = sort_key_mapping.get(sort_by, 'points')
    
    # Sort standings by the chosen criterion
    reversed_sort = (sort_dir == "desc")
    sorted_standings = sorted(
        processed_standings, 
        key=lambda x: x[sort_key],
        reverse=reversed_sort
    )
    
    # Build the table rows
    for i, standing in enumerate(sorted_standings):
        # Format goal difference string
        gd_str = f"{standing['goal_diff']:+d}" if standing['goal_diff'] != 0 else "0"
        
        # Format row
        row = [
            _format_position(i + 1),  # New position based on sort order
            standing["team_name"],
            standing["played"],
            standing["wins"],
            standing["draws"],
            standing["losses"],
            standing["goals_for"],
            standing["goals_against"],
            gd_str,
            f"{Fore.CYAN}{Style.BRIGHT}{standing['points']}{Style.RESET_ALL}"  # Calculated points
        ]
        
        table_rows.append(row)
    
    return table_rows