#!/usr/bin/env python3
from inotify_simple import INotify, flags
from json import loads
from re import match
from ipaddress import ip_address
from subprocess import check_output, CalledProcessError, call, check_call


class Config:
    HOSTS = None
    DEVICES = None
    LIMITED_USER = None
    RETRIES = None
    DIG_TIMEOUT = None


class NetscriptsException(Exception):
    pass


with open('/etc/netscripts.json', 'r') as f:
    contents = loads(f.read())
    Config.HOSTS = contents.get('hosts', None) or []
    Config.DEVICES = contents.get('devices', None) or '/sys/class/net'
    Config.LIMITED_USER = contents.get('limited_user', None) or 'user'
    Config.RETRIES = contents.get('dig_opts', None).get('retries', None) or 5
    Config.DIG_TIMEOUT = contents.get('dig_opts', None).get('timeout', None) or 3


def resolve(hostnames):
    user = ['su', Config.LIMITED_USER, '--command']
    result = []
    ips = None

    # resolve each host
    for hostname in hostnames:

        # retry if network error
        for _ in range(Config.RETRIES):
            try:
                ips = check_output(
                    user + ['dig -4 +short +timeout={} {}'.format(Config.DIG_TIMEOUT, hostname)]
                ).decode('utf-8').split('\n')
            except CalledProcessError as e:
                if e.returncode != 9:  # 9, network error I think.
                    break  # don't bother retrying if not a network issue

        # could be None (on network error)
        if ips:
            # filter out non-ips - like CNAMEs, empty strings etc.
            for ip in ips:
                try:
                    ip_address(ip)
                    result.append(ip)
                except ValueError:
                    pass  # non-ip
        else:
            raise NetscriptsException

    return result


def ipset(name, ips=None):
    call(['ipset', '-q', 'destroy', name])
    check_call(['ipset', 'create', name, 'hash:net'])
    if ips:
        for ip in ips:
            check_call(['ipset', 'add', name, '{}/32'.format(ip)])


def create_whitelist(host):
    whitelisted = host['domains']['whitelisted']
    ips = resolve(hostnames=whitelisted['domain_names'])
    ipset(name=whitelisted['ipset_name'], ips=ips)


def create_sets():
    for host in Config.HOSTS:
        create_whitelist(host=host)


def create_empty_sets():
    for host in Config.HOSTS:
        ipset_name = host['domains']['whitelisted']['ipset_name']
        ipset(name=ipset_name)


create_empty_sets()  # so that iptables rules have something to use

inotify = INotify()
watch_flags = flags.CREATE
inotify.add_watch(Config.DEVICES, watch_flags)

while True:
    event = inotify.read()
    try:
        for e in event:
            if match('^tun', e.name):
                create_sets()
    except NetscriptsException:
        # if it doesn't work for one, it won't work for any - so catch all here, but do nothing.
        continue
