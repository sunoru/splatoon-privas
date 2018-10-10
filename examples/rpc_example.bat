zerorpc tcp://127.0.0.1:4242 create_priva Ten-Wins
zerorpc tcp://127.0.0.1:4242 run_action 0 start
zerorpc tcp://127.0.0.1:4242 run_action 0 \"add_players\" [\"a\",\"b\",\"c\",\"d\",\"e\",\"f\",\"g\",\"h\",\"i\"] --json
zerorpc tcp://127.0.0.1:4242 run_action 0 start_battle
zerorpc tcp://127.0.0.1:4242 run_action 0 \"end_battle\" true --json
zerorpc tcp://127.0.0.1:4242 run_action 0 report
zerorpc tcp://127.0.0.1:4242 run_action 0 start_battle
zerorpc tcp://127.0.0.1:4242 run_action 0 \"end_battle\" true --json
zerorpc tcp://127.0.0.1:4242 run_action 0 report
zerorpc tcp://127.0.0.1:4242 run_action 0 dump_json
zerorpc tcp://127.0.0.1:4242 run_action 0 end
