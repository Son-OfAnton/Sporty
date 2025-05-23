"""
Unit tests for the team stats command functionality.

This module contains pytest-based tests for the team_stats function in the
app.cli.commands.team_stats_cmd module.
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from app.cli.commands.team_stats_cmd import team_stats
from app.models.football_data import (
    Team, League, TeamStatistics, FixtureCount, TeamGoalStats, GoalStats, 
    TeamCardStats, CardStats, BiggestScores, BiggestStats, StreakStats, LineupStat
)
from app.services.football_service import FootballService


@pytest.fixture
def mock_service():
    """Create a mock FootballService for testing."""
    with patch('app.cli.commands.team_stats_cmd.FootballService') as MockService:
        service_instance = MagicMock(spec=FootballService)
        MockService.return_value = service_instance
        yield service_instance


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner for testing CLI commands."""
    return CliRunner()


@pytest.fixture
def sample_team():
    """Create a sample team for testing."""
    return Team(
        id=42,
        name="Arsenal FC",
        country="England",
        logo="https://example.com/arsenal.png",
        founded=1886,
        venue_name="Emirates Stadium"
    )


@pytest.fixture
def sample_league():
    """Create a sample league for testing."""
    return League(
        id=39,
        name="Premier League",
        country="England",
        logo="https://example.com/premier-league.png",
        season=2023
    )


@pytest.fixture
def sample_team_stats(sample_team, sample_league):
    """Create sample team statistics for testing."""
    # Create fixture counts
    fixtures = FixtureCount(
        played=FixtureCount(home=19, away=19, total=38),
        wins=FixtureCount(home=14, away=12, total=26),
        draws=FixtureCount(home=3, away=3, total=6),
        losses=FixtureCount(home=2, away=4, total=6)
    )
    
    # Create goal stats
    for_goals = GoalStats(
        home=40, away=35, total=75, average=1.97,
        minute={
            "0-15": {"total": 10, "percentage": "13.3%"},
            "16-30": {"total": 15, "percentage": "20.0%"},
            "31-45": {"total": 12, "percentage": "16.0%"},
            "46-60": {"total": 14, "percentage": "18.7%"},
            "61-75": {"total": 10, "percentage": "13.3%"},
            "76-90": {"total": 14, "percentage": "18.7%"}
        }
    )
    
    against_goals = GoalStats(
        home=15, away=20, total=35, average=0.92,
        minute={
            "0-15": {"total": 5, "percentage": "14.3%"},
            "16-30": {"total": 6, "percentage": "17.1%"},
            "31-45": {"total": 7, "percentage": "20.0%"},
            "46-60": {"total": 7, "percentage": "20.0%"},
            "61-75": {"total": 5, "percentage": "14.3%"},
            "76-90": {"total": 5, "percentage": "14.3%"}
        }
    )
    
    goals = TeamGoalStats(for_goals=for_goals, against=against_goals)
    
    # Create card stats
    yellow_cards = CardStats(
        total=65,
        minute={
            "0-15": {"total": 5, "percentage": "7.7%"},
            "16-30": {"total": 10, "percentage": "15.4%"},
            "31-45": {"total": 12, "percentage": "18.5%"},
            "46-60": {"total": 15, "percentage": "23.1%"},
            "61-75": {"total": 10, "percentage": "15.4%"},
            "76-90": {"total": 13, "percentage": "20.0%"}
        }
    )
    
    red_cards = CardStats(
        total=3,
        minute={
            "0-15": {"total": 0, "percentage": "0.0%"},
            "16-30": {"total": 0, "percentage": "0.0%"},
            "31-45": {"total": 0, "percentage": "0.0%"},
            "46-60": {"total": 1, "percentage": "33.3%"},
            "61-75": {"total": 1, "percentage": "33.3%"},
            "76-90": {"total": 1, "percentage": "33.3%"}
        }
    )
    
    cards = TeamCardStats(yellow=yellow_cards, red=red_cards)
    
    # Create biggest stats
    biggest = BiggestStats(
        wins=BiggestScores(home="4-0", away="3-0"),
        losses=BiggestScores(home="0-2", away="0-3"),
        streak=StreakStats(wins=5, draws=2, losses=2)
    )
    
    # Create lineup stats
    lineups = [
        LineupStat(formation="4-3-3", played=20),
        LineupStat(formation="4-2-3-1", played=16),
        LineupStat(formation="3-4-3", played=2)
    ]
    
    # Create clean sheet and failed to score stats
    clean_sheet = FixtureCount(home=10, away=8, total=18)
    failed_to_score = FixtureCount(home=2, away=4, total=6)
    
    # Create team statistics
    return TeamStatistics(
        team=sample_team,
        league=sample_league,
        form="WDWWL",
        fixtures=fixtures,
        goals=goals,
        clean_sheet=clean_sheet,
        failed_to_score=failed_to_score,
        cards=cards,
        biggest=biggest,
        lineups=lineups
    )


def test_team_stats_success(cli_runner, mock_service, sample_team, sample_team_stats):
    """Test successful retrieval and display of team statistics."""
    # Set up mock return values
    mock_service.get_current_season.return_value = 2023
    mock_service.get_team.return_value = sample_team
    mock_service.get_team_statistics.return_value = sample_team_stats
    
    # Run the CLI command
    result = cli_runner.invoke(team_stats, ['42'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Check that service methods were called correctly
    mock_service.get_team.assert_called_once_with(42)
    mock_service.get_team_statistics.assert_called_once_with(team_id=42, season=2023, league_id=None)
    
    # Check that output contains expected content
    assert sample_team.name in result.output
    assert "Premier League" in result.output
    
    # Check that overall performance section is displayed
    assert "Overall Performance:" in result.output
    assert "Matches Played" in result.output
    assert "38" in result.output  # Total matches
    assert "26" in result.output  # Total wins
    
    # Check goals section
    assert "Goals:" in result.output
    assert "75" in result.output  # Goals scored
    assert "35" in result.output  # Goals conceded
    
    # Check home/away split is displayed
    assert "Home vs Away Performance:" in result.output
    assert "19" in result.output  # Home matches
    
    # Check formations are displayed
    assert "Most Used Formations:" in result.output
    assert "4-3-3" in result.output
    
    # Check discipline section
    assert "Discipline:" in result.output
    assert "65" in result.output  # Yellow cards
    assert "3" in result.output   # Red cards


def test_team_stats_with_season(cli_runner, mock_service, sample_team, sample_team_stats):
    """Test statistics retrieval with a specific season."""
    # Set up mock return values
    mock_service.get_team.return_value = sample_team
    mock_service.get_team_statistics.return_value = sample_team_stats
    
    # Run the CLI command with season option
    result = cli_runner.invoke(team_stats, ['42', '--season', '2022'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Check that the service was called with the correct season
    mock_service.get_team_statistics.assert_called_once_with(team_id=42, season=2022, league_id=None)
    
    # Check that the season is displayed correctly
    assert "Season: 2022" in result.output


def test_team_stats_with_league(cli_runner, mock_service, sample_team, sample_team_stats):
    """Test statistics retrieval with a specific league filter."""
    # Set up mock return values
    mock_service.get_team.return_value = sample_team
    mock_service.get_team_statistics.return_value = sample_team_stats
    
    # Run the CLI command with league option
    result = cli_runner.invoke(team_stats, ['42', '--league', '39'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Check that the service was called with the correct league
    mock_service.get_team_statistics.assert_called_once_with(team_id=42, season=mock_service.get_current_season.return_value, league_id=39)


def test_team_not_found(cli_runner, mock_service):
    """Test handling of a non-existent team."""
    # Set up mock to return None for get_team
    mock_service.get_team.return_value = None
    
    # Run the CLI command
    result = cli_runner.invoke(team_stats, ['99999'])
    
    # Verify the command executed successfully (exits cleanly)
    assert result.exit_code == 0
    
    # Check that error message was displayed
    assert "Team with ID 99999 not found" in result.output
    
    # Verify get_team_statistics was not called
    mock_service.get_team_statistics.assert_not_called()


def test_no_stats_found(cli_runner, mock_service, sample_team):
    """Test handling of a team with no statistics."""
    # Set up mocks
    mock_service.get_team.return_value = sample_team
    mock_service.get_team_statistics.return_value = None
    
    # Run the CLI command
    result = cli_runner.invoke(team_stats, ['42'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Check that team info is displayed
    assert sample_team.name in result.output
    
    # Check that error message was displayed
    assert "No statistics found for" in result.output


def test_include_live_parameter(cli_runner, mock_service, sample_team, sample_team_stats):
    """Test the --include-live parameter."""
    # Set up mock return values
    mock_service.get_team.return_value = sample_team
    mock_service.get_team_statistics.return_value = sample_team_stats
    
    # Run the CLI command with --exclude-live option
    result = cli_runner.invoke(team_stats, ['42', '--exclude-live'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Basic validation - ensure the command ran
    assert sample_team.name in result.output


def test_api_error_handling(cli_runner, mock_service):
    """Test handling of API errors."""
    from app.utils.error_handlers import APIError
    
    # Set up mock to raise an API error
    mock_service.get_team.side_effect = APIError("API Error: Cannot connect to API")
    
    # Run the CLI command
    result = cli_runner.invoke(team_stats, ['42'])
    
    # Verify the command shows the error but exits cleanly
    assert result.exit_code == 0
    assert "API Error:" in result.output


if __name__ == "__main__":
    # Can be run directly with: python -m pytest test_team_stats_command.py -v
    pytest.main(["-v", __file__])