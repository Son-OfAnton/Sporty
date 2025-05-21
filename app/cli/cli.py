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
logger.info("Logging is configured correctly.")


def main():
    """
    Main entry point for the Sporty CLI.

    This function sets up the command-line interface and handles
    command execution.
    """
    # Check if the script is being run directly
    if __name__ == "__main__":
        cli()
    else:
        # If imported, set up error handling
        setup_error_handling()


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

            status_text = f"{status_color}{fixture.status.short}{Style.RESET_ALL}"

            # Add elapsed time for live matches
            if hasattr(fixture, 'status') and hasattr(fixture.status, 'elapsed') and fixture.status.elapsed:
                status_text += f" {fixture.status.elapsed}'"

            # Format score based on status
            if fixture.status.short == "NS":
                # Match not started
                score_text = f"{Fore.WHITE}vs{Style.RESET_ALL}"
            else:
                # Match in progress or finished
                home_goals = fixture.home_team.goals if fixture.home_team.goals is not None else 0
                away_goals = fixture.away_team.goals if fixture.away_team.goals is not None else 0
                score_text = f"{Fore.WHITE}{Style.BRIGHT}{home_goals} - {away_goals}{Style.RESET_ALL}"

            # Format date/time for not started matches
            date_text = ""
            if fixture.status.short == "NS":
                date_text = fixture.date.strftime("%H:%M")

            table_data.append([
                status_text,
                f"{fixture.home_team.name} {Fore.WHITE}vs{Style.RESET_ALL} {fixture.away_team.name}",
                score_text,
                date_text
            ])

        # Display table with the appropriate headers
        headers = ["Status", "Match", "Score", "Time"]
        if all(row[3] == "" for row in table_data):
            # If no time column is used, don't show it
            table_data = [row[0:3] for row in table_data]
            headers = headers[0:3]

        click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

    elif format == "detailed":
        # Detailed view for each fixture
        for fixture in fixtures:
            click.echo("\n" + "─" * 60)

            # Match header
            click.echo(
                f"{Fore.BLUE}{Style.BRIGHT}{fixture.home_team.name} vs {fixture.away_team.name}{Style.RESET_ALL}")

            # Status
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

            status_text = f"{status_color}{fixture.status.long}{Style.RESET_ALL}"
            if hasattr(fixture, 'status') and hasattr(fixture.status, 'elapsed') and fixture.status.elapsed:
                status_text += f" ({fixture.status.elapsed}')"
            click.echo(f"Status: {status_text}")

            # Date and time
            date_str = fixture.date.strftime("%Y-%m-%d %H:%M")
            click.echo(f"Date: {date_str}")

            # Venue
            if fixture.venue:
                click.echo(f"Venue: {fixture.venue}")

            # Referee
            if fixture.referee:
                click.echo(f"Referee: {fixture.referee}")

            # Score
            if fixture.status.short != "NS":
                home_goals = fixture.home_team.goals if fixture.home_team.goals is not None else 0
                away_goals = fixture.away_team.goals if fixture.away_team.goals is not None else 0
                click.echo(
                    f"Score: {Fore.WHITE}{Style.BRIGHT}{home_goals}-{away_goals}{Style.RESET_ALL}")

            # Teams
            click.echo(
                f"Home: {Fore.CYAN}{fixture.home_team.name}{Style.RESET_ALL}")
            click.echo(
                f"Away: {Fore.CYAN}{fixture.away_team.name}{Style.RESET_ALL}")

            # Additional score information if available
            if fixture.score and fixture.score.halftime and fixture.status.short != "NS":
                ht = fixture.score.halftime
                ht_home = ht.get("home", 0)
                ht_away = ht.get("away", 0)
                click.echo(f"Halftime: {ht_home}-{ht_away}")

            if fixture.score and fixture.score.fulltime and fixture.status.short == "FT":
                ft = fixture.score.fulltime
                ft_home = ft.get("home", 0)
                ft_away = ft.get("away", 0)
                click.echo(f"Fulltime: {ft_home}-{ft_away}")

            if fixture.score and fixture.score.extratime and any(v is not None for v in fixture.score.extratime.values()):
                et = fixture.score.extratime
                et_home = et.get("home", 0)
                et_away = et.get("away", 0)
                click.echo(f"Extra time: {et_home}-{et_away}")

            if fixture.score and fixture.score.penalty and any(v is not None for v in fixture.score.penalty.values()):
                pen = fixture.score.penalty
                pen_home = pen.get("home", 0)
                pen_away = pen.get("away", 0)
                click.echo(f"Penalties: {pen_home}-{pen_away}")


@click.group()
def scores():
    """Get match statistics."""
    pass


@scores.command(name="stats")
@click.argument("fixture_id", type=int)
def fixture_statistics(fixture_id):
    """
    Display detailed statistics for a specific match.
    
    Shows goals, cards, substitutions, lineups, and other statistics.
    Requires the fixture ID as an argument.
    """
    from app.services.football_service import FootballService
    from app.utils.error_handlers import APIError
    from tabulate import tabulate
    from colorama import Fore, Style, init
    
    # Initialize colorama
    init()
    
    try:
        service = FootballService()
        
        click.echo(f"Fetching statistics for fixture ID: {fixture_id}")
        
        # Get fixture information first
        fixture = service.get_fixtures_by_id(fixture_id=fixture_id)
        if not fixture:
            click.echo(f"No fixture found with ID {fixture_id}.")
            return
            
        # Display basic fixture information
        click.echo(f"\n{Fore.BLUE}{Style.BRIGHT}Match: {fixture.home_team.name} vs {fixture.away_team.name}{Style.RESET_ALL}")
        click.echo(f"Date: {fixture.date.strftime('%Y-%m-%d %H:%M')}")
        if fixture.score and fixture.home_team.goals is not None and fixture.away_team.goals is not None:
            click.echo(f"Score: {Fore.WHITE}{Style.BRIGHT}{fixture.home_team.goals}-{fixture.away_team.goals}{Style.RESET_ALL}")
        
        # Get match statistics
        stats = service.get_match_statistics(fixture_id)
        
        # Display events (goals, cards, substitutions)
        if stats.events:
            click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Match Events:{Style.RESET_ALL}")
            
            # Organize events by type
            goals = [e for e in stats.events if e.type == "Goal"]
            cards = [e for e in stats.events if e.type == "Card"]
            substitutions = [e for e in stats.events if e.type == "subst"]
            
            # Display goals
            if goals:
                click.echo(f"\n{Fore.YELLOW}Goals:{Style.RESET_ALL}")
                goals_table = []
                for goal in sorted(goals, key=lambda x: x.time):
                    team_color = Fore.CYAN if goal.team_id == fixture.home_team.id else Fore.MAGENTA
                    assist_text = f" (Assist: {goal.assist_player_name})" if goal.assist_player_name else ""
                    goal_type = f" - {goal.detail}" if goal.detail != "Normal Goal" else ""
                    
                    goals_table.append([
                        f"{goal.time}'",
                        f"{team_color}{goal.team_name}{Style.RESET_ALL}",
                        f"{goal.player_name}{goal_type}{assist_text}"
                    ])
                
                click.echo(tabulate(goals_table, headers=["Time", "Team", "Scorer"], tablefmt="simple"))
            
            # Display cards
            if cards:
                click.echo(f"\n{Fore.YELLOW}Cards:{Style.RESET_ALL}")
                cards_table = []
                for card in sorted(cards, key=lambda x: x.time):
                    team_color = Fore.CYAN if card.team_id == fixture.home_team.id else Fore.MAGENTA
                    card_color = Fore.YELLOW if card.detail == "Yellow Card" else Fore.RED
                    
                    cards_table.append([
                        f"{card.time}'",
                        f"{team_color}{card.team_name}{Style.RESET_ALL}",
                        f"{card_color}{card.detail}{Style.RESET_ALL}",
                        f"{card.player_name}"
                    ])
                
                click.echo(tabulate(cards_table, headers=["Time", "Team", "Card", "Player"], tablefmt="simple"))
            
            # Display substitutions
            if substitutions:
                click.echo(f"\n{Fore.YELLOW}Substitutions:{Style.RESET_ALL}")
                subs_table = []
                for sub in sorted(substitutions, key=lambda x: x.time):
                    team_color = Fore.CYAN if sub.team_id == fixture.home_team.id else Fore.MAGENTA
                    
                    subs_table.append([
                        f"{sub.time}'",
                        f"{team_color}{sub.team_name}{Style.RESET_ALL}",
                        f"{Fore.RED}◀ {sub.detail}{Style.RESET_ALL}",
                        f"{Fore.GREEN}▶ {sub.player_name}{Style.RESET_ALL}"
                    ])
                
                click.echo(tabulate(subs_table, headers=["Time", "Team", "Out", "In"], tablefmt="simple"))
        
        # Display team statistics
        if stats.team_statistics:
            click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Match Statistics:{Style.RESET_ALL}")
            
            # Create a table with both teams
            stats_table = []
            
            # Get both team statistics
            home_stats = stats.team_statistics.get(fixture.home_team.id)
            away_stats = stats.team_statistics.get(fixture.away_team.id)
            
            if home_stats and away_stats:
                # Find common statistics between both teams
                home_stat_types = {stat.type for stat in home_stats.statistics}
                away_stat_types = {stat.type for stat in away_stats.statistics}
                common_stat_types = sorted(home_stat_types.intersection(away_stat_types))
                
                for stat_type in common_stat_types:
                    home_value = next((stat.value for stat in home_stats.statistics if stat.type == stat_type), "-")
                    away_value = next((stat.value for stat in away_stats.statistics if stat.type == stat_type), "-")
                    
                    stats_table.append([
                        f"{Fore.CYAN}{home_value}{Style.RESET_ALL}",
                        stat_type,
                        f"{Fore.MAGENTA}{away_value}{Style.RESET_ALL}"
                    ])
                
                # Create headers with team names
                headers = [
                    f"{Fore.CYAN}{fixture.home_team.name}{Style.RESET_ALL}",
                    "Statistic",
                    f"{Fore.MAGENTA}{fixture.away_team.name}{Style.RESET_ALL}"
                ]
                
                click.echo(tabulate(stats_table, headers=headers, tablefmt="simple"))
        
        # Display lineups
        if stats.lineups:
            click.echo(f"\n{Fore.GREEN}{Style.BRIGHT}Lineups:{Style.RESET_ALL}")
            
            # Get both team lineups
            home_lineup = stats.lineups.get(fixture.home_team.id)
            away_lineup = stats.lineups.get(fixture.away_team.id)
            
            if home_lineup:
                click.echo(f"\n{Fore.CYAN}{home_lineup.team_name} ({home_lineup.formation}){Style.RESET_ALL}")
                click.echo(f"Coach: {home_lineup.coach}")
                
                # Starting XI
                click.echo(f"\n{Fore.YELLOW}Starting XI:{Style.RESET_ALL}")
                starters_table = []
                for player in sorted(home_lineup.starters, key=lambda x: (x.position or "", x.name)):
                    starters_table.append([
                        f"{player.number}" if player.number else "-",
                        player.name,
                        player.position if player.position else "-"
                    ])
                
                click.echo(tabulate(starters_table, headers=["#", "Player", "Position"], tablefmt="simple"))
                
                # Substitutes
                click.echo(f"\n{Fore.YELLOW}Substitutes:{Style.RESET_ALL}")
                subs_table = []
                for player in sorted(home_lineup.substitutes, key=lambda x: (x.position or "", x.name)):
                    subs_table.append([
                        f"{player.number}" if player.number else "-",
                        player.name,
                        player.position if player.position else "-"
                    ])
                
                click.echo(tabulate(subs_table, headers=["#", "Player", "Position"], tablefmt="simple"))
            
            if away_lineup:
                click.echo(f"\n{Fore.MAGENTA}{away_lineup.team_name} ({away_lineup.formation}){Style.RESET_ALL}")
                click.echo(f"Coach: {away_lineup.coach}")
                
                # Starting XI
                click.echo(f"\n{Fore.YELLOW}Starting XI:{Style.RESET_ALL}")
                starters_table = []
                for player in sorted(away_lineup.starters, key=lambda x: (x.position or "", x.name)):
                    starters_table.append([
                        f"{player.number}" if player.number else "-",
                        player.name,
                        player.position if player.position else "-"
                    ])
                
                click.echo(tabulate(starters_table, headers=["#", "Player", "Position"], tablefmt="simple"))
                
                # Substitutes
                click.echo(f"\n{Fore.YELLOW}Substitutes:{Style.RESET_ALL}")
                subs_table = []
                for player in sorted(away_lineup.substitutes, key=lambda x: (x.position or "", x.name)):
                    subs_table.append([
                        f"{player.number}" if player.number else "-",
                        player.name,
                        player.position if player.position else "-"
                    ])
                
                click.echo(tabulate(subs_table, headers=["#", "Player", "Position"], tablefmt="simple"))
            
    except APIError as e:
        click.echo(f"API Error: {e.message}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@scores.command(name="lineup")
@click.argument("fixture_id", type=int)
@click.option(
    "--visual/--no-visual", 
    default=True,
    help="Show visual formation representation."
)
def fixture_lineup(fixture_id, visual):
    """
    Display the lineup and formation for a specific match.
    
    Shows the complete starting XI, formation, substitutes, and coach information
    for both teams in a match.
    
    Requires the fixture ID as an argument.
    """
    from app.services.football_service import FootballService
    from app.utils.error_handlers import APIError
    from tabulate import tabulate
    from colorama import Fore, Style, init
    
    # Initialize colorama
    init()
    
    try:
        service = FootballService()
        
        click.echo(f"Fetching lineup information for fixture ID: {fixture_id}")
        
        # Get fixture information first
        fixture = service.get_fixtures_by_id(fixture_id=fixture_id)
        if not fixture:
            click.echo(f"No fixture found with ID {fixture_id}.")
            return
            
        # Get lineups
        lineups = service.get_fixture_lineups(fixture_id)
        
        if not lineups:
            click.echo("No lineup information available for this match.")
            return
            
        # Display match header
        click.echo(f"\n{Fore.BLUE}{Style.BRIGHT}Match: {fixture.home_team.name} vs {fixture.away_team.name}{Style.RESET_ALL}")
        click.echo(f"Date: {fixture.date.strftime('%Y-%m-%d %H:%M')}")
        
        # Get both team lineups
        home_lineup = lineups.get(fixture.home_team.id)
        away_lineup = lineups.get(fixture.away_team.id)
        
        # Display home team lineup
        if home_lineup:
            click.echo(f"\n{Fore.CYAN}{Style.BRIGHT}{home_lineup.team_name}{Style.RESET_ALL}")
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