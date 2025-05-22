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


def main():
    """
    Main entry point for the Sporty CLI.

    This function sets up the command-line interface and handles
    command execution.
    """
    # Set up error handling
    setup_error_handling()
    # Call the CLI directly
    cli()


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

            # Prepare the status display with elapsed time if applicable
            status_display = fixture.status.short
            if fixture.status.elapsed is not None and fixture.status.short not in ["NS", "FT", "PST", "CANC", "ABD", "SUSP"]:
                status_display = f"{status_display} {fixture.status.elapsed}'"

            # Format match time
            match_time = fixture.date.strftime("%H:%M")

            # Add row to table data
            table_data.append([
                match_time,
                f"{status_color}{status_display}{Style.RESET_ALL}",
                Fore.GREEN + fixture.home_team.name +
                Style.RESET_ALL if fixture.home_team.winner else fixture.home_team.name,
                fixture.score_display,
                Fore.GREEN + fixture.away_team.name +
                Style.RESET_ALL if fixture.away_team.winner else fixture.away_team.name
            ])

        # Display table
        headers = ["Time", "Status", "Home Team", "Score", "Away Team"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
    else:
        # Detailed format
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

            # Format date and time
            match_datetime = fixture.date.strftime("%Y-%m-%d %H:%M")

            # Venue and referee info if available
            venue_info = f" at {fixture.venue}" if fixture.venue else ""
            referee_info = f" (Referee: {fixture.referee})" if fixture.referee else ""

            # Status display
            status_display = fixture.status.short
            if fixture.status.elapsed is not None and fixture.status.short not in ["NS", "FT", "PST", "CANC", "ABD", "SUSP"]:
                status_display = f"{status_display} {fixture.status.elapsed}'"

            # Print header with match info
            click.echo(f"\n{Fore.YELLOW}{Style.BRIGHT}{match_datetime}{Style.RESET_ALL}")
            click.echo(
                f"{fixture.home_team.name} vs {fixture.away_team.name}{venue_info}{referee_info}")
            click.echo(
                f"Status: {status_color}{fixture.status.long} ({status_display}){Style.RESET_ALL}")

            # Score information
            click.echo(f"\nScore: {Fore.BRIGHT}{fixture.score_display}{Style.RESET_ALL}")

            # Additional score details if available
            if fixture.score:
                if fixture.score.halftime and fixture.score.halftime.get("home") is not None:
                    home_ht = fixture.score.halftime.get("home", 0)
                    away_ht = fixture.score.halftime.get("away", 0)
                    click.echo(f"Halftime: {home_ht}-{away_ht}")

                if fixture.score.fulltime and fixture.score.fulltime.get("home") is not None:
                    home_ft = fixture.score.fulltime.get("home", 0)
                    away_ft = fixture.score.fulltime.get("away", 0)
                    click.echo(f"Fulltime: {home_ft}-{away_ft}")

                if fixture.score.extratime and fixture.score.extratime.get("home") is not None:
                    home_et = fixture.score.extratime.get("home", 0)
                    away_et = fixture.score.extratime.get("away", 0)
                    click.echo(f"Extra Time: {home_et}-{away_et}")

                if fixture.score.penalty and fixture.score.penalty.get("home") is not None:
                    home_pen = fixture.score.penalty.get("home", 0)
                    away_pen = fixture.score.penalty.get("away", 0)
                    click.echo(f"Penalties: {home_pen}-{away_pen}")

            # Add a separator line
            click.echo(f"{'-'*50}")


@cli.command(name="stats")
@click.argument("fixture_id", type=int)
def fixture_statistics(fixture_id):
    """
    Display detailed statistics for a specific fixture.
    
    FIXTURE_ID: ID of the fixture to display statistics for
    """
    from app.services.football_service import FootballService
    from app.utils.error_handlers import APIError
    from tabulate import tabulate
    from colorama import Fore, Style, init
    
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


@cli.command(name="lineup")
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
    from app.services.football_service import FootballService
    from app.utils.error_handlers import APIError
    from tabulate import tabulate
    from colorama import Fore, Style, init
    
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
                _display_visual_formation(home_lineup)
            
            # Starting XI
            click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Starting XI:{Style.RESET_ALL}")
            starters_table = []
            for player in sorted(home_lineup.starters, key=lambda x: (x.position or "", x.name)):
                # Colorize by position
                position_color = _get_position_color(player.position)
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
                position_color = _get_position_color(player.position)
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
                _display_visual_formation(away_lineup)
            
            # Starting XI
            click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Starting XI:{Style.RESET_ALL}")
            starters_table = []
            for player in sorted(away_lineup.starters, key=lambda x: (x.position or "", x.name)):
                # Colorize by position
                position_color = _get_position_color(player.position)
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
                position_color = _get_position_color(player.position)
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

def _get_position_color(position):
    """Get color based on player position."""
    from colorama import Fore
    
    if not position:
        return ""
        
    position = position.lower()
    
    if "goalkeeper" in position or "gk" == position:
        return Fore.YELLOW
    elif "defender" in position or position in ["cb", "rb", "lb", "rwb", "lwb"]:
        return Fore.BLUE
    elif "midfielder" in position or position in ["cm", "cdm", "cam", "rm", "lm"]:
        return Fore.GREEN
    elif "forward" in position or "striker" in position or position in ["cf", "st", "rw", "lw"]:
        return Fore.RED
    else:
        return ""

def _display_visual_formation(lineup):
    """Display a visual representation of the team formation."""
    from colorama import Fore, Style
    
    if not lineup.formation:
        return
        
    try:
        # Parse formation
        formation_parts = lineup.formation.split("-")
        if not formation_parts:
            return
            
        # Create a mapping of positions to players
        position_players = {}
        for player in lineup.starters:
            if player.grid:
                position_players[player.grid] = player
        
        # Defense line
        positions = len(formation_parts)
        width = 60  # Terminal width for the formation display
        
        # Create the pitch representation
        lines = []
        
        # Add goalkeeper
        gk_line = " " * (width // 2 - 5) + f"{Fore.YELLOW}(GK){Style.RESET_ALL}" + " " * (width // 2 - 5)
        lines.append(gk_line)
        
        # Find goalkeeper
        goalkeeper = next((p for p in lineup.starters if p.position and ("goalkeeper" in p.position.lower() or "gk" == p.position.lower())), None)
        if goalkeeper:
            gk_name = goalkeeper.name if len(goalkeeper.name) <= 20 else goalkeeper.name[:18] + ".."
            gk_line = " " * (width // 2 - len(gk_name) // 2) + f"{Fore.YELLOW}{gk_name}{Style.RESET_ALL}" + " " * (width // 2 - len(gk_name) // 2)
            lines.append(gk_line)
            
        lines.append("")  # Space
        
        # Add remaining lines based on formation
        player_lines = []
        
        # For each line in the formation
        for i, count in enumerate(formation_parts):
            count = int(count)
            line = []
            
            # Position name
            position_name = ""
            if i == 0:
                position_name = f"{Fore.BLUE}Defenders{Style.RESET_ALL}"
            elif i == len(formation_parts) - 1:
                position_name = f"{Fore.RED}Forwards{Style.RESET_ALL}"
            else:
                position_name = f"{Fore.GREEN}Midfielders{Style.RESET_ALL}"
                
            # Center the position name
            position_line = " " * (width // 2 - len(position_name) // 2 - 10) + position_name + " " * (width // 2 - len(position_name) // 2 - 10)
            player_lines.append(position_line)
            
            # Space
            player_lines.append("")
                
            # Find players for this line
            players_in_line = []
            for player in lineup.starters:
                if not player.position:
                    continue
                    
                position = player.position.lower()
                
                # Check if player belongs to this formation line
                if i == 0 and ("defender" in position or position in ["cb", "rb", "lb", "rwb", "lwb"]):
                    players_in_line.append(player)
                elif i == len(formation_parts) - 1 and ("forward" in position or "striker" in position or position in ["cf", "st", "rw", "lw"]):
                    players_in_line.append(player)
                elif i > 0 and i < len(formation_parts) - 1 and ("midfielder" in position or position in ["cm", "cdm", "cam", "rm", "lm"]):
                    players_in_line.append(player)
            
            # Sort players by grid position if available, otherwise by name
            players_in_line.sort(key=lambda x: x.grid if x.grid else x.name)
            
            # Limit to formation count
            players_in_line = players_in_line[:count]
            
            # Add players to the line
            if players_in_line:
                segment_width = width // (len(players_in_line) + 1)
                player_slots = []
                
                for j, player in enumerate(players_in_line):
                    position_color = _get_position_color(player.position)
                    number = f"({player.number})" if player.number else ""
                    player_name = player.name if len(player.name) <= 15 else player.name[:13] + ".."
                    player_text = f"{position_color}{player_name} {number}{Style.RESET_ALL}"
                    
                    # Center in the slot
                    slot = " " * (segment_width // 2 - len(player_name) // 2) + player_text + " " * (segment_width // 2 - len(player_name) // 2)
                    player_slots.append(slot)
                    
                player_lines.append("".join(player_slots))
                
            player_lines.append("")  # Space
            
        # Add the player lines
        lines.extend(player_lines)
        
        # Output the formation
        for line in lines:
            click.echo(line)
            
    except Exception as e:
        # If any error occurs, just skip the visual representation
        click.echo(f"Could not display visual formation: {e}")
        return


if __name__ == '__main__':
    main()