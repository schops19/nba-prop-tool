# NBA Prop Tool

A tool to help with NBA prop bets by analyzing player performance from their last 10 games and comparing to current betting lines.

## Features

- Fetches player's last 10 games stats (points, rebounds, assists)
- Retrieves current betting odds for player props
- Compares averages to betting lines

## Installation

1. Clone or download this repository.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   Or manually:
   ```
   pip install nba_api pandas requests streamlit
   ```

## Usage

### Command Line Tool
Run the CLI tool with a player's full name:

```
python prop_scout.py "Stephen Curry"
```

To specify a season:

```
python prop_scout.py "Stephen Curry" --season 2025-26
```

### Web Dashboard
Run the interactive dashboard:

```
streamlit run dashboard.py
```

Then open the URL shown in your browser.

The dashboard features:
- Player search and analysis
- Visual metrics for averages
- Game-by-game breakdown table
- Sample betting odds comparison (demo mode)
- Over/under analysis based on recent performance

Example output:

```
Found Stephen Curry (ID: 201939)

--- PROP SCOUT REPORT ---
Games Analyzed: 10
Average Points: 27.5
Average Rebounds: 5.2
Average Assists: 6.8

Last 10 Games:
GAME_DATE   MATCHUP     PTS  REB  AST
2024-03-25  GSW vs LAL   30    6    7
...

--- BETTING LINES ---
Points:
  DraftKings: 26.5 (-110)
  FanDuel: 27.5 (-115)
  Average vs Line: 27.5 vs 26.5 (Over)
...
```

## Notes

- Uses NBA API for game stats
- Uses The Odds API for betting lines (requires API key)
- Defaults to the most recent season with available data; use --season to specify