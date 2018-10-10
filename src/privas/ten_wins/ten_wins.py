import random

from privas.bases import PrivaError
from privas.common import CommonPriva


class TenWinsPriva(CommonPriva):
    class Meta:
        names = {
            'en': 'Ten-Wins',
            'zh_CN': '十胜'
        }
        pkg_name = 'ten_wins'
        min_players = 8

    def __init__(self):
        super().__init__()
        self.winners = None

    def _from_dict(self, data):
        super()._from_dict(data)
        self.winners = data['winners']

    def _to_dict(self):
        ret = super()._to_dict()
        ret['winners'] = self.winners
        return ret

    @staticmethod
    def _shuffle_by_score(players):
        i = 0
        while i < len(players) - 1:
            j = i + 1
            while j < len(players) and all(players[j][x] == players[i][x] for x in ['wins', 'byes', 'loses']):
                j += 1
            # Knuth shuffle
            k = i
            while k < j - 1:
                p = random.randrange(k, j)
                players[k], players[p] = players[p], players[k]
                k += 1
            i = j
        return players

    def _match_players(self, team_a=None, team_b=None):
        team_a, team_b = super()._match_players(team_a, team_b)
        if not team_a and not team_b:
            active_players = set(self.active_players())
            to_battle = [
                player for player in active_players
                if sum(self.players[player][x] for x in ['wins', 'loses', 'byes']) < self.status
            ]
            to_sort = active_players - set(to_battle)
            standings = self._shuffle_by_score(self.standings(to_sort))
            to_battle += [player['name'] for player in standings[-(8 - len(to_battle)):]]
            team_a = [to_battle[i] for i in [0, 7, 3, 4]]
            team_b = [to_battle[i] for i in [1, 6, 2, 5]]
            return team_a, team_b
        elif team_a and team_b:
            return team_a, team_b
        else:
            raise PrivaError(4, 'Invalid player combination.')

    def end_battle(self, result):
        ret = super().end_battle(result)
        winners = [player for player in self.active_players() if self.players[player]['wins'] >= 10]
        if len(winners) > 0:
            ret.append(winners)
            self.winners = winners
        return ret

    def _undo_action(self, action):
        if action[1] == 'battle' and action[2] == 'end' and len(action) > 5:
            self.winners = None
        return super()._undo_action(action)
