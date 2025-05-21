"""
Tests for the live scores feature.
"""

import pytest
import responses
import json
from datetime import datetime
from urllib.parse import urljoin

from app.api.client import FootballAPIClient
from app.services.football_service import FootballService
from app.models.football_data import Fixture, League, FixtureTeam, FixtureStatus


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
    # We'll use monkeypatch in the tests to avoid making real API calls
    return FootballService(api_key=mock_api_key)


@pytest.fixture
def mock_live_response():
    """Create a mock response for the live scores endpoint."""
    return {
        "get": "fixtures",
        "parameters": {"live": "all"},
        "errors": [],
        "results": 2,
        "paging": {
            "current": 1,
            "total": 1
        },
        "response": [
            {
                "fixture": {
                    "id": 1234567,
                    "referee": "John Smith",
                    "timezone": "UTC",
                    "date": "2023-05-20T15:00:00+00:00",
                    "timestamp": 1673712000,
                    "status": {
                        "long": "First Half",
                        "short": "1H",
                        "elapsed": 23
                    },
                    "venue": {
                        "id": 1000,
                        "name": "Stadium A",
                        "city": "City A"
                    }
                },
                "league": {
                    "id": 39,
                    "name": "Premier League",
                    "country": "England",
                    "logo": "https://media.api-sports.io/football/leagues/39.png",
                    "flag": "https://media.api-sports.io/flags/gb.svg",
                    "season": 2022,
                    "round": "Regular Season - 19"
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
                    "home": 1,
                    "away": 0
                },
                "score": {
                    "halftime": {
                        "home": 1,
                        "away": 0
                    },
                    "fulltime": {
                        "home": None,
                        "away": None
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
            },
            {
                "fixture": {
                    "id": 1234568,
                    "referee": "Jane Doe",
                    "timezone": "UTC",
                    "date": "2023-05-20T15:00:00+00:00",
                    "timestamp": 1673712000,
                    "status": {
                        "long": "Second Half",
                        "short": "2H",
                        "elapsed": 65
                    },
                    "venue": {
                        "id": 1001,
                        "name": "Stadium B",
                        "city": "City B"
                    }
                },
                "league": {
                    "id": 39,
                    "name": "Premier League",
                    "country": "England",
                    "logo": "https://media.api-sports.io/football/leagues/39.png",
                    "flag": "https://media.api-sports.io/flags/gb.svg",
                    "season": 2022,
                    "round": "Regular Season - 19"
                },
                "teams": {
                    "home": {
                        "id": 50,
                        "name": "Manchester City",
                        "logo": "https://media.api-sports.io/football/teams/50.png",
                        "winner": None
                    },
                    "away": {
                        "id": 40,
                        "name": "Liverpool",
                        "logo": "https://media.api-sports.io/football/teams/40.png",
                        "winner": None
                    }
                },
                "goals": {
                    "home": 2,
                    "away": 2
                },
                "score": {
                    "halftime": {
                        "home": 1,
                        "away": 1
                    },
                    "fulltime": {
                        "home": None,
                        "away": None
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
def mock_live_response_with_league(mock_live_response):
    """Create a mock response for the live scores with a specific league."""
    # Copy the original response and modify parameters
    response = mock_live_response.copy()
    response["parameters"] = {"live": "all", "league": 39}
    
    # Only return fixtures from Premier League (already the case in our fixture)
    return response


class TestLiveScoresAPI:
    """Tests for the live scores API functionality."""

    @responses.activate
    def test_get_live_scores(self, mock_client, mock_live_response):
        """Test the get_live_scores method in the API client."""
        # Mock the API response
        url = urljoin(mock_client.BASE_URL, "fixtures")
        responses.add(
            responses.GET,
            url,
            json=mock_live_response,
            status=200
        )
        
        # Call the method
        result = mock_client.get_live_scores()
        
        # Check the result
        assert result == mock_live_response
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-apisports-key"] == "test_api_key"
        assert "live=all" in responses.calls[0].request.url
    
    @responses.activate
    def test_get_live_scores_with_league(self, mock_client, mock_live_response_with_league):
        """Test the get_live_scores method with a specific league ID."""
        # Mock the API response
        url = urljoin(mock_client.BASE_URL, "fixtures")
        responses.add(
            responses.GET,
            url,
            json=mock_live_response_with_league,
            status=200
        )
        
        # Call the method
        result = mock_client.get_live_scores(league_id=39)
        
        # Check the result
        assert result == mock_live_response_with_league
        assert len(responses.calls) == 1
        assert "league=39" in responses.calls[0].request.url
        assert "live=all" in responses.calls[0].request.url
    
    @responses.activate
    def test_get_live_scores_with_timezone(self, mock_client, mock_live_response):
        """Test the get_live_scores method with a timezone parameter."""
        # Mock the API response
        url = urljoin(mock_client.BASE_URL, "fixtures")
        responses.add(
            responses.GET,
            url,
            json=mock_live_response,
            status=200
        )
        
        # Call the method
        result = mock_client.get_live_scores(timezone="America/New_York")
        
        # Check the result
        assert result == mock_live_response
        assert len(responses.calls) == 1
        assert "timezone=America%2FNew_York" in responses.calls[0].request.url


class TestLiveScoresService:
    """Tests for the live scores service functionality."""

    @pytest.fixture
    def mock_football_service(self, mock_service, mock_live_response, monkeypatch):
        """Create a mock FootballService that returns predefined fixtures."""
        def mock_live_scores(*args, **kwargs):
            return mock_live_response
        
        # Mock the API client's get_live_scores method
        monkeypatch.setattr(mock_service.client, "get_live_scores", mock_live_scores)
        
        return mock_service
    
    def test_get_live_scores_returns_fixtures(self, mock_football_service, mock_live_response):
        """Test that get_live_scores returns a list of Fixture objects."""
        # Call the service method
        fixtures = mock_football_service.get_live_scores()
        
        # Check results
        assert len(fixtures) == 2
        
        # Verify that they are proper Fixture objects
        for fixture in fixtures:
            assert isinstance(fixture, Fixture)
            assert fixture.is_live
            assert isinstance(fixture.status, FixtureStatus)
            assert fixture.status.elapsed is not None
            assert isinstance(fixture.home_team, FixtureTeam)
            assert isinstance(fixture.away_team, FixtureTeam)
            assert isinstance(fixture.league, League)
    
    def test_get_live_scores_with_league_id(self, mock_football_service, monkeypatch, mock_live_response_with_league):
        """Test get_live_scores with a specific league ID."""
        # Replace the mocked response with the league-specific one
        def mock_live_scores_league(*args, **kwargs):
            # Verify league ID is passed correctly
            assert kwargs.get("league_id") == 39
            return mock_live_response_with_league
        
        monkeypatch.setattr(mock_football_service.client, "get_live_scores", mock_live_scores_league)
        
        # Call the service method
        fixtures = mock_football_service.get_live_scores(league_id=39)
        
        # Should return fixtures
        assert len(fixtures) == 2
        
        # All fixtures should belong to the Premier League
        for fixture in fixtures:
            assert fixture.league.id == 39
            assert fixture.league.name == "Premier League"
    
    def test_get_live_scores_preserves_match_details(self, mock_football_service, mock_live_response):
        """Test that fixture details are correctly parsed from the API response."""
        # Call the service method
        fixtures = mock_football_service.get_live_scores()
        
        # Get the first fixture from our test data
        fixture_data = mock_live_response["response"][0]
        fixture = fixtures[0]
        
        # Check that the details match
        assert fixture.id == fixture_data["fixture"]["id"]
        assert fixture.status.short == fixture_data["fixture"]["status"]["short"]
        assert fixture.status.elapsed == fixture_data["fixture"]["status"]["elapsed"]
        assert fixture.home_team.name == fixture_data["teams"]["home"]["name"]
        assert fixture.away_team.name == fixture_data["teams"]["away"]["name"]
        assert fixture.home_team.goals == fixture_data["goals"]["home"]
        assert fixture.away_team.goals == fixture_data["goals"]["away"]
    
    def test_get_live_matches_by_league(self, mock_football_service, monkeypatch):
        """Test get_live_matches_by_league method."""
        # Create a simplified mock for testing the method
        test_league = League(id=39, name="Premier League", country="England", logo="")
        test_fixtures = [
            Fixture(
                id=1, 
                date=datetime.now(),
                status=FixtureStatus(long="First Half", short="1H", elapsed=23),
                home_team=FixtureTeam(id=42, name="Arsenal", logo="", goals=1),
                away_team=FixtureTeam(id=33, name="Manchester United", logo="", goals=0),
                league=test_league
            )
        ]
        
        # Mock the required methods
        def mock_get_leagues(*args, **kwargs):
            return [test_league]
        
        def mock_get_live_scores(*args, **kwargs):
            return test_fixtures if kwargs.get("league_id") == 39 else []
        
        monkeypatch.setattr(mock_football_service, "get_leagues", mock_get_leagues)
        monkeypatch.setattr(mock_football_service, "get_live_scores", mock_get_live_scores)
        
        # Call the method
        result = mock_football_service.get_live_matches_by_league()
        
        # Check the result
        assert len(result) == 1
        assert test_league in result
        assert result[test_league] == test_fixtures
