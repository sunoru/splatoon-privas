import datetime
import glob
import json
import os
import re

from privas.bases import BasePriva, PKG_PATH, PrivaError
from privas.utils import find_language


class CommonPriva(BasePriva):
    """Class for Common functions. Most of the implementations of rules can inherit this class.

    status: -2 for Over, -1 for Ready, 0 for Started, n for Battle #n.
    """
    DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

    class Meta:
        """Class for meta information of a Priva."""
        names = {
            'en': 'Common',
            'zh_CN': '普通'
        }
        pkg_name = 'common'
        type_name = 'common'
        min_players = 0

    def _from_dict(self, data):
        self.status = data['status']
        self.logs = data['logs']
        self.battles = {
            int(x): data['battles'][x]
            for x in data['battles']
        }
        self.players = data['players']
        self.in_battle = data['in_battle']

    @classmethod
    def from_json(cls, json_data):
        data = json.loads(json_data)
        x = cls(*data['args'])
        x._from_dict(data)
        return x

    def _to_dict(self):
        return {
            'name': self.Meta.pkg_name,
            'args': self.args,
            'status': self.status,
            'logs': self.logs,
            'battles': self.battles,
            'players': self.players,
            'in_battle': self.in_battle
        }

    def dump_json(self, **kwargs):
        return json.dumps(self._to_dict(), **kwargs)

    def __init__(self):
        super().__init__()
        self.status = -1
        self.logs = []
        self.battles = {}
        self.players = {}
        self.in_battle = False
        self.args = []

    def add_log(self, *info):
        time = datetime.datetime.now().strftime(CommonPriva.DATETIME_FMT)
        log = [time, *info]
        self.logs.append(log)
        return log

    @classmethod
    def rules(cls, language='en'):
        """Return the rule descriptions that are stored in a markdown file.
        If the language not supported it will choose the closest one."""
        path = os.path.join(PKG_PATH, cls.Meta.pkg_name, "rules*.md")
        rule_files = glob.glob(path)
        rule_files.sort(key=lambda x: len(x))
        if len(rule_files) == 0:
            return
        i = max(find_language(
            list(''.join(re.split(r'rules|-|\.md', os.path.basename(x))) for x in rule_files),
            language
        )[0], 0)
        filename = rule_files[i]
        with open(filename, encoding='utf-8') as fi:
            return fi.read()

    def start(self):
        if self.status >= 0:
            raise PrivaError(1, 'Already started')
        self.status = 0
        return self.add_log('status', self.status)

    def end(self):
        prev_status = self.status
        self.status = -2
        return self.add_log('status', self.status, prev_status)

    def active_players(self):
        return list(filter(lambda x: self.players[x]['active'], self.players.keys()))

    def add_players(self, players):
        """Add a list of players."""
        if self.in_battle:
            raise PrivaError(2, 'The Priva is during a battle.')
        new_players = []
        for player in players:
            if player not in self.players:
                new_players.append(player)
            elif self.players[player]['active']:
                raise PrivaError(3, '%s is already in this Priva.' % player)
        if len(new_players) + len(self.active_players()) > 10:
            raise PrivaError(4, 'Too many (>10) players.')
        for player in new_players:
            self.players[player] = {
                'name': player,
                'wins': 0,
                'loses': 0,
                'byes': 0,
            }
        for player in players:
            self.players[player]['active'] = True
        return self.add_log('players', 'add', players, new_players)

    def remove_players(self, players):
        """Remove a list of players. Players will not be actually removed but marked as inactive."""
        if self.in_battle:
            raise PrivaError(2, 'The Priva is during a battle.')
        for player in players:
            if player not in self.players or not self.players[player]['active']:
                raise PrivaError(5, '%s is not in this Priva.' % player)
        for player in players:
            self.players[player]['active'] = False
        return self.add_log('players', 'remove', players)

    def _check_valid_battle(self, team_a, team_b):
        a, b, p = set(team_a), set(team_b), set(self.active_players())
        return len(a.intersection(b)) == 0 and p.issuperset(a) and p.issuperset(b) and len(p - a - b) <= 2

    def _match_players(self, team_a, team_b):
        if self.status < 0:
            raise PrivaError(6, 'The Priva is not started or already ended.')
        if self.in_battle:
            raise PrivaError(2, 'The Priva is already in a battle.')
        if self.Meta.min_players > 0 and len(self.active_players()) < self.Meta.min_players:
            raise PrivaError(7, 'Players not enough.')
        return team_a, team_b

    def _start_battle(self, team_a, team_b):
        if not self._check_valid_battle(team_a, team_b):
            raise PrivaError(8, 'Invalid player combination.')
        self.status += 1
        self.in_battle = True
        n = self.status
        self.battles[n] = {
            'num': n,
            'team_a': team_a,
            'team_b': team_b,
            'winner': None
        }
        byes = []
        for player in self.active_players():
            if player not in team_a and player not in team_b:
                self.players[player]['byes'] += 1
                byes.append(player)
        return self.add_log('battle', 'start', n, team_a, team_b, byes)

    def start_battle(self, team_a=None, team_b=None):
        team_a, team_b = self._match_players(team_a, team_b)
        return self._start_battle(team_a, team_b)

    def end_battle(self, winner):
        if self.status <= 0 or not self.in_battle:
            raise PrivaError(9, 'The Priva is not in a battle.')
        winner = winner.lower()
        if winner not in {'a', 'b'}:
            raise PrivaError(10, '`winner` should be "a" or "b".')
        n = self.status
        battle = self.battles[n]
        battle['winner'] = winner
        self.in_battle = False
        win, lose = battle['team_a'], battle['team_b']
        if winner == 'b':
            win, lose = lose, win
        for player in win:
            self.players[player]['wins'] += 1
        for player in lose:
            self.players[player]['loses'] += 1
        return self.add_log('battle', 'end', n, winner)

    def _undo_action(self, action):
        if action[1] == 'players':
            if action[2] == 'add':
                for player in action[3]:
                    if player in action[4]:
                        del self.players[player]
                    else:
                        self.players[player]['active'] = False
            elif action[2] == 'remove':
                for player in action[3]:
                    self.players[player]['active'] = True
        elif action[1] == 'status':
            if action[2] == 0:
                self.status = -1
            elif action[2] == -2:
                self.status = action[3]
        elif action[1] == 'battle':
            if action[2] == 'start':
                del self.battles[action[3]]
                self.status = action[3] - 1
                self.in_battle = False
                for player in self.active_players():
                    if player not in action[4] and player not in action[5]:
                        self.players[player]['byes'] -= 1
            elif action[2] == 'end':
                battle = self.battles[action[3]]
                winner = action[4]
                battle['winner'] = None
                self.in_battle = True
                win, lose = battle['team_a'], battle['team_b']
                if winner == 'b':
                    win, lose = lose, win
                for player in win:
                    self.players[player]['wins'] -= 1
                for player in lose:
                    self.players[player]['loses'] -= 1
        return True

    def undo(self):
        """Undo the last action in logs."""
        if len(self.logs) < 1:
            raise PrivaError(11, 'No action to undo.')
        action = self.logs.pop()
        return self._undo_action(action)

    def get_logs(self, num=None):
        """Return num recent logs. If num is None, return all logs."""
        return self.logs if num is None else self.logs[-num:]

    def standings(self, player_names=None):
        if player_names is None:
            player_names = self.players.keys()
        players = list(self.players[player] for player in player_names)
        players.sort(key=lambda x: (-x['wins'], x['loses']))
        return players

    def _first_in_logs(self, *args, reverse=False):
        try:
            return next(filter(
                lambda x: all(x[i + 1] == y for (i, y) in enumerate(args)),
                reversed(self.logs) if reverse else self.logs
            ))
        except StopIteration:
            return None

    def report(self, language='en'):
        """Return current information of the Priva"""
        results = {
            'name': self.Meta.names[find_language(list(self.Meta.names.keys()), language)[1]],
            'status': self.status,
            'in_battle': self.in_battle,
            'standings': self.standings(),
            'args': self.args
        }
        results['recent_battle'] = battle = self.battles[self.status] if self.status > 0 else None
        if battle is not None:
            battle['start_time'] = self._first_in_logs('battle', 'start', self.status)[0]
            x = self._first_in_logs('battle', 'end', self.status)
            battle['end_time'] = None if x is None else x[0]

        x = self._first_in_logs('status', 0, reverse=True)
        results['start_time'] = None if x is None else x[0]
        x = self._first_in_logs('status', -2, reverse=True)
        results['end_time'] = None if x is None else x[0]
        return results

    def __str__(self):
        return '<%s %s, %d Players, %d Battles>' % (
            self.Meta.names['en'], self.status, len(self.players), len(self.battles)
        )
