#!/usr/bin/env python3
import json
import sys

import zerorpc

from privas import Privas, PrivaError


class PrivaRPC:
    priva_pool = {}
    n = 0

    def create_priva(self, typename, *args, **kwargs):
        if typename not in Privas:
            raise NotImplementedError()
        priva = Privas[typename](*args, **kwargs)
        pid = self.n
        self.n += 1
        self.priva_pool[pid] = priva
        return pid

    def delete_priva(self, pid):
        if pid not in self.priva_pool:
            return False
        del self.priva_pool[pid]
        return True

    def run_action(self, pid, action, *args, **kwargs):
        pid = int(pid)
        if pid not in self.priva_pool:
            raise Exception(1, 'Invalid priva ID')
        priva = self.priva_pool[pid]
        action_func = getattr(priva, action)
        if action_func is None:
            raise Exception(2, 'Invalid action name')
        try:
            return action_func(*args, **kwargs)
        except PrivaError as e:
            raise e


def main():
    endpoint = sys.argv[1] if len(sys.argv) > 1 else 'tcp://0.0.0.0:4242'
    s = zerorpc.Server(PrivaRPC())
    s.bind(endpoint)
    s.run()


if __name__ == '__main__':
    main()
