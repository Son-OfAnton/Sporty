"""
CLI commands for handling live match data.
"""

import click
import logging
from colorama import init

logger = logging.getLogger(__name__)

@click.group()
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
    # Import match_scores here to avoid circular imports
    from app.cli.commands.matches_cmd import match_scores
    ctx.forward(match_scores, live=True)