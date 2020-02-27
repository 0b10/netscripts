#!/usr/bin/env python3
from inotify_simple import INotify, flags
from json import loads
from re import match
from ipaddress import ip_address
from subprocess import check_output, CalledProcessError, call, check_call
from logging import DEBUG, getLogger, StreamHandler
from systemd.journal import JournalHandler

logger = getLogger()
logger.addHandler(JournalHandler(SYSLOG_IDENTIFIER='netscripts-daemon'))
logger.setLevel(DEBUG)


class Config:
    HOSTS = None
    DEVICES = None
    LIMITED_USER = None
    RETRIES = None
    DIG_TIMEOUT = None


class NetscriptsException(Exception):
    pass


try:
    with open('/etc/netscripts.json', 'r') as f:
        contents = loads(f.read())
        Config.HOSTS = contents.get('hosts', None) or []
        Config.DEVICES = contents.get('devices', None) or '/sys/class/net'
        Config.LIMITED_USER = contents.get('limited_user', None) or 'user'
        Config.RETRIES = contents.get('dig_opts', None).get('retries', None) or 5
        Config.DIG_TIMEOUT = contents.get('dig_opts', None).get('timeout', None) or 3
except Exception as e:
    logger.error('Unable to open config file - exiting', exc_info=True, stack_info=True)
    raise e


def resolve(hostnames, logger):
    user = ['su', Config.LIMITED_USER, '--command']
    result = []
    ips = []

    # resolve each host
    for hostname in hostnames:
        logger.info('Attempting to resolve for: %s', hostname)

        # retry if network error
        for attempt in range(Config.RETRIES):
            try:
                ips = check_output(
                    user + ['dig -4 +short +timeout={} {}'.format(Config.DIG_TIMEOUT, hostname)]
                ).decode('utf-8').split('\n')
                logger.info('Resolved for: %s', hostname)
                break
            except CalledProcessError as e:
                if e.returncode != 9:  # 9, network error I think.
                    logger.warning('Unable to resolve hostnames due to netwok error')
                    break  # don't bother retrying if not a network issue
                logger.error('Attempt %i/%i: Unable to resolve: %s',
                             attempt, Config.RETRIES, hostname, exc_info=True, stack_info=True)

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
            logger.warning('Received an empty result for resolved hostnames')
            raise NetscriptsException

    return list(set(result))  # remove duplicates


def ipset(name, logger, ips=None):
    call(['ipset', '-q', 'destroy', name])

    try:
        check_call(['ipset', 'create', name, 'hash:net'])
    except CalledProcessError as e:
        logger.error('Unable to create ipset: %s', name, exc_info=True, stack_info=True)
        raise e

    if ips:
        for ip in ips:
            try:
                check_call(['ipset', 'add', name, '{}/32'.format(ip)])
            except CalledProcessError as e:
                logger.error('Unable to add member to %s ipset: %s',
                             name, ip, exc_info=True, stack_info=True)
                raise e

    if ips:
        msg = 'Ipset successfully populated: {}'.format(name)
    else:
        msg = 'Empty ipset successfully created: {}'.format(name)

    logger.info(msg)


def create_whitelist(host, logger):
    whitelisted = host['domains']['whitelisted']
    ips = resolve(hostnames=whitelisted['domain_names'], logger=logger)
    ipset(name=whitelisted['ipset_name'], ips=ips, logger=logger)


def create_sets(logger):
    for host in Config.HOSTS:
        create_whitelist(host=host, logger=logger)


def create_empty_sets(logger):
    for host in Config.HOSTS:
        ipset_name = host['domains']['whitelisted']['ipset_name']
        ipset(name=ipset_name, logger=logger)
        # logger.info('Empty ipset successfully created: %s', ipset_name)


inotify = INotify()
watch_flags = flags.CREATE
inotify.add_watch(Config.DEVICES, watch_flags)

create_empty_sets(logger=logger)  # so that iptables rules have something to use

while True:
    event = inotify.read()
    try:
        for e in event:
            if match('^tun', e.name):
                logger.info('Tun device detected, creating ipsets...')
                create_sets(logger=logger)
    except NetscriptsException:
        # if it doesn't work for one, it won't work for any - so catch all here, but do nothing.
        logger.info('Stopped trying to resolve, waiting for next tun event')
        continue
