import random

from privas.bases import PrivaError
from privas.common import CommonPriva


class NWinsPriva(CommonPriva):
    class Meta:
        names = {
            'en': 'N-Wins',
            'zh_CN': 'n胜'
        }
        pkg_name = 'n_wins'
        type_name = 'n_wins'
        min_players = 8

    def __init__(self, n:int):
        super().__init__()
        if n < 2:
            raise PrivaError(12, 'Invalid parameter: `n`.')
        self.winners = None
        self.win_goal = n
        self.args = [n]

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
            sort_by_byes = self.active_players()
            sort_key = lambda player: (
                self.players[player]['byes'],
                -sum(self.players[player][x] for x in ['wins', 'loses']),
                -self.players[player]['wins']
            )
            sort_by_byes.sort(key=sort_key)
            to_byes = []
            i = 0
            l = len(active_players) - 8
            while l > 0:
                j = i + 1
                while j < len(sort_by_byes) and sort_key(sort_by_byes[j]) == sort_key(sort_by_byes[i]):
                    j += 1
                if j - i <= l:
                    to_byes.extend(sort_by_byes[i:j])
                    l -= j - i
                else:
                    to_byes.extend(random.sample(sort_by_byes[i:j], l))
                    l = 0
                i = j
            to_battle = active_players - set(to_byes)
            to_battle = [player['name'] for player in self._shuffle_by_score(self.standings(to_battle))]
            team_a = [to_battle[i] for i in [0, 7, 3, 4]]
            team_b = [to_battle[i] for i in [1, 6, 2, 5]]
            return team_a, team_b
        elif team_a and team_b:
            return team_a, team_b
        else:
            raise PrivaError(8, 'Invalid player combination.')

    def report(self, language='en'):
        ret = super().report(language)
        if self.winners is not None:
            ret['winners'] = self.winners
        return ret

    def end_battle(self, winner):
        ret = super().end_battle(winner)
        priva_winners = [player for player in self.active_players() if self.players[player]['wins'] >= self.win_goal]
        if len(priva_winners) > 0:
            ret.append(priva_winners)
            self.winners = priva_winners
        return ret

    def _undo_action(self, action):
        if action[1] == 'battle' and action[2] == 'end' and len(action) > 5:
            self.winners = None
        return super()._undo_action(action)


class TenWinsPriva(NWinsPriva):
    class Meta:
        names = {
            'en': 'Ten-Wins',
            'zh_CN': '十胜'
        }
        pkg_name = 'n_wins'
        type_name = 'ten_wins'
        min_players = 8

    def __init__(self):
        super().__init__(n=10)
        self.args = []
