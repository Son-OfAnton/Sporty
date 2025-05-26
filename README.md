# Sporty CLI

A command-line application for sports management and statistics.

## Installation

```bash
pip install -e .
```

## Usage

```bash
sporty --help
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/sporty.git
cd sporty

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## Live Scores Feature

The Sporty app includes a live scores feature to track matches currently in progress:

```bash
# Get live scores for all matches in progress
sporty live scores

# Get live scores for a specific league
sporty live scores --league 39  # Premier League

# Get live scores for all leagues in a country
sporty live scores --country "England"

# Choose your preferred timezone
sporty live scores --timezone "America/New_York"

# Get detailed information for each match
sporty live scores --format detailed
```

This feature shows real-time match updates including:

- Current score
- Match status (first half, second half, etc.)
- Minutes played
- Team information

Data is fetched directly from the API-Football service.

## Commands

Below is the list of all commands supported by Sporty CLI:

### matches scores

```bash
sporty matches scores [OPTIONS]
```

Filter and display match scores.
Options:

- `--league, -l` LEAGUE_ID
- `--team, -t` TEAM_ID
- `--country, -c` COUNTRY_NAME
- `--date, -d` YYYY-MM-DD
- `--from-date` YYYY-MM-DD
- `--to-date` YYYY-MM-DD
- `--season, -s` SEASON_YEAR
- `--live/--no-live`
- `--timezone, -tz` TIMEZONE
- `--format, -f` [table|detailed]

### live scores

```bash
sporty live scores [OPTIONS]
```

Alias for `matches scores --live`.
Options:

- `--league, -l` LEAGUE_ID
- `--country, -c` COUNTRY_NAME
- `--timezone, -t` TIMEZONE
- `--format, -f` [table|detailed]

### stats

```bash
sporty stats FIXTURE_ID
```

Display detailed statistics for a fixture.

### lineup

```bash
sporty lineup FIXTURE_ID
```

Show lineup for a fixture.

### squad

```bash
sporty squad TEAM_ID [OPTIONS]
```

Display squad for a team.
Options:

- `--season, -s` SEASON_YEAR

### history

```bash
sporty history TEAM_ID
```

Show historical results for a team.

### team-stats

```bash
sporty team-stats TEAM_ID [OPTIONS]
```

Display season statistics for a team.
Options:

- `--season, -s` SEASON_YEAR
- `--league, -l` LEAGUE_ID
- `--include-live/--exclude-live`

### standings league

```bash
sporty standings league [OPTIONS]
```

Display league standings.
Options:

- `--league, -l` LEAGUE_ID
- `--name, -n` LEAGUE_NAME
- `--country, -c` COUNTRY_NAME
- `--season, -s` SEASON_YEAR
- `--filter, -f` [all|home|away]

### standings list-leagues

```bash
sporty standings list-leagues [OPTIONS]
```

List available leagues.
Options:

- `--country, -c` COUNTRY_NAME
- `--season, -s` SEASON_YEAR
