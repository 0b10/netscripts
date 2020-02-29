#!/usr/bin/env python3
from json import loads
from argparse import ArgumentParser


class Config:
    def __init__(self, path):
        with open('/etc/netscripts.json') as f:
            self._config = loads(f.read())
            self._hosts = self._config['hosts']

    def get_names(self):
        return [a['name'] for a in self._hosts]

    def get_src(self, name):
        for host in self._hosts:
            if host['name'] == name:
                return host['src']

    def get_white_egress_ipset_name(self, name):
        for host in self._hosts:
            if host['name'] == name:
                return host['whitelisted']['egress']['ipset_name']

    def get_global_white_egress_ipset_name(self):
        return self._config['global']['whitelisted']['egress']['ipset_name']


parser = ArgumentParser(description='Get config options from the netscripts config file')
exclusive = parser.add_mutually_exclusive_group()
exclusive.add_argument('--get-names', action='store_true', help='get a list of rule names')
exclusive.add_argument('--get-src', action='store', type=str,
                       help='get a src address, given the rule name')
exclusive.add_argument('--get-white-egress-ipset', action='store', type=str,
                       help='get the ipset name for the relative whitelisted rules. Take a rule name as an arg')
exclusive.add_argument('--get-global-white-egress-ipset-name', action='store_true',
                       help='get the name of the global egress whitelist ipset')


args = parser.parse_args()
conf = Config(path='/etc/netscripts.json')

if args.get_names:
    print('\n'.join(conf.get_names()))

if args.get_src:
    print(conf.get_src(name=args.get_src))

if args.get_white_egress_ipset:
    print(conf.get_white_egress_ipset_name(name=args.get_white_egress_ipset))

if args.get_global_white_egress_ipset_name:
    print(conf.get_global_white_egress_ipset_name())
