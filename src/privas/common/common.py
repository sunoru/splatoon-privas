import datetime
import glob
import json
import os
from privas.bases import BasePriva, PKG_PATH, PrivaError


class CommonPriva(BasePriva):
    """Class for Common functions. Most of the implementations of rules can inherit this class.

    status: -2 for Over, -1 for Ready, 0 for Started, n for Battle #n.
    """
    DATETIME_FMT = '%Y-%m-%d %H:%M:%S'

    class Meta:
        """Class for meta information of a Priva."""
        name = 'Common'
        pkg_name = 'common'
        min_players = 0

    def _from_dict(self, data):
        self.status = data['status']
        self.logs = data['logs']
        self.battles = data['battles']
        self.players = data['players']
        self.in_battle = data['in_battle']

    @classmethod
    def from_json(cls, json_data):
        x = cls()
        data = json.loads(json_data)
        x._from_dict(data)
        return x

    def _to_dict(self):
        return {
            'status': self.status,
            'logs': self.logs,
            'battles': self.battles,
            'players': self.players,
            'in_battle': self.in_battle
        }

    def dump_json(self, **kwargs):
        return json.dumps(self._to_dict(), **kwargs)

    def __init__(self):
        self.status = -1
        self.logs = []
        self.battles = {}
        self.players = {}
        self.in_battle = False

    def add_log(self, *info):
        time = datetime.datetime.now().strftime(CommonPriva.DATETIME_FMT)
        log = (time, *info)
        self.logs.append(log)
        return log

    def rules(self, language='en'):
        """Return the rule descriptions that are stored in a markdown file.
        If the language not supported it will choose the closest one."""
        path = os.path.join(PKG_PATH, self.__class__.Meta.pkg_name, "rules*.md")
        rule_files = glob.glob(path)
        rule_files.sort(key=lambda x: len(x))
        if len(rule_files) == 0:
            return
        tmp = list(filter(lambda x: x.lower().endswith("%s.md" % language.lower()), rule_files))
        if tmp:
            filename = tmp[0]
        else:
            tmp = list(filter(lambda x: x.lower().find("rules-%s" % language.lower()) >= 0, rule_files))
            if tmp:
                filename = tmp[0]
            else:
                filename = rule_files[0]
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
            raise PrivaError(2, 'The Private is during a battle.')
        new_players = []
        for player in players:
            if player not in self.players:
                new_players.append(player)
            elif self.players[player]['active']:
                raise PrivaError(1, '%s is already in this Private.' % player)
        if len(new_players) + len(self.active_players()) > 10:
            raise PrivaError(3, 'Too many (>10) players.')
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
                raise PrivaError(1, '%s is already removed or has not been added.' % player)
        for player in players:
            self.players[player]['active'] = False
        return self.add_log('players', 'remove', players)

    def _check_valid_battle(self, team_a, team_b):
        a, b, p = set(team_a), set(team_b), set(self.active_players())
        return len(a.intersection(b)) == 0 and p.issuperset(a) and p.issuperset(b) and len(p - a - b) <= 2

    def start_battle(self, team_a, team_b):
        if self.status < 0:
            raise PrivaError(3, 'The Priva is not started or is already over.')
        if self.in_battle:
            raise PrivaError(2, 'The Priva is already in a battle.')
        if self.Meta.min_players > 0 and len(self.players) < self.Meta.min_players:
            raise PrivaError(1, 'Players not enough.')
        if not self._check_valid_battle(team_a, team_b):
            raise PrivaError(4, 'Invalid player combination.')
        self.status += 1
        self.in_battle = True
        n = self.status
        self.battles[n] = {
            'num': n,
            'team_a': team_a,
            'team_b': team_b,
            'result': None
        }
        for player in self.active_players():
            if player not in team_a and player not in team_b:
                self.players[player]['byes'] += 1
        return self.add_log('battle', 'start', n, team_a, team_b)

    def end_battle(self, result):
        if self.status <= 0 or not self.in_battle:
            raise PrivaError(3, 'The Priva is not in a battle.')
        n = self.status
        battle = self.battles[n]
        battle['result'] = result
        self.in_battle = False
        win, lose = battle['team_a'], battle['team_b']
        if not result:
            win, lose = lose, win
        for player in win:
            self.players[player]['wins'] += 1
        for player in lose:
            self.players[player]['loses'] += 1
        return self.add_log('battle', 'end', n, result)

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
                result = action[4]
                battle['result'] = None
                self.in_battle = True
                win, lose = battle['team_a'], battle['team_b']
                if not result:
                    win, lose = lose, win
                for player in win:
                    self.players[player]['wins'] -= 1
                for player in lose:
                    self.players[player]['loses'] -= 1
        return True

    def undo(self):
        """Undo the last action in logs."""
        if len(self.logs) < 1:
            raise PrivaError(1, 'No action to undo.')
        action = self.logs.pop()
        return self._undo_action(action)

    def get_logs(self, num=None):
        """Return num recent logs. If num is None, return all logs."""
        return self.logs if num is None else self.logs[-num:]

    def standings(self, player_names=None):
        if player_names is None:
            player_names = self.players.keys()
        players = list(self.players[player] for player in player_names)
        players.sort(key=lambda x: (-x['wins'], -x['byes'], x['loses']))
        return players

    def _first_in_logs(self, *args, reverse=False):
        try:
            return next(filter(
                lambda x: all(x[i + 1] == y for (i, y) in enumerate(args)),
                reversed(self.logs) if reverse else self.logs
            ))
        except StopIteration:
            return None

    def report(self):
        """Return current information of the Priva"""
        results = {
            'name': self.__class__.Meta.name,
            'status': self.status,
            'in_battle': self.in_battle,
            'standings': self.standings(),
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
            self.__class__.Meta.name, self.status, len(self.players), len(self.battles)
        )
