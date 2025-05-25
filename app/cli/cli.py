#!/usr/bin/env python3
"""
Sporty CLI - Main entry point for the Sporty command-line interface.
"""

import click
import logging
import sys
import os

from app.utils.error_handlers import setup_error_handling
from app.cli.commands import (
    matches, 
    live, 
    fixture_statistics, 
    fixture_lineup, 
    team_squad, 
    team_history, 
    team_stats,
)
# Import our new standings command
from app.cli.commands.standings_cmd import standings
from app.cli.commands.top_performer_cmd import top_performer

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


# Add command groups
cli.add_command(matches)
cli.add_command(live)
cli.add_command(fixture_statistics, name="stats")
cli.add_command(fixture_lineup, name="lineup")
cli.add_command(team_squad, name="squad")
cli.add_command(team_history, name="history")
cli.add_command(team_stats, name="team-stats")
cli.add_command(standings, name="standings")
cli.add_command(top_performer, name="top-performer")


if __name__ == '__main__':
    main()