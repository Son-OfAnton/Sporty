"""
Football data models for the Sporty application.
"""

from dataclasses import dataclass, field
import dataclasses
from datetime import datetime
from typing import List, Dict, Any, Optional, Union


@dataclass
class League:
    """
    Represents a football league.

    Attributes:
        id: League ID
        name: League name
        country: Country name
        logo: URL to the league logo
        season: Current season
    """
    id: int
    name: str
    country: str
    logo: str
    season: Optional[int] = None
    type: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'League':
        """Create a League object from API data."""
        league_data = data.get("league", {})
        return cls(
            id=league_data.get("id"),
            name=league_data.get("name"),
            country=league_data.get("country"),
            logo=league_data.get("logo"),
            season=data.get("season"),
            type=league_data.get("type")
        )


@dataclass
class Team:
    """
    Represents a football team.

    Attributes:
        id: Team ID
        name: Team name
        country: Country name
        logo: URL to the team logo
        founded: Year the team was founded
        venue_name: Name of the team's venue
    """
    id: int
    name: str
    country: str
    logo: str
    founded: Optional[int] = None
    venue_name: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Team':
        """Create a Team object from API data."""
        team_data = data.get("team", {})
        venue = data.get("venue", {})

        return cls(
            id=team_data.get("id"),
            name=team_data.get("name"),
            country=team_data.get("country"),
            logo=team_data.get("logo"),
            founded=team_data.get("founded"),
            venue_name=venue.get("name") if venue else None
        )


@dataclass
class Player:
    """
    Represents a football player.

    Attributes:
        id: Player ID
        name: Player name
        age: Player age
        nationality: Player nationality
        position: Player position
        photo: URL to the player's photo
    """
    id: int
    name: str
    age: Optional[int] = None
    nationality: Optional[str] = None
    position: Optional[str] = None
    photo: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Player":
        """Create a Player object from API data."""
        # This handles both direct player data and nested player data
        # Try player key first, fallback to whole data
        player_data = data.get("player", data)

        return cls(
            id=player_data.get("id"),
            name=player_data.get("name"),
            age=player_data.get("age"),
            nationality=player_data.get("nationality"),
            position=player_data.get("position"),
            photo=player_data.get("photo")
        )


@dataclass
class FixtureStatus:
    """
    Fixture status information.

    Attributes:
        long: Long form status description (e.g. "In Play")
        short: Short form status code (e.g. "1H" for first half)
        elapsed: Minutes elapsed in the match
    """
    long: str
    short: str
    elapsed: Optional[int] = None

    @property
    def is_live(self) -> bool:
        """Check if the match is currently live."""
        live_statuses = ["1H", "2H", "HT", "ET", "BT", "P", "LIVE"]
        return self.short in live_statuses


@dataclass
class FixtureScore:
    """
    Score information for a fixture.

    Attributes:
        halftime: Score at halftime (home-away)
        fulltime: Score at fulltime (home-away)
        extratime: Score in extra time (home-away)
        penalty: Score in penalties (home-away)
    """
    halftime: Optional[Dict[str, int]] = None
    fulltime: Optional[Dict[str, int]] = None
    extratime: Optional[Dict[str, int]] = None
    penalty: Optional[Dict[str, int]] = None


@dataclass
class FixtureTeam:
    """
    Team information for a fixture.

    Attributes:
        id: Team ID
        name: Team name
        logo: URL to the team logo
        goals: Number of goals scored
        winner: True if this team is the winner
    """
    id: int
    name: str
    logo: str
    goals: Optional[int] = None
    winner: Optional[bool] = None


@dataclass
class Fixture:
    """
    Represents a football match fixture.

    Attributes:
        id: Fixture ID
        date: Date of the fixture
        status: Status of the fixture
        home_team: Home team information
        away_team: Away team information
        league: League information
        score: Detailed score information
        referee: Name of the referee
        venue: Venue information
    """
    id: int
    date: datetime
    status: FixtureStatus
    home_team: FixtureTeam
    away_team: FixtureTeam
    league: League
    score: Optional[FixtureScore] = None
    referee: Optional[str] = None
    venue: Optional[str] = None

    @property
    def is_live(self) -> bool:
        """Check if the match is currently live."""
        return self.status.is_live

    @property
    def score_display(self) -> str:
        """Get a display-friendly score string."""
        home_goals = self.home_team.goals if self.home_team.goals is not None else 0
        away_goals = self.away_team.goals if self.away_team.goals is not None else 0
        return f"{home_goals}-{away_goals}"

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'Fixture':
        """Create a Fixture object from API data."""
        fixture_data = data.get("fixture", {})
        teams_data = data.get("teams", {})
        goals_data = data.get("goals", {})
        score_data = data.get("score", {})
        status_data = fixture_data.get("status", {})

        # Create FixtureStatus
        status = FixtureStatus(
            long=status_data.get("long", ""),
            short=status_data.get("short", ""),
            elapsed=status_data.get("elapsed")
        )

        # Create FixtureTeams
        home_team = FixtureTeam(
            id=teams_data.get("home", {}).get("id", 0),
            name=teams_data.get("home", {}).get("name", ""),
            logo=teams_data.get("home", {}).get("logo", ""),
            goals=goals_data.get("home"),
            winner=teams_data.get("home", {}).get("winner")
        )

        away_team = FixtureTeam(
            id=teams_data.get("away", {}).get("id", 0),
            name=teams_data.get("away", {}).get("name", ""),
            logo=teams_data.get("away", {}).get("logo", ""),
            goals=goals_data.get("away"),
            winner=teams_data.get("away", {}).get("winner")
        )

        # Create FixtureScore
        score = FixtureScore(
            halftime=score_data.get("halftime"),
            fulltime=score_data.get("fulltime"),
            extratime=score_data.get("extratime"),
            penalty=score_data.get("penalty")
        )

        # Parse date
        date_str = fixture_data.get("date")
        date = datetime.fromisoformat(date_str.replace(
            "Z", "+00:00")) if date_str else datetime.now()

        # Create League
        league = League(
            id=data.get("league", {}).get("id", 0),
            name=data.get("league", {}).get("name", ""),
            country=data.get("league", {}).get("country", ""),
            logo=data.get("league", {}).get("logo", ""),
            season=data.get("league", {}).get("season")
        )

        return cls(
            id=fixture_data.get("id", 0),
            date=date,
            status=status,
            home_team=home_team,
            away_team=away_team,
            league=league,
            score=score,
            referee=fixture_data.get("referee"),
            venue=fixture_data.get("venue", {}).get("name")
        )


@dataclass
class TeamStanding:
    """
    Represents a team's standing in a league.

    Attributes:
        rank: Team's rank in the league
        team: Team information
        points: Total points
        played: Games played
        win: Games won
        draw: Games drawn
        lose: Games lost
        goals_for: Goals scored
        goals_against: Goals conceded
    """
    rank: int
    team: Team
    points: int
    played: int
    win: int
    draw: int
    lose: int
    goals_for: int
    goals_against: int

    @property
    def goal_difference(self) -> int:
        """Get the goal difference."""
        return self.goals_for - self.goals_against

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'TeamStanding':
        """Create a TeamStanding object from API data."""
        team_data = data.get("team", {})

        team = Team(
            id=team_data.get("id", 0),
            name=team_data.get("name", ""),
            country="",  # Not provided in standings
            logo=team_data.get("logo", "")
        )

        all_data = data.get("all", {})
        goals_data = all_data.get("goals", {})

        return cls(
            rank=data.get("rank", 0),
            team=team,
            points=data.get("points", 0),
            played=all_data.get("played", 0),
            win=all_data.get("win", 0),
            draw=all_data.get("draw", 0),
            lose=all_data.get("lose", 0),
            goals_for=goals_data.get("for", 0),
            goals_against=goals_data.get("against", 0)
        )


@dataclass
class FixtureEvent:
    """
    Represents an event that occurred during a match.

    Attributes:
        time: Time when the event occurred (in minutes)
        team_id: ID of the team this event belongs to
        team_name: Name of the team this event belongs to
        player_id: ID of the player involved
        player_name: Name of the player involved
        type: Type of event (Goal, Card, etc.)
        detail: Detailed type (Yellow Card, Red Card, Normal Goal, etc.)
        comments: Additional comments about the event
        assist_player_id: ID of the player who provided the assist (for goals)
        assist_player_name: Name of the player who provided the assist (for goals)
    """
    time: int
    team_id: int
    team_name: str
    player_id: Optional[int]
    player_name: str
    type: str
    detail: str
    comments: Optional[str] = None
    assist_player_id: Optional[int] = None
    assist_player_name: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'FixtureEvent':
        """Create a FixtureEvent object from API data."""
        time_data = data.get("time", {})
        team_data = data.get("team", {})
        player_data = data.get("player", {})
        assist_data = data.get("assist", {})

        return cls(
            time=time_data.get("elapsed", 0),
            team_id=team_data.get("id", 0),
            team_name=team_data.get("name", ""),
            player_id=player_data.get("id"),
            player_name=player_data.get("name", ""),
            type=data.get("type", ""),
            detail=data.get("detail", ""),
            comments=data.get("comments"),
            assist_player_id=assist_data.get("id"),
            assist_player_name=assist_data.get("name")
        )


@dataclass
class TeamStatistic:
    """
    Represents a single statistic for a team.

    Attributes:
        type: Type of statistic
        value: Value of the statistic
    """
    type: str
    value: Any


@dataclass
class FixtureStatistics:
    """
    Represents statistics for a team in a fixture.

    Attributes:
        team_id: ID of the team
        team_name: Name of the team
        statistics: List of statistics
    """
    team_id: int
    team_name: str
    statistics: List[TeamStatistic]

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'FixtureStatistics':
        """Create a FixtureStatistics object from API data."""
        team_data = data.get("team", {})
        statistics_data = data.get("statistics", [])

        statistics = []
        for stat in statistics_data:
            if stat.get("type") and stat.get("value") is not None:
                statistics.append(TeamStatistic(
                    type=stat.get("type"),
                    value=stat.get("value")
                ))

        return cls(
            team_id=team_data.get("id", 0),
            team_name=team_data.get("name", ""),
            statistics=statistics
        )


@dataclass
class LineupPlayer:
    """
    Represents a player in a lineup.

    Attributes:
        id: Player ID
        name: Player name
        number: Shirt number
        position: Position
        grid: Position on field grid (if available)
    """
    id: int
    name: str
    number: Optional[int] = None
    position: Optional[str] = None
    grid: Optional[str] = None


@dataclass
class TeamLineup:
    """
    Represents a team's lineup for a fixture.

    Attributes:
        team_id: Team ID
        team_name: Team name
        formation: Team formation (e.g., "4-3-3")
        starters: List of starting players
        substitutes: List of substitute players
        coach: Name of the coach
    """
    team_id: int
    team_name: str
    formation: str
    starters: List[LineupPlayer]
    substitutes: List[LineupPlayer]
    coach: str

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'TeamLineup':
        """Create a TeamLineup object from API data."""
        team_data = data.get("team", {})
        coach_data = data.get("coach", {})
        starters_data = data.get("startXI", [])
        subs_data = data.get("substitutes", [])

        starters = []
        for player_data in starters_data:
            player_info = player_data.get("player", {})
            starters.append(LineupPlayer(
                id=player_info.get("id", 0),
                name=player_info.get("name", ""),
                number=player_info.get("number"),
                position=player_info.get("position"),
                grid=player_info.get("grid")
            ))

        substitutes = []
        for player_data in subs_data:
            player_info = player_data.get("player", {})
            substitutes.append(LineupPlayer(
                id=player_info.get("id", 0),
                name=player_info.get("name", ""),
                number=player_info.get("number"),
                position=player_info.get("position")
            ))

        return cls(
            team_id=team_data.get("id", 0),
            team_name=team_data.get("name", ""),
            formation=data.get("formation", ""),
            starters=starters,
            substitutes=substitutes,
            coach=coach_data.get("name", "")
        )


@dataclass
class MatchStatistics:
    """
    Container for all statistics for a fixture.

    Attributes:
        events: List of match events
        team_statistics: Dictionary of team statistics, keyed by team ID
        lineups: Dictionary of team lineups, keyed by team ID
    """
    events: List[FixtureEvent]
    team_statistics: Dict[int, FixtureStatistics]
    lineups: Dict[int, TeamLineup]


@dataclass
class FixtureCount:
    """
    Represents fixture counts for a team.
    
    Attributes:
        home: Home fixtures count
        away: Away fixtures count
        total: Total fixtures count
    """
    home: int = 0
    away: int = 0
    total: int = 0

@dataclass
class GoalStats:
    """
    Represents goal statistics with distribution.
    
    Attributes:
        home: Home goals count
        away: Away goals count
        total: Total goals count
        average: Average goals per match
        minute: Distribution of goals by minute
    """
    home: int = 0
    away: int = 0
    total: int = 0
    average: float = 0.0
    minute: Optional[Dict[str, Any]] = None

@dataclass
class TeamGoalStats:
    """
    Represents a team's goal statistics.
    
    Attributes:
        for_goals: Goals scored statistics
        against: Goals conceded statistics
    """
    for_goals: GoalStats
    against: GoalStats

@dataclass
class CardStats:
    """
    Represents card statistics.
    
    Attributes:
        total: Total cards count
        minute: Distribution of cards by minute
    """
    total: int = 0
    minute: Optional[Dict[str, Any]] = None

@dataclass
class TeamCardStats:
    """
    Represents a team's disciplinary record.
    
    Attributes:
        yellow: Yellow cards statistics
        red: Red cards statistics
    """
    yellow: CardStats
    red: CardStats

@dataclass
class BiggestScores:
    """
    Represents biggest scoring records.
    
    Attributes:
        home: Biggest home score
        away: Biggest away score
    """
    home: Optional[str] = None
    away: Optional[str] = None

@dataclass
class StreakStats:
    """
    Represents streak statistics.
    
    Attributes:
        wins: Longest winning streak
        draws: Longest drawing streak
        losses: Longest losing streak
    """
    wins: int = 0
    draws: int = 0
    losses: int = 0

@dataclass
class BiggestStats:
    """
    Represents biggest record statistics.
    
    Attributes:
        goals: Biggest goals record
        wins: Biggest win records
        losses: Biggest loss records
        streak: Streak records
    """
    wins: BiggestScores
    losses: BiggestScores
    streak: StreakStats

@dataclass
class LineupStat:
    """
    Represents a lineup's usage statistics.
    
    Attributes:
        formation: Formation used (e.g., "4-3-3")
        played: Number of matches played with this formation
    """
    formation: str
    played: int

@dataclass
class TeamStatistics:
    """
    Comprehensive statistics for a team.
    
    Attributes:
        team: Team information
        league: League information
        season: Season information
        fixtures: Fixture count statistics
        goals: Goal statistics
        clean_sheet: Clean sheet statistics
        failed_to_score: Failed to score statistics
        cards: Card statistics
        biggest: Biggest record statistics
        lineups: Lineup statistics
    """
    team: Team
    league: Optional[League]
    form: Optional[str] = None
    fixtures: FixtureCount = field(default_factory=FixtureCount)
    goals: TeamGoalStats = None
    clean_sheet: FixtureCount = field(default_factory=FixtureCount)
    failed_to_score: FixtureCount = field(default_factory=FixtureCount)
    cards: TeamCardStats = None
    biggest: BiggestStats = None
    lineups: List[LineupStat] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> 'TeamStatistics':
        """Create a TeamStatistics object from API data."""
        team_data = data.get("team", {})
        league_data = data.get("league", {})
        
        team = Team(
            id=team_data.get("id", 0),
            name=team_data.get("name", ""),
            country=team_data.get("country", ""),
            logo=team_data.get("logo", "")
        )
        
        league = None
        if league_data:
            league = League(
                id=league_data.get("id", 0),
                name=league_data.get("name", ""),
                country=league_data.get("country", ""),
                logo=league_data.get("logo", ""),
                season=league_data.get("season")
            )
        
        # Parse fixture counts
        fixtures_data = data.get("fixtures", {})
        fixtures = FixtureCount(
            home=fixtures_data.get("played", {}).get("home", 0),
            away=fixtures_data.get("played", {}).get("away", 0),
            total=fixtures_data.get("played", {}).get("total", 0)
        )
        
        # Create fixture count objects for wins, draws, losses
        wins = FixtureCount(
            home=fixtures_data.get("wins", {}).get("home", 0),
            away=fixtures_data.get("wins", {}).get("away", 0),
            total=fixtures_data.get("wins", {}).get("total", 0)
        )
        
        draws = FixtureCount(
            home=fixtures_data.get("draws", {}).get("home", 0),
            away=fixtures_data.get("draws", {}).get("away", 0),
            total=fixtures_data.get("draws", {}).get("total", 0)
        )
        
        losses = FixtureCount(
            home=fixtures_data.get("loses", {}).get("home", 0),
            away=fixtures_data.get("loses", {}).get("away", 0),
            total=fixtures_data.get("loses", {}).get("total", 0)
        )
        
        # Set fixtures with all counts
        fixtures_full = dataclasses.replace(
            fixtures,
            wins=wins,
            draws=draws,
            losses=losses
        )
        
        # Parse goals statistics
        goals_data = data.get("goals", {})
        
        for_goals = GoalStats(
            home=goals_data.get("for", {}).get("total", {}).get("home", 0),
            away=goals_data.get("for", {}).get("total", {}).get("away", 0),
            total=goals_data.get("for", {}).get("total", {}).get("total", 0),
            average=float(goals_data.get("for", {}).get("average", {}).get("total", 0)),
            minute=goals_data.get("for", {}).get("minute", {})
        )
        
        against_goals = GoalStats(
            home=goals_data.get("against", {}).get("total", {}).get("home", 0),
            away=goals_data.get("against", {}).get("total", {}).get("away", 0),
            total=goals_data.get("against", {}).get("total", {}).get("total", 0),
            average=float(goals_data.get("against", {}).get("average", {}).get("total", 0)),
            minute=goals_data.get("against", {}).get("minute", {})
        )
        
        goals = TeamGoalStats(for_goals=for_goals, against=against_goals)
        
        # Parse clean sheet and failed to score stats
        clean_sheet_data = data.get("clean_sheet", {})
        clean_sheet = FixtureCount(
            home=clean_sheet_data.get("home", 0),
            away=clean_sheet_data.get("away", 0),
            total=clean_sheet_data.get("total", 0)
        )
        
        failed_to_score_data = data.get("failed_to_score", {})
        failed_to_score = FixtureCount(
            home=failed_to_score_data.get("home", 0),
            away=failed_to_score_data.get("away", 0),
            total=failed_to_score_data.get("total", 0)
        )
        
        # Parse card stats
        cards_data = data.get("cards", {})
        
        yellow_cards = CardStats(
            total=sum(int(count) for _, count in cards_data.get("yellow", {}).get("total", {}).items()),
            minute=cards_data.get("yellow", {}).get("minute", {})
        )
        
        red_cards = CardStats(
            total=sum(int(count) for _, count in cards_data.get("red", {}).get("total", {}).items()),
            minute=cards_data.get("red", {}).get("minute", {})
        )
        
        cards = TeamCardStats(yellow=yellow_cards, red=red_cards)
        
        # Parse biggest stats
        biggest_data = data.get("biggest", {})
        
        biggest_wins = BiggestScores(
            home=biggest_data.get("wins", {}).get("home"),
            away=biggest_data.get("wins", {}).get("away")
        )
        
        biggest_losses = BiggestScores(
            home=biggest_data.get("loses", {}).get("home"),
            away=biggest_data.get("loses", {}).get("away")
        )
        
        streak = StreakStats(
            wins=biggest_data.get("streak", {}).get("wins", 0),
            draws=biggest_data.get("streak", {}).get("draws", 0),
            losses=biggest_data.get("streak", {}).get("loses", 0)
        )
        
        biggest = BiggestStats(
            wins=biggest_wins,
            losses=biggest_losses,
            streak=streak
        )
        
        # Parse lineups
        lineups_data = data.get("lineups", [])
        lineups = []
        
        for lineup in lineups_data:
            lineups.append(LineupStat(
                formation=lineup.get("formation", ""),
                played=lineup.get("played", 0)
            ))
        
        return cls(
            team=team,
            league=league,
            form=data.get("form"),
            fixtures=fixtures_full,
            goals=goals,
            clean_sheet=clean_sheet,
            failed_to_score=failed_to_score,
            cards=cards,
            biggest=biggest,
            lineups=lineups
        )