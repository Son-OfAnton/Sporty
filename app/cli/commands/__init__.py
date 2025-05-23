"""
CLI commands for the Sporty application.
"""

from app.cli.commands.matches_cmd import matches
from app.cli.commands.live_cmd import live
from app.cli.commands.stats_cmd import fixture_statistics
from app.cli.commands.lineup_cmd import fixture_lineup
from app.cli.commands.squad_cmd import team_squad
from app.cli.commands.team_history_cmd import team_history
from app.cli.commands.team_stats_cmd import team_stats
from app.cli.commands.standings_cmd import standings

# Export all command groups
__all__ = [
    'matches', 
    'live', 
    'fixture_statistics', 
    'fixture_lineup', 
    'team_squad',
    'team_history',
    'team_stats',
    'standings'
]