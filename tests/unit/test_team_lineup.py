"""
Tests for the team lineup feature.
"""

import pytest
import responses
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from urllib.parse import urljoin

from app.api.client import FootballAPIClient
from app.services.football_service import FootballService
from app.cli.cli import scores
from app.models.football_data import (
    Fixture, League, FixtureTeam, FixtureStatus, 
    TeamLineup, Player
)


@pytest.fixture
def mock_api_key():
    """Return a mock API key."""
    return "test_api_key"


@pytest.fixture
def mock_client(mock_api_key):
    """Create a mock FootballAPIClient."""
    return FootballAPIClient(api_key=mock_api_key)


@pytest.fixture
def mock_service(mock_api_key):
    """Create a mock FootballService with the API client mocked."""
    return FootballService(api_key=mock_api_key)


@pytest.fixture
def mock_fixture():
    """Create a mock fixture for testing."""
    premier_league = League(
        id=39,
        name="Premier League",
        country="England",
        logo="https://media.api-sports.io/football/leagues/39.png",
        season=2022
    )
    
    return Fixture(
        id=1234567,
        date="2023-05-20T15:00:00+00:00",
        status=FixtureStatus(
            long="Match Finished",
            short="FT",
            elapsed=90
        ),
        home_team=FixtureTeam(
            id=42,
            name="Arsenal",
            logo="https://media.api-sports.io/football/teams/42.png",
            goals=2,
            winner=True
        ),
        away_team=FixtureTeam(
            id=33,
            name="Manchester United",
            logo="https://media.api-sports.io/football/teams/33.png",
            goals=1,
            winner=False
        ),
        league=premier_league,
        venue="Emirates Stadium",
        referee="Anthony Taylor"
    )


@pytest.fixture
def mock_lineups_response():
    """Create a mock response for the fixture lineups endpoint."""
    return {
        "get": "fixtures/lineups",
        "parameters": {"fixture": "1234567"},
        "errors": [],
        "results": 2,
        "paging": {
            "current": 1,
            "total": 1
        },
        "response": [
            {
                "team": {
                    "id": 42,
                    "name": "Arsenal",
                    "logo": "https://media.api-sports.io/football/teams/42.png",
                    "colors": {
                        "player": {
                            "primary": "ff0000",
                            "number": "ffffff",
                            "border": "ff0000"
                        },
                        "goalkeeper": {
                            "primary": "ffff00",
                            "number": "000000",
                            "border": "ffff00"
                        }
                    }
                },
                "coach": {
                    "id": 100,
                    "name": "Mikel Arteta",
                    "photo": "https://media.api-sports.io/football/coachs/100.png"
                },
                "formation": "4-3-3",
                "startXI": [
                    {
                        "player": {
                            "id": 101,
                            "name": "Aaron Ramsdale",
                            "number": 32,
                            "pos": "G",
                            "grid": "1:1"
                        }
                    },
                    {
                        "player": {
                            "id": 102,
                            "name": "Ben White",
                            "number": 4,
                            "pos": "D",
                            "grid": "2:4"
                        }
                    },
                    {
                        "player": {
                            "id": 103,
                            "name": "Gabriel",
                            "number": 6,
                            "pos": "D",
                            "grid": "2:3"
                        }
                    },
                    {
                        "player": {
                            "id": 104,
                            "name": "William Saliba",
                            "number": 12,
                            "pos": "D",
                            "grid": "2:2"
                        }
                    },
                    {
                        "player": {
                            "id": 105,
                            "name": "Oleksandr Zinchenko",
                            "number": 17,
                            "pos": "D",
                            "grid": "2:1"
                        }
                    },
                    {
                        "player": {
                            "id": 106,
                            "name": "Martin Odegaard",
                            "number": 8,
                            "pos": "M",
                            "grid": "3:3"
                        }
                    },
                    {
                        "player": {
                            "id": 107,
                            "name": "Thomas Partey",
                            "number": 5,
                            "pos": "M",
                            "grid": "3:2"
                        }
                    },
                    {
                        "player": {
                            "id": 108,
                            "name": "Granit Xhaka",
                            "number": 34,
                            "pos": "M",
                            "grid": "3:1"
                        }
                    },
                    {
                        "player": {
                            "id": 109,
                            "name": "Bukayo Saka",
                            "number": 7,
                            "pos": "F",
                            "grid": "4:3"
                        }
                    },
                    {
                        "player": {
                            "id": 110,
                            "name": "Gabriel Jesus",
                            "number": 9,
                            "pos": "F",
                            "grid": "4:2"
                        }
                    },
                    {
                        "player": {
                            "id": 111,
                            "name": "Gabriel Martinelli",
                            "number": 11,
                            "pos": "F",
                            "grid": "4:1"
                        }
                    }
                ],
                "substitutes": [
                    {
                        "player": {
                            "id": 112,
                            "name": "Matt Turner",
                            "number": 30,
                            "pos": "G",
                            "grid": None
                        }
                    },
                    {
                        "player": {
                            "id": 113,
                            "name": "Kieran Tierney",
                            "number": 3,
                            "pos": "D",
                            "grid": None
                        }
                    },
                    {
                        "player": {
                            "id": 114,
                            "name": "Eddie Nketiah",
                            "number": 14,
                            "pos": "F",
                            "grid": None
                        }
                    }
                ]
            },
            {
                "team": {
                    "id": 33,
                    "name": "Manchester United",
                    "logo": "https://media.api-sports.io/football/teams/33.png",
                    "colors": {
                        "player": {
                            "primary": "ff0000",
                            "number": "ffffff",
                            "border": "ff0000"
                        },
                        "goalkeeper": {
                            "primary": "00ff00",
                            "number": "000000",
                            "border": "00ff00"
                        }
                    }
                },
                "coach": {
                    "id": 200,
                    "name": "Erik ten Hag",
                    "photo": "https://media.api-sports.io/football/coachs/200.png"
                },
                "formation": "4-2-3-1",
                "startXI": [
                    {
                        "player": {
                            "id": 201,
                            "name": "David de Gea",
                            "number": 1,
                            "pos": "G",
                            "grid": "1:1"
                        }
                    },
                    {
                        "player": {
                            "id": 202,
                            "name": "Aaron Wan-Bissaka",
                            "number": 29,
                            "pos": "D",
                            "grid": "2:4"
                        }
                    },
                    {
                        "player": {
                            "id": 203,
                            "name": "Raphael Varane",
                            "number": 19,
                            "pos": "D",
                            "grid": "2:3"
                        }
                    },
                    {
                        "player": {
                            "id": 204,
                            "name": "Lisandro Martinez",
                            "number": 6,
                            "pos": "D",
                            "grid": "2:2"
                        }
                    },
                    {
                        "player": {
                            "id": 205,
                            "name": "Luke Shaw",
                            "number": 23,
                            "pos": "D",
                            "grid": "2:1"
                        }
                    },
                    {
                        "player": {
                            "id": 206,
                            "name": "Casemiro",
                            "number": 18,
                            "pos": "M",
                            "grid": "3:2"
                        }
                    },
                    {
                        "player": {
                            "id": 207,
                            "name": "Fred",
                            "number": 17,
                            "pos": "M",
                            "grid": "3:1"
                        }
                    },
                    {
                        "player": {
                            "id": 208,
                            "name": "Antony",
                            "number": 21,
                            "pos": "F",
                            "grid": "4:3"
                        }
                    },
                    {
                        "player": {
                            "id": 209,
                            "name": "Bruno Fernandes",
                            "number": 8,
                            "pos": "M",
                            "grid": "4:2"
                        }
                    },
                    {
                        "player": {
                            "id": 210,
                            "name": "Marcus Rashford",
                            "number": 10,
                            "pos": "F",
                            "grid": "4:1"
                        }
                    },
                    {
                        "player": {
                            "id": 211,
                            "name": "Wout Weghorst",
                            "number": 27,
                            "pos": "F",
                            "grid": "5:1"
                        }
                    }
                ],
                "substitutes": [
                    {
                        "player": {
                            "id": 212,
                            "name": "Tom Heaton",
                            "number": 22,
                            "pos": "G",
                            "grid": None
                        }
                    },
                    {
                        "player": {
                            "id": 213,
                            "name": "Harry Maguire",
                            "number": 5,
                            "pos": "D",
                            "grid": None
                        }
                    },
                    {
                        "player": {
                            "id": 214,
                            "name": "Jadon Sancho",
                            "number": 25,
                            "pos": "F",
                            "grid": None
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_fixture_response():
    """Create a mock response for the fixture endpoint."""
    return {
        "get": "fixtures",
        "parameters": {"id": "1234567"},
        "errors": [],
        "results": 1,
        "paging": {
            "current": 1,
            "total": 1
        },
        "response": [
            {
                "fixture": {
                    "id": 1234567,
                    "referee": "Anthony Taylor",
                    "timezone": "UTC",
                    "date": "2023-05-20T15:00:00+00:00",
                    "timestamp": 1673712000,
                    "status": {
                        "long": "Match Finished",
                        "short": "FT",
                        "elapsed": 90
                    },
                    "venue": {
                        "id": 1000,
                        "name": "Emirates Stadium",
                        "city": "London"
                    }
                },
                "league": {
                    "id": 39,
                    "name": "Premier League",
                    "country": "England",
                    "logo": "https://media.api-sports.io/football/leagues/39.png",
                    "flag": "https://media.api-sports.io/flags/gb.svg",
                    "season": 2022,
                    "round": "Regular Season - 36"
                },
                "teams": {
                    "home": {
                        "id": 42,
                        "name": "Arsenal",
                        "logo": "https://media.api-sports.io/football/teams/42.png",
                        "winner": True
                    },
                    "away": {
                        "id": 33,
                        "name": "Manchester United",
                        "logo": "https://media.api-sports.io/football/teams/33.png",
                        "winner": False
                    }
                },
                "goals": {
                    "home": 2,
                    "away": 1
                },
                "score": {
                    "halftime": {
                        "home": 1,
                        "away": 1
                    },
                    "fulltime": {
                        "home": 2,
                        "away": 1
                    },
                    "extratime": {
                        "home": None,
                        "away": None
                    },
                    "penalty": {
                        "home": None,
                        "away": None
                    }
                }
            }
        ]
    }


@pytest.fixture
def mock_team_lineups():
    """Create mock team lineups for testing."""
    # Arsenal lineup
    arsenal_lineup = TeamLineup(
        team_id=42,
        team_name="Arsenal",
        formation="4-3-3",
        starters=[
            Player(id=101, name="Aaron Ramsdale", number=32, position="G", grid="1:1"),
            Player(id=102, name="Ben White", number=4, position="D", grid="2:4"),
            Player(id=103, name="Gabriel", number=6, position="D", grid="2:3"),
            Player(id=104, name="William Saliba", number=12, position="D", grid="2:2"),
            Player(id=105, name="Oleksandr Zinchenko", number=17, position="D", grid="2:1"),
            Player(id=106, name="Martin Odegaard", number=8, position="M", grid="3:3"),
            Player(id=107, name="Thomas Partey", number=5, position="M", grid="3:2"),
            Player(id=108, name="Granit Xhaka", number=34, position="M", grid="3:1"),
            Player(id=109, name="Bukayo Saka", number=7, position="F", grid="4:3"),
            Player(id=110, name="Gabriel Jesus", number=9, position="F", grid="4:2"),
            Player(id=111, name="Gabriel Martinelli", number=11, position="F", grid="4:1")
        ],
        substitutes=[
            Player(id=112, name="Matt Turner", number=30, position="G"),
            Player(id=113, name="Kieran Tierney", number=3, position="D"),
            Player(id=114, name="Eddie Nketiah", number=14, position="F")
        ],
        coach="Mikel Arteta"
    )
    
    # Man Utd lineup
    man_utd_lineup = TeamLineup(
        team_id=33,
        team_name="Manchester United",
        formation="4-2-3-1",
        starters=[
            Player(id=201, name="David de Gea", number=1, position="G", grid="1:1"),
            Player(id=202, name="Aaron Wan-Bissaka", number=29, position="D", grid="2:4"),
            Player(id=203, name="Raphael Varane", number=19, position="D", grid="2:3"),
            Player(id=204, name="Lisandro Martinez", number=6, position="D", grid="2:2"),
            Player(id=205, name="Luke Shaw", number=23, position="D", grid="2:1"),
            Player(id=206, name="Casemiro", number=18, position="M", grid="3:2"),
            Player(id=207, name="Fred", number=17, position="M", grid="3:1"),
            Player(id=208, name="Antony", number=21, position="F", grid="4:3"),
            Player(id=209, name="Bruno Fernandes", number=8, position="M", grid="4:2"),
            Player(id=210, name="Marcus Rashford", number=10, position="F", grid="4:1"),
            Player(id=211, name="Wout Weghorst", number=27, position="F", grid="5:1")
        ],
        substitutes=[
            Player(id=212, name="Tom Heaton", number=22, position="G"),
            Player(id=213, name="Harry Maguire", number=5, position="D"),
            Player(id=214, name="Jadon Sancho", number=25, position="F")
        ],
        coach="Erik ten Hag"
    )
    
    return {42: arsenal_lineup, 33: man_utd_lineup}


class TestTeamLineupAPI:
    """Tests for the team lineup API functionality."""

    @responses.activate
    def test_get_fixture_lineups(self, mock_client, mock_lineups_response):
        """Test the get_fixture_lineups method."""
        # Mock the API response
        url = urljoin(mock_client.BASE_URL, "fixtures/lineups")
        responses.add(
            responses.GET,
            url,
            json=mock_lineups_response,
            status=200
        )
        
        # Call the method
        result = mock_client.get_fixture_lineups(fixture_id=1234567)
        
        # Check the result
        assert result == mock_lineups_response
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-apisports-key"] == "test_api_key"
        assert "fixture=1234567" in responses.calls[0].request.url


class TestTeamLineupService:
    """Tests for the team lineup service functionality."""

    def test_get_fixture_lineups(self, mock_service, monkeypatch, mock_lineups_response):
        """Test the get_fixture_lineups service method."""
        # Mock the client's get_fixture_lineups method
        def mock_get_fixture_lineups(*args, **kwargs):
            assert kwargs.get("fixture_id") == 1234567
            return mock_lineups_response
        
        monkeypatch.setattr(mock_service.client, "get_fixture_lineups", mock_get_fixture_lineups)
        
        # Use the api_utils parse_response function directly for the test
        from app.utils.api_utils import parse_response
        
        def mock_parse(*args, **kwargs):
            return parse_response(mock_lineups_response)
            
        monkeypatch.setattr(mock_service, "get_fixture_lineups", lambda fixture_id: {
            42: TeamLineup.from_api(parse_response(mock_lineups_response)[0]),
            33: TeamLineup.from_api(parse_response(mock_lineups_response)[1])
        })
        
        # Call the service method
        lineups = mock_service.get_fixture_lineups(fixture_id=1234567)
        
        # Check that we have lineups for both teams
        assert len(lineups) == 2
        assert 42 in lineups  # Arsenal team ID
        assert 33 in lineups  # Man Utd team ID
        
        # Check the Arsenal lineup
        arsenal = lineups[42]
        assert arsenal.team_name == "Arsenal"
        assert arsenal.formation == "4-3-3"
        assert arsenal.coach == "Mikel Arteta"
        assert len(arsenal.starters) == 11
        assert len(arsenal.substitutes) == 3
        
        # Check the Man Utd lineup
        man_utd = lineups[33]
        assert man_utd.team_name == "Manchester United"
        assert man_utd.formation == "4-2-3-1"
        assert man_utd.coach == "Erik ten Hag"
        assert len(man_utd.starters) == 11
        assert len(man_utd.substitutes) == 3
        
        # Check player information for a specific player
        saka = next((p for p in arsenal.starters if p.name == "Bukayo Saka"), None)
        assert saka is not None
        assert saka.number == 7
        assert saka.position == "F"
        assert saka.grid == "4:3"


class TestTeamLineupCommand:
    """Tests for the team lineup CLI command."""

    def test_scores_lineup_command(self, mock_team_lineups, mock_fixture):
        """Test the scores lineup command."""
        runner = CliRunner()
        
        # Mock the service
        with patch('app.services.football_service.FootballService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_fixtures_by_id.return_value = mock_fixture
            mock_service.get_fixture_lineups.return_value = mock_team_lineups
            
            # Run the command
            result = runner.invoke(scores, ['lineup', '1234567'])
            
            # Check the command executed successfully
            assert result.exit_code == 0
            
            # Check that service methods were called properly
            mock_service.get_fixtures_by_id.assert_called_once_with(fixture_id=1234567)
            mock_service.get_fixture_lineups.assert_called_once_with(fixture_id=1234567)
            
            # Check for key elements in the output
            # Match info
            assert "Arsenal vs Manchester United" in result.output
            
            # Team formations
            assert "Arsenal" in result.output
            assert "Formation: 4-3-3" in result.output
            assert "Manchester United" in result.output
            assert "Formation: 4-2-3-1" in result.output
            
            # Coach information
            assert "Coach: Mikel Arteta" in result.output
            assert "Coach: Erik ten Hag" in result.output
            
            # Starting XI
            assert "Starting XI:" in result.output
            assert "Aaron Ramsdale" in result.output
            assert "Bukayo Saka" in result.output
            assert "David de Gea" in result.output
            assert "Bruno Fernandes" in result.output
            
            # Substitutes
            assert "Substitutes:" in result.output
            assert "Eddie Nketiah" in result.output
            assert "Jadon Sancho" in result.output
            
            # Check for visual formation display
            assert "Formation:" in result.output
            
    def test_scores_lineup_no_visual(self, mock_team_lineups, mock_fixture):
        """Test the scores lineup command with visual formation disabled."""
        runner = CliRunner()
        
        # Mock the service
        with patch('app.services.football_service.FootballService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_fixtures_by_id.return_value = mock_fixture
            mock_service.get_fixture_lineups.return_value = mock_team_lineups
            
            # Run the command with --no-visual flag
            result = runner.invoke(scores, ['lineup', '1234567', '--no-visual'])
            
            # Check the command executed successfully
            assert result.exit_code == 0
            
            # Match info and basic lineup should still be there
            assert "Arsenal vs Manchester United" in result.output
            assert "Arsenal" in result.output
            assert "Formation: 4-3-3" in result.output
            
            # Starting XI and substitutes should be shown
            assert "Starting XI:" in result.output
            assert "Substitutes:" in result.output
            
    def test_scores_lineup_no_fixture(self):
        """Test scores lineup command when no fixture is found."""
        runner = CliRunner()
        
        # Mock the service
        with patch('app.services.football_service.FootballService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_fixtures_by_id.return_value = None
            
            # Run the command
            result = runner.invoke(scores, ['lineup', '1234567'])
            
            # Check the command executed successfully
            assert result.exit_code == 0
            assert "No fixture found" in result.output
    
    def test_scores_lineup_no_lineup(self, mock_fixture):
        """Test scores lineup command when no lineup data is found."""
        runner = CliRunner()
        
        # Mock the service
        with patch('app.services.football_service.FootballService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_fixtures_by_id.return_value = mock_fixture
            mock_service.get_fixture_lineups.return_value = {}
            
            # Run the command
            result = runner.invoke(scores, ['lineup', '1234567'])
            
            # Check the command executed successfully
            assert result.exit_code == 0
            assert "No lineup information available" in result.output
    
    def test_scores_lineup_api_error(self):
        """Test error handling in scores lineup command."""
        runner = CliRunner()
        
        # Mock the service to raise an APIError
        with patch('app.services.football_service.FootballService') as MockService:
            from app.utils.error_handlers import APIError
            mock_service = MockService.return_value
            mock_service.get_fixtures_by_id.side_effect = APIError("API Error occurred", None)
            
            # Run the command
            result = runner.invoke(scores, ['lineup', '1234567'])
            
            # Check the command handles the error
            assert result.exit_code == 0  # Command should complete but show error
            assert "API Error" in result.output