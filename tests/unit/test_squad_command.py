"""
Unit tests for the squad command functionality.

This module contains pytest-based tests for the team_squad function in the
app.cli.commands.squad_cmd module.
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from app.cli.commands.squad_cmd import team_squad
from app.models.football_data import Team, Player
from app.services.football_service import FootballService


@pytest.fixture
def mock_service():
    """Create a mock FootballService for testing."""
    with patch('app.cli.commands.squad_cmd.FootballService') as MockService:
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
def sample_players():
    """Create a sample list of players for testing."""
    return [
        # Goalkeepers
        Player(id=1, name="Aaron Ramsdale", age=25, nationality="England", position="Goalkeeper", photo=None),
        Player(id=2, name="David Raya", age=28, nationality="Spain", position="Goalkeeper", photo=None),
        
        # Defenders
        Player(id=3, name="William Saliba", age=22, nationality="France", position="Defender", photo=None),
        Player(id=4, name="Gabriel Magalhães", age=25, nationality="Brazil", position="Defender", photo=None),
        Player(id=5, name="Ben White", age=25, nationality="England", position="Defender", photo=None),
        
        # Midfielders
        Player(id=6, name="Martin Ødegaard", age=24, nationality="Norway", position="Midfielder", photo=None),
        Player(id=7, name="Thomas Partey", age=30, nationality="Ghana", position="Midfielder", photo=None),
        Player(id=8, name="Declan Rice", age=24, nationality="England", position="Midfielder", photo=None),
        
        # Forwards
        Player(id=9, name="Bukayo Saka", age=21, nationality="England", position="Forward", photo=None),
        Player(id=10, name="Gabriel Jesus", age=26, nationality="Brazil", position="Forward", photo=None),
        Player(id=11, name="Gabriel Martinelli", age=22, nationality="Brazil", position="Forward", photo=None),
    ]


def test_team_squad_success(cli_runner, mock_service, sample_team, sample_players):
    """Test successful retrieval and display of a team squad."""
    # Set up mock return values
    mock_service.get_current_season.return_value = 2023
    mock_service.get_team.return_value = sample_team
    mock_service.get_players.return_value = sample_players
    
    # Run the CLI command
    result = cli_runner.invoke(team_squad, ['42'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Check that service methods were called correctly
    mock_service.get_team.assert_called_once_with(42)
    mock_service.get_players.assert_called_once_with(team_id=42, season=2023)
    
    # Check that output contains expected content
    assert sample_team.name in result.output
    assert "Emirates Stadium" in result.output
    assert "Season: 2023" in result.output
    
    # Check that players are displayed
    assert "Aaron Ramsdale" in result.output
    assert "Bukayo Saka" in result.output
    assert "Martin Ødegaard" in result.output
    
    # Check that positions are categorized
    assert "Goalkeepers:" in result.output
    assert "Defenders:" in result.output
    assert "Midfielders:" in result.output
    assert "Forwards:" in result.output
    
    # Check that the total count is correct
    assert "Total: 11 players" in result.output


def test_team_squad_with_season(cli_runner, mock_service, sample_team, sample_players):
    """Test squad retrieval with a specific season."""
    # Set up mock return values
    mock_service.get_team.return_value = sample_team
    mock_service.get_players.return_value = sample_players
    
    # Run the CLI command with season option
    result = cli_runner.invoke(team_squad, ['42', '--season', '2022'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Check that the service was called with the correct season
    mock_service.get_players.assert_called_once_with(team_id=42, season=2022)
    
    # Check that the season is displayed correctly
    assert "Season: 2022" in result.output


def test_team_not_found(cli_runner, mock_service):
    """Test handling of a non-existent team."""
    # Set up mock to return None for get_team
    mock_service.get_team.return_value = None
    
    # Run the CLI command
    result = cli_runner.invoke(team_squad, ['99999'])
    
    # Verify the command executed successfully (exits cleanly)
    assert result.exit_code == 0
    
    # Check that error message was displayed
    assert "Team with ID 99999 not found" in result.output
    
    # Verify get_players was not called
    mock_service.get_players.assert_not_called()


def test_no_players_found(cli_runner, mock_service, sample_team):
    """Test handling of a team with no players."""
    # Set up mocks
    mock_service.get_team.return_value = sample_team
    mock_service.get_players.return_value = []
    
    # Run the CLI command
    result = cli_runner.invoke(team_squad, ['42'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Check that team info is displayed
    assert sample_team.name in result.output
    
    # Check that error message was displayed
    assert "No player data available" in result.output


def test_player_without_position(cli_runner, mock_service, sample_team):
    """Test handling of players without position data."""
    # Create players with missing positions
    players_missing_positions = [
        Player(id=1, name="Player 1", age=25, nationality="Country", position="Goalkeeper", photo=None),
        Player(id=2, name="Player 2", age=27, nationality="Country", position=None, photo=None),
        Player(id=3, name="Player 3", age=30, nationality="Country", position="", photo=None),
    ]
    
    # Set up mocks
    mock_service.get_team.return_value = sample_team
    mock_service.get_players.return_value = players_missing_positions
    
    # Run the CLI command
    result = cli_runner.invoke(team_squad, ['42'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Check that players are displayed
    assert "Player 1" in result.output
    assert "Player 2" in result.output
    assert "Player 3" in result.output
    
    # Check that the "Others" category is used for players without position
    assert "Others:" in result.output


@patch('app.cli.commands.squad_cmd.get_position_color')
def test_position_coloring(mock_get_color, cli_runner, mock_service, sample_team, sample_players):
    """Test that positions are colored correctly."""
    # Set up mock color function
    mock_get_color.return_value = "\033[0;32m"  # Green color
    
    # Set up service mocks
    mock_service.get_team.return_value = sample_team
    mock_service.get_players.return_value = sample_players[:3]  # Just use a few players
    
    # Run the CLI command
    result = cli_runner.invoke(team_squad, ['42'])
    
    # Verify the command executed successfully
    assert result.exit_code == 0
    
    # Verify the color function was called for each player's position
    assert mock_get_color.call_count >= len(sample_players[:3])


def test_api_error_handling(cli_runner, mock_service):
    """Test handling of API errors."""
    from app.utils.error_handlers import APIError
    
    # Set up mock to raise an API error
    mock_service.get_team.side_effect = APIError("API Error: Cannot connect to API")
    
    # Run the CLI command
    result = cli_runner.invoke(team_squad, ['42'])
    
    # Verify the command shows the error but exits cleanly
    assert result.exit_code == 0
    assert "API Error:" in result.output


if __name__ == "__main__":
    # Can be run directly with: python -m pytest test_squad_command.py -v
    pytest.main(["-v", __file__])