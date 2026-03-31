import argparse
import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.http import NBAStatsHTTP
import requests
import os
import datetime

# Set custom headers to mimic browser requests
NBAStatsHTTP._headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.nba.com/'
}

# The Odds API key - get from https://the-odds-api.com/
API_KEY = os.getenv('ODDS_API_KEY')  # Set environment variable or replace with your key

def get_current_season():
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    if month >= 10:  # NBA season starts in October
        return f"{year}-{year+1}"
    else:
        return f"{year-1}-{year}"

def get_player_id(name):
    nba_players = players.get_players()
    player = [p for p in nba_players if p['full_name'].lower() == name.lower()]
    if player:
        return player[0]['id']
    else:
        print(f"Player '{name}' not found.")
        return None

def get_last_10_games(player_id, season=None):
    if season is None:
        season = get_current_season()
    try:
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season, season_type_all_star='Regular Season')
        df = gamelog.get_data_frames()[0]
        return df.head(10)
    except Exception as e:
        print(f"Error fetching game log for {season}: {e}")
        return pd.DataFrame()

def get_betting_odds(player_name):
    if not API_KEY:
        print("API key not set. Please set ODDS_API_KEY environment variable.")
        return None
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&markets=player_points,player_rebounds,player_assists&regions=us"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # Find odds for the player
        player_odds = {}
        for game in data:
            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        if outcome.get('description', '').lower() == player_name.lower():
                            key = market['key']
                            if key not in player_odds:
                                player_odds[key] = []
                            player_odds[key].append({
                                'bookmaker': bookmaker['title'],
                                'line': outcome.get('point', 0),
                                'odds': outcome.get('price', 0)
                            })
        return player_odds
    except Exception as e:
        print(f"Error fetching betting odds: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='NBA Prop Bet Scout Tool')
    parser.add_argument('player_name', help='Full name of the NBA player')
    parser.add_argument('--season', help='NBA season (e.g., 2024-25)', default=None)
    args = parser.parse_args()

    player_name = args.player_name
    season = args.season
    player_id = get_player_id(player_name)
    if not player_id:
        return

    print(f"Found {player_name} (ID: {player_id})")

    df = get_last_10_games(player_id, season)
    if df.empty:
        print("No game data available.")
        return

    # Calculate stats
    avg_pts = df['PTS'].mean()
    avg_reb = df['REB'].mean()
    avg_ast = df['AST'].mean()

    print("\n--- PROP SCOUT REPORT ---")
    print(f"Games Analyzed: {len(df)}")
    print(f"Average Points: {avg_pts:.1f}")
    print(f"Average Rebounds: {avg_reb:.1f}")
    print(f"Average Assists: {avg_ast:.1f}")

    print("\nLast 10 Games:")
    print(df[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST']].to_string(index=False))

    # Fetch betting odds
    odds = get_betting_odds(player_name)
    if odds:
        print("\n--- BETTING LINES ---")
        for market, lines in odds.items():
            market_name = market.replace('player_', '').title()
            print(f"\n{market_name}:")
            for line in lines[:3]:  # Show top 3 bookmakers
                print(f"  {line['bookmaker']}: {line['line']} ({line['odds']})")
            # Compare to average
            avg_val = {'player_points': avg_pts, 'player_rebounds': avg_reb, 'player_assists': avg_ast}[market]
            if lines:
                typical_line = lines[0]['line']
                print(f"  Average vs Line: {avg_val:.1f} vs {typical_line} ({'Over' if avg_val > typical_line else 'Under'})")
    else:
        print("Could not fetch betting odds.")

if __name__ == "__main__":
    main()