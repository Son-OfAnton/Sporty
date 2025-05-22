"""
CLI commands for the Sporty application.
"""

from app.cli.commands.matches_cmd import matches
from app.cli.commands.live_cmd import live
from app.cli.commands.stats_cmd import fixture_statistics
from app.cli.commands.lineup_cmd import fixture_lineup
from app.cli.commands.squad_cmd import team_squad

# Export all command groups
__all__ = ['matches', 'live', 'fixture_statistics', 'fixture_lineup', 'team_squad']