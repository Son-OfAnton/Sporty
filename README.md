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
