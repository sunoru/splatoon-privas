import json
from privas.ten_wins import TenWinsPriva

priva = TenWinsPriva()
priva.start()

players = [('player_%s' % i) for i in range(10)]

priva.add_players(players)

priva.start_battle()
priva.end_battle(True)
report = priva.report()
print(json.dumps(report, indent=4))

priva.start_battle()
priva.end_battle(True)
report = priva.report()
print(json.dumps(report, indent=4))
