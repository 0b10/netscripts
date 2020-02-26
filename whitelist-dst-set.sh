#!/bin/sh

function __whitelist_dst_set() {
  [[ -z $1 ]] && echo "\$1 should be a rule name: WL-DST-\${1}" && return 1;
  [[ -z $2 ]] && echo "\$2 should be a set name - these are whitelisted, and allowed" && return 1;

  local chain_name=$1;

  echo iptables -N "WL-DST-$chain_name";
  echo iptables -A $chain_name -m set --match-set $2 dst -j ALLOW;

  # log and deny everything else
  echo iptables -A $chain_name -j LOG --log-prefix "[FORWARD:REJECTED-${1}-EGRESS]" --log-level 6;
  echo iptables -A $chain_name -j REJECT --reject-with icmp-port-unreachable;
}

if [[ ! -z $@ ]]; then
  # if called directly
  __whitelist_dst_set "$@"
fi
