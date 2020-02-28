#!/usr/bin/env python3
from pyudev import Context, Monitor
from json import loads
from re import match
from ipaddress import ip_address
from subprocess import check_output, CalledProcessError, call, check_call
from logging import DEBUG, getLogger, StreamHandler
from systemd.journal import JournalHandler
from glob import glob

logger = getLogger()
logger.addHandler(JournalHandler(SYSLOG_IDENTIFIER='netscripts-daemon'))
logger.setLevel(DEBUG)


class Config:
    HOSTS = None
    DEVICES = None
    LIMITED_USER = None
    RETRIES = None
    DIG_TIMEOUT = None
    GLOBAL_EGRESS_IP_WL = []


class NetscriptsException(Exception):
    pass


try:
    with open('/etc/netscripts.json', 'r') as f:
        contents = loads(f.read())

        Config.HOSTS = contents\
            .get('hosts', [])

        Config.GLOBAL_EGRESS_IP_WL = contents\
            .get('global', {})\
            .get('whitelisted', {})\
            .get('egress', {})\
            .get('host_addr', [])

        Config.GLOBAL_EGRESS_IP_WL_IPSET_NAME = contents\
            .get('global', {})\
            .get('whitelisted', {})\
            .get('egress', {})['ipset_name']

        Config.LIMITED_USER = contents\
            .get('limited_user', 'user')

        Config.RETRIES = contents\
            .get('dig_opts', {})\
            .get('retries', 5)

        Config.DIG_TIMEOUT = contents\
            .get('dig_opts', {})\
            .get('timeout', 3)

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


class IPSet:
    def __init__(self, name, logger):
        self._name = name
        self._created = False
        self._logger = logger

    def _do(self, command, log_msg_success, log_msg_failure):
        if not self._created:
            try:
                check_call(command)
            except CalledProcessError:
                self._logger.debug(log_msg_failure, exc_info=True, stack_info=True)
                return False
        self._logger.debug(log_msg_success, exc_info=False, stack_info=False)
        return True

    def _create(self):
        return self._do(
            command=['ipset', 'create', self._name, 'hash:net'],
            log_msg_success='Ipset created: {}'.format(self._name),
            log_msg_failure='Unable to create ipset: {}'.format(self._name)
        )

    def _flush(self):
        return self._do(
            command=['ipset', '-q', 'flush', self._name],
            log_msg_success='Ipset flushed: {}'.format(self._name),
            log_msg_failure='Unable to flush ipset: {}'.format(self._name)
        )

    def _destroy(self):
        return self._do(
            command=['ipset', '-q', 'destroy', self._name],
            log_msg_success='Ipset destroyed: {}'.format(self._name),
            log_msg_failure='Unable to destroy ipset: {}'.format(self._name)
        )

    def create(self):
        # try creating first
        if self._create():
            return self

        # flush it, because if exists
        if self._flush():
            # now an empty set is available, so no create
            return self

        # else try recreating
        if self._destroy():
            if self._create():
                return self

        # something's wrong
        self._logger.error("Unable to create ipset: {}", self._name)
        raise Exception

    def add(self, ips):
        if ips:
            for ip in ips:
                added = self._do(
                    ['ipset', 'add', self._name, '{}/32'.format(ip)],
                    log_msg_success='Ip added to set: {}: {}'.format(self._name, ip),
                    log_msg_failure='Unable to add ip to set: {}: {}'.format(self._name, ip)
                )
                if not added:
                    raise Exception
        self._logger.info("Ipset populated: %s", self._name)


def create_egress_whitelist(host, logger):
    whitelisted = host['whitelisted']['egress']
    ips = resolve(hostnames=whitelisted['domain_names'], logger=logger)
    IPSet(name=whitelisted['ipset_name'], logger=logger).create().add(ips=ips)


def create_sets(logger):
    for host in Config.HOSTS:
        create_egress_whitelist(host=host, logger=logger)


def create_empty_sets(logger):
    for host in Config.HOSTS:
        ipset_name = host['whitelisted']['egress']['ipset_name']
        IPSet(name=ipset_name, logger=logger).create()


def create_static_sets(logger):
    IPSet(name=Config.GLOBAL_EGRESS_IP_WL_IPSET_NAME, logger=logger)\
        .create()\
        .add(ips=Config.GLOBAL_EGRESS_IP_WL)


create_empty_sets(logger=logger)  # so that iptables rules have something to use
create_static_sets(logger=logger)

context = Context()
monitor = Monitor.from_netlink(context)
monitor.filter_by('net')

# if a tun device already exists
for device in context.list_devices(subsystem='net'):
    if match('^tun', device.sys_name):
        logger.info('Tun device already exists, creating ipsets...')
        create_sets(logger=logger)

# monitor (poll) device events
for device in iter(monitor.poll, None):
    if device.action == 'add' and match('^tun', device.sys_name):
        logger.info('New tun device ({}) detected, creating ipsets...'.format(device.sys_name))
        try:
            create_sets(logger=logger)
        except NetscriptsException:
            logger.info('Stopped trying to resolve, waiting for next tun event')
            continue
