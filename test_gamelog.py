from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.http import NBAStatsHTTP
import traceback

NBAStatsHTTP._headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.nba.com/'}

name = 'Stephen Curry'
pl = players.get_players()
player = [p for p in pl if p['full_name'] == name][0]
print('id', player['id'])
seasons = ['2025-26', '2024-25', '2023-24']

for season in seasons:
    try:
        g = playergamelog.PlayerGameLog(player_id=player['id'], season=season, season_type_all_star='Regular Season')
        df = g.get_data_frames()[0]
        print(season, 'rows', len(df))
        print(df[['GAME_DATE', 'MATCHUP', 'PTS']].head(3))
    except Exception as e:
        print('err', season, type(e), e)
        traceback.print_exc()
