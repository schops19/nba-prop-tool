import streamlit as st
import pandas as pd
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, commonteamroster
from nba_api.stats.library.http import NBAStatsHTTP
import datetime

# Set custom headers to mimic browser requests
NBAStatsHTTP._headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.nba.com/'
}

# The Odds API key - get from https://the-odds-api.com/
# Removed - now using demo mode only

def get_current_season():
    now = datetime.datetime.now()
    year = now.year
    month = now.month
    if month >= 10:  # NBA season starts in October
        start = year
        end = (year + 1) % 100
    else:
        start = year - 1
        end = year % 100
    return f"{start}-{end:02d}"

def get_player_id(name):
    nba_players = players.get_players()
    player = [p for p in nba_players if p['full_name'].lower() == name.lower()]
    if player:
        return player[0]['id']
    else:
        return None

def get_game_log_with_retries(player_id, season, retries=3, timeout=30):
    last_exception = None
    for attempt in range(1, retries + 1):
        try:
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star='Regular Season',
                timeout=timeout,
            )
            return gamelog
        except Exception as e:
            last_exception = e
            if attempt < retries:
                st.warning(f"Attempt {attempt}/{retries} failed for season {season}: {e}. Retrying on same season...")
            else:
                st.warning(f"Attempt {attempt}/{retries} failed for season {season}: {e}. Giving up on this season.")
    raise last_exception


def get_all_games(player_id, season=None, min_games=0):
    # Try current season first, then previous seasons until we gather min_games if requested
    if season is None:
        current = get_current_season()
        start_year = int(current.split('-')[0])
        seasons_to_try = [
            current,
            f"{start_year-1}-{(start_year)%100:02d}",
            f"{start_year-2}-{(start_year-1)%100:02d}"
        ]
    else:
        seasons_to_try = [season]

    all_games = []
    for s in seasons_to_try:
        try:
            gamelog = get_game_log_with_retries(player_id, s, retries=3, timeout=45)
            df = gamelog.get_data_frames()[0]
            if not df.empty:
                df = df.copy()
                df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
                all_games.append(df)

                if min_games > 0 and sum([len(gr) for gr in all_games]) >= min_games:
                    break
        except Exception as e:
            st.warning(f"Error fetching game log for {s}: {e}")
            continue

    if not all_games:
        return pd.DataFrame()

    combined = pd.concat(all_games, ignore_index=True)
    combined = combined.sort_values('GAME_DATE', ascending=False)
    return combined


@st.cache_data(ttl=600)
def get_recent_games(player_id, num_games=10, season=None):
    if not player_id or num_games <= 0:
        return pd.DataFrame()

    # play the same approach as get_all_games, but stop as soon as we have enough games
    if season is None:
        current = get_current_season()
        start_year = int(current.split('-')[0])
        seasons = [
            current,
            f"{start_year-1}-{(start_year)%100:02d}",
            f"{start_year-2}-{(start_year-1)%100:02d}"
        ]
    else:
        seasons = [season]

    games = []
    for s in seasons:
        try:
            gamelog = get_game_log_with_retries(player_id, s, retries=2, timeout=20)
            df = gamelog.get_data_frames()[0]
            if not df.empty:
                df = df.copy()
                df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
                games.append(df)

                combined = pd.concat(games, ignore_index=True).sort_values('GAME_DATE', ascending=False)
                if len(combined) >= num_games:
                    return combined.head(num_games)
        except Exception as e:
            st.warning(f"Season {s} unavailable (timeout or error): {e}. Trying prior season...")
            continue

    if not games:
        return pd.DataFrame()

    combined = pd.concat(games, ignore_index=True).sort_values('GAME_DATE', ascending=False)
    return combined.head(num_games)


st.title("NBA Prop Scout Dashboard")

st.markdown("Compare two NBA players' recent performance across the last N games.")

# Sidebar for settings
st.sidebar.title("Settings")

nba_teams = teams.get_teams()
team_names = sorted([t['full_name'] for t in nba_teams])

# Player 1 selection
selected_team_1 = st.sidebar.selectbox("Player 1 Team", ["All Teams"] + team_names)
if selected_team_1 != "All Teams":
    team1_obj = next((t for t in nba_teams if t['full_name'] == selected_team_1), None)
    if team1_obj:
        roster1 = commonteamroster.CommonTeamRoster(team_id=team1_obj['id']).get_data_frames()[0]
        player_names_1 = sorted(roster1['PLAYER'].tolist())
    else:
        player_names_1 = []
else:
    player_names_1 = sorted([p['full_name'] for p in players.get_players() if p.get('is_active')])

selected_player_1 = st.sidebar.selectbox("Player 1", player_names_1, index=player_names_1.index("Stephen Curry") if "Stephen Curry" in player_names_1 else 0)
custom_player_1 = st.sidebar.text_input("Or type custom Player 1 name", "")
player_1 = custom_player_1.strip() or selected_player_1

# Player 2 selection
selected_team_2 = st.sidebar.selectbox("Player 2 Team", ["All Teams"] + team_names)
if selected_team_2 != "All Teams":
    team2_obj = next((t for t in nba_teams if t['full_name'] == selected_team_2), None)
    if team2_obj:
        roster2 = commonteamroster.CommonTeamRoster(team_id=team2_obj['id']).get_data_frames()[0]
        player_names_2 = sorted(roster2['PLAYER'].tolist())
    else:
        player_names_2 = []
else:
    player_names_2 = sorted([p['full_name'] for p in players.get_players() if p.get('is_active')])

selected_player_2 = st.sidebar.selectbox("Player 2", player_names_2, index=player_names_2.index("LeBron James") if "LeBron James" in player_names_2 else 0)
custom_player_2 = st.sidebar.text_input("Or type custom Player 2 name", "")
player_2 = custom_player_2.strip() or selected_player_2

st.sidebar.markdown("---")
st.sidebar.write("### How many recent games to compare")

player1_id = get_player_id(player_1)
player2_id = get_player_id(player_2)

# Use fixed healthy upper bound to avoid a preload of all seasons, and get recent games quickly
max_games_1 = 82 if player1_id else 0
max_games_2 = 82 if player2_id else 0

if max_games_1 == 0 or max_games_2 == 0:
    max_games = max(max_games_1, max_games_2)
else:
    max_games = min(max_games_1, max_games_2)

if max_games <= 0:
    st.sidebar.info("No games available for one or both players.")
    num_games = 0
elif max_games == 1:
    num_games = 1
    st.sidebar.info("Only 1 game is available for comparison.")
else:
    num_games = st.sidebar.slider("How many recent games?", min_value=1, max_value=max_games, value=min(10, max_games))

def enrich_game_df(df):
    if df.empty:
        return df
    df = df.copy()
    df['PTS_REB_AST_AVG'] = (df['PTS'] + df['REB'] + df['AST']) / 3

    # Clean shooting percentage columns and mark as NaN where no attempts 
    for pct_col in ['FG_PCT', 'FT_PCT', 'FG3_PCT']:
        if pct_col in df.columns:
            df[pct_col] = pd.to_numeric(df[pct_col], errors='coerce')
        else:
            df[pct_col] = pd.NA

    # If no attempts for a given shooting type, set % to NaN so it doesn't bias averages
    if 'FGA' in df.columns:
        df.loc[df['FGA'] == 0, 'FG_PCT'] = pd.NA
    if 'FTA' in df.columns:
        df.loc[df['FTA'] == 0, 'FT_PCT'] = pd.NA
    if 'FG3A' in df.columns:
        df.loc[df['FG3A'] == 0, 'FG3_PCT'] = pd.NA

    return df


def summarize_stats(df):
    if df.empty:
        return {
            'PTS': 0, 'REB': 0, 'AST': 0, 'PTS_REB_AST_AVG': 0,
            'FG_PCT': None, 'FT_PCT': None, 'FG3_PCT': None
        }

    def safe_mean(series):
        if series.dropna().empty:
            return None
        return float(series.mean())

    return {
        'PTS': df['PTS'].mean(),
        'REB': df['REB'].mean(),
        'AST': df['AST'].mean(),
        'PTS_REB_AST_AVG': df['PTS_REB_AST_AVG'].mean(),
        'FG_PCT': safe_mean(df['FG_PCT']),
        'FT_PCT': safe_mean(df['FT_PCT']),
        'FG3_PCT': safe_mean(df['FG3_PCT'])
    }


if st.button("Analyze Players"):
    if not player_1:
        st.error("Please select Player 1.")
        st.stop()
    if not player_2:
        st.error("Please select Player 2.")
        st.stop()

    player1_id = get_player_id(player_1)
    player2_id = get_player_id(player_2)

    if not player1_id:
        st.error(f"Player 1 '{player_1}' not found.")
        st.stop()
    if not player2_id:
        st.error(f"Player 2 '{player_2}' not found.")
        st.stop()

    if max_games == 0:
        st.error("No overlapping game history available for the selected players.")
        st.stop()

    games1 = enrich_game_df(get_recent_games(player1_id, num_games))
    games2 = enrich_game_df(get_recent_games(player2_id, num_games))

    if games1.empty:
        st.error(f"No game data available for {player_1}.")
        st.stop()
    if games2.empty:
        st.error(f"No game data available for {player_2}.")
        st.stop()

    summary1 = summarize_stats(games1)
    summary2 = summarize_stats(games2)

    st.subheader(f"Player Comparison ({num_games} most recent games)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### {player_1}")
        st.metric("PTS", f"{summary1['PTS']:.1f}")
        st.metric("REB", f"{summary1['REB']:.1f}")
        st.metric("AST", f"{summary1['AST']:.1f}")
        st.metric("P/R/A avg", f"{summary1['PTS_REB_AST_AVG']:.1f}")
        st.metric("FG%", f"{summary1['FG_PCT']*100:.1f}%" if summary1['FG_PCT'] is not None else "N/A")
        st.metric("FT%", f"{summary1['FT_PCT']*100:.1f}%" if summary1['FT_PCT'] is not None else "N/A")
        st.metric("3P%", f"{summary1['FG3_PCT']*100:.1f}%" if summary1['FG3_PCT'] is not None else "N/A")

    with c2:
        st.markdown(f"### {player_2}")
        st.metric("PTS", f"{summary2['PTS']:.1f}")
        st.metric("REB", f"{summary2['REB']:.1f}")
        st.metric("AST", f"{summary2['AST']:.1f}")
        st.metric("P/R/A avg", f"{summary2['PTS_REB_AST_AVG']:.1f}")
        st.metric("FG%", f"{summary2['FG_PCT']*100:.1f}%" if summary2['FG_PCT'] is not None else "N/A")
        st.metric("FT%", f"{summary2['FT_PCT']*100:.1f}%" if summary2['FT_PCT'] is not None else "N/A")
        st.metric("3P%", f"{summary2['FG3_PCT']*100:.1f}%" if summary2['FG3_PCT'] is not None else "N/A")

    st.markdown("#### Player 1 recent games")
    st.dataframe(games1[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 'PTS_REB_AST_AVG', 'FG_PCT', 'FT_PCT', 'FG3_PCT']].reset_index(drop=True), use_container_width=True)

    st.markdown("#### Player 2 recent games")
    st.dataframe(games2[['GAME_DATE', 'MATCHUP', 'PTS', 'REB', 'AST', 'PTS_REB_AST_AVG', 'FG_PCT', 'FT_PCT', 'FG3_PCT']].reset_index(drop=True), use_container_width=True)

st.markdown("---")
st.markdown("Data sources: NBA API")