"""
Tests for the live scores CLI command.
"""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from datetime import datetime

from app.cli.cli import scores, cli
from app.models.football_data import (
    Fixture, League, FixtureTeam, FixtureStatus, FixtureScore
)


@pytest.fixture
def mock_fixtures():
    """Create mock fixtures for testing."""
    # Create a test league
    premier_league = League(
        id=39,
        name="Premier League",
        country="England",
        logo="https://media.api-sports.io/football/leagues/39.png",
        season=2022
    )
    
    # Create test fixtures
    return [
        Fixture(
            id=1234567,
            date=datetime(2023, 5, 20, 15, 0, 0),
            status=FixtureStatus(
                long="First Half",
                short="1H",
                elapsed=23
            ),
            home_team=FixtureTeam(
                id=42,
                name="Arsenal",
                logo="https://media.api-sports.io/football/teams/42.png",
                goals=1,
                winner=True
            ),
            away_team=FixtureTeam(
                id=33,
                name="Manchester United",
                logo="https://media.api-sports.io/football/teams/33.png",
                goals=0,
                winner=False
            ),
            league=premier_league,
            referee="John Smith",
            score=FixtureScore(
                halftime={"home": 1, "away": 0},
                fulltime=None,
                extratime=None,
                penalty=None
            )
        ),
        Fixture(
            id=1234568,
            date=datetime(2023, 5, 20, 15, 0, 0),
            status=FixtureStatus(
                long="Second Half",
                short="2H",
                elapsed=65
            ),
            home_team=FixtureTeam(
                id=50,
                name="Manchester City",
                logo="https://media.api-sports.io/football/teams/50.png",
                goals=2,
                winner=None
            ),
            away_team=FixtureTeam(
                id=40,
                name="Liverpool",
                logo="https://media.api-sports.io/football/teams/40.png",
                goals=2,
                winner=None
            ),
            league=premier_league,
            referee="Jane Doe",
            score=FixtureScore(
                halftime={"home": 1, "away": 1},
                fulltime=None,
                extratime=None,
                penalty=None
            )
        )
    ]


@pytest.fixture
def matches_by_league(mock_fixtures):
    """Create a dictionary of leagues to fixtures."""
    return {mock_fixtures[0].league: mock_fixtures}


class TestLiveScoresCommand:
    """Tests for the live scores CLI command."""

    def test_live_scores_specific_league(self, mock_fixtures):
        """Test the live scores command for a specific league."""
        runner = CliRunner()
        
        # Mock the FootballService to return our fixtures
        with patch('app.services.football_service.FootballService') as MockService:
            # Configure the mock to return our test fixtures
            mock_service_instance = MockService.return_value
            mock_service_instance.get_live_scores.return_value = mock_fixtures
            
            # Run the command
            result = runner.invoke(scores, ['live', '--league', '39'])
            
            # Check the command executed successfully
            assert result.exit_code == 0
            
            # Verify service was called correctly
            mock_service_instance.get_live_scores.assert_called_once_with(
                league_id=39, timezone='UTC'
            )
            
            # Check output contains match information
            assert "Arsenal" in result.output
            assert "Manchester United" in result.output
            assert "1 - 0" in result.output 
            assert "1H 23'" in result.output

    def test_live_scores_all_leagues(self, matches_by_league):
        """Test the live scores command for all leagues."""
        runner = CliRunner()
        
        # Mock the FootballService
        with patch('app.services.football_service.FootballService') as MockService:
            # Configure the mock
            mock_service_instance = MockService.return_value
            mock_service_instance.get_current_season.return_value = 2022
            mock_service_instance.get_live_matches_by_league.return_value = matches_by_league
            
            # Run the command
            result = runner.invoke(scores, ['live'])
            
            # Check the command executed successfully
            assert result.exit_code == 0
            
            # Verify service was called correctly
            mock_service_instance.get_live_matches_by_league.assert_called_once_with(
                country=None, season=2022, timezone='UTC'
            )
            
            # Check output contains expected information
            assert "Premier League (England)" in result.output
            assert "Total: 2 live matches in 1 leagues" in result.output

    def test_live_scores_formatting_options(self, mock_fixtures):
        """Test formatting options for live scores command."""
        runner = CliRunner()
        
        # Mock the FootballService
        with patch('app.services.football_service.FootballService') as MockService:
            # Configure the mock
            mock_service_instance = MockService.return_value
            mock_service_instance.get_live_scores.return_value = mock_fixtures
            
            # Test detailed format
            result = runner.invoke(scores, ['live', '--league', '39', '--format', 'detailed'])
            
            # Check detailed output format
            assert result.exit_code == 0
            assert "Match: Arsenal vs Manchester United" in result.output
            assert "Status: First Half (23')" in result.output

    def test_live_scores_country_filter(self, matches_by_league):
        """Test country filtering in live scores command."""
        runner = CliRunner()
        
        # Mock the FootballService
        with patch('app.services.football_service.FootballService') as MockService:
            # Configure the mock
            mock_service_instance = MockService.return_value
            mock_service_instance.get_current_season.return_value = 2022
            mock_service_instance.get_live_matches_by_league.return_value = matches_by_league
            
            # Run the command with country filter
            result = runner.invoke(scores, ['live', '--country', 'England'])
            
            # Check the command executed successfully
            assert result.exit_code == 0
            
            # Verify service was called with correct country
            mock_service_instance.get_live_matches_by_league.assert_called_once_with(
                country='England', season=2022, timezone='UTC'
            )
            
            # Check output contains expected information
            assert "Premier League (England)" in result.output

    def test_live_scores_no_matches(self):
        """Test live scores command when no matches are found."""
        runner = CliRunner()
        
        # Mock the FootballService to return empty results
        with patch('app.services.football_service.FootballService') as MockService:
            # Empty results for specific league
            mock_service_instance = MockService.return_value
            mock_service_instance.get_live_scores.return_value = []
            mock_service_instance.get_live_matches_by_league.return_value = {}
            
            # Test with specific league
            result = runner.invoke(scores, ['live', '--league', '39'])
            assert result.exit_code == 0
            assert "No live matches found" in result.output
            
            # Test with all leagues
            result = runner.invoke(scores, ['live'])
            assert result.exit_code == 0
            assert "No live matches found" in result.output

    def test_live_scores_api_error(self):
        """Test error handling in live scores command."""
        runner = CliRunner()
        
        # Mock the FootballService to raise an APIError
        with patch('app.services.football_service.FootballService') as MockService:
            from app.utils.error_handlers import APIError
            mock_service_instance = MockService.return_value
            mock_service_instance.get_live_scores.side_effect = APIError("API Error occurred", None)
            
            # Run the command
            result = runner.invoke(scores, ['live', '--league', '39'])
            
            # Check the command handles the error
            assert result.exit_code == 0  # Command should complete but show error
            assert "API Error" in result.output
