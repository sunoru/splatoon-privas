#!/usr/bin/env python3
import sys
import uuid

import zerorpc

from privas import Privas, PrivaError


class PrivaRPC:
    priva_pool = {}

    @staticmethod
    def list_priva_types():
        return {
            x: {
                'names': Privas[x].Meta.names,
                'args': [
                    (arg, Privas[x].__init__.__annotations__.get(arg, str).__name__)
                    for arg in Privas[x].__init__.__code__.co_varnames[1:]
                ]
            }
            for x in Privas.keys()
        }

    def list_privas(self):
        return {pid: str(self.priva_pool[pid]) for pid in self.priva_pool}

    def show_rules(self, typename, language='en'):
        if typename not in Privas:
            raise NotImplementedError()
        return Privas[typename].rules(language)

    def create_priva(self, typename, *args, **kwargs):
        if typename not in Privas:
            raise NotImplementedError()
        priva = Privas[typename](*args, **kwargs)
        pid = str(uuid.uuid1())
        self.priva_pool[pid] = priva
        return pid

    def delete_priva(self, pid):
        if pid not in self.priva_pool:
            return False
        del self.priva_pool[pid]
        return True

    def run_action(self, pid, action, *args, **kwargs):
        if pid not in self.priva_pool:
            raise Exception(-2, 'Invalid priva ID')
        priva = self.priva_pool[pid]
        action_func = getattr(priva, action)
        if action_func is None:
            raise Exception(-3, 'Invalid action name')
        if 'no_return' in kwargs:
            action_func(*args, **kwargs)
            return True
        return action_func(*args, **kwargs)
    

    def restore_priva(self, typename, pid, json_data):
        if typename not in Privas:
            raise NotImplementedError()
        priva_class = Privas[typename]
        action_func = getattr(priva_class, 'from_json')
        if action_func is None:
            raise NotImplementedError()
        priva = action_func(json_data)
        self.priva_pool[pid] = priva
        return pid


def main():
    endpoint = sys.argv[1] if len(sys.argv) > 1 else 'tcp://0.0.0.0:4242'
    s = zerorpc.Server(PrivaRPC())
    s.bind(endpoint)
    s.run()


if __name__ == '__main__':
    main()
