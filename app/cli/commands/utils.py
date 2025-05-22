"""
Utility functions for CLI commands.
"""

import click
from colorama import Fore, Style
from tabulate import tabulate

def get_position_color(position):
    """Get color based on player position."""
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

def display_visual_formation(lineup):
    """Display a visual representation of the team formation."""
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
                    position_color = get_position_color(player.position)
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

def display_fixtures(fixtures, format):
    """Helper function to display fixtures."""
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