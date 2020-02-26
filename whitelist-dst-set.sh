#!/bin/sh

function __whitelist_dst_set() {
  [[ -z $1 ]] && echo "\$1 should be a rule name - it's just used for logging" && return 1;
  [[ -z $2 ]] && echo "\$2 should be a set name - these are whitelisted, and allowed" && return 1;
  [[ -z $3 ]] && echo "\$2 should be a chain name" && return 1;

  local chain_name=$3;

  iptables -N $chain_name || iptables -F $chain_name;
  iptables -A $chain_name -m set --match-set $2 dst -j ACCEPT;

  # log and deny everything else
  iptables -A $chain_name -j LOG --log-prefix "[FORWARD:REJECT-${1}-EGRESS]" --log-level 6;
  iptables -A $chain_name -j REJECT --reject-with icmp-port-unreachable;
}

if [[ ! -z $@ ]]; then
  # if called directly
  __whitelist_dst_set "$@"
fi
