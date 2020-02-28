#!/bin/sh

function __set_vpn_rules() {
  local cwd=`dirname $0`;

  source "${cwd}/whitelist-dst-set.sh";
  source "${cwd}/reject-domain.sh";
  source "${cwd}/allow-local-resolver.sh";
  source "${cwd}/reject-http.sh";
  config="${cwd}/get-config.py"
  get_config="python3 ${cwd}/get-config.py"

  # whitelist dst hosts
  names=`$get_config --get-names`;
  for name in ${names[@]}; do
    src=`$get_config --get-src $name`;
    ipset_name=`$get_config --get-white-egress-ipset $name`;

    chain_name="WL-$name-EGRESS"
    __whitelist_dst_set $name $ipset_name $chain_name;  # $1:rule_name $2:ipset_name $3:chain_name
    local rule="FORWARD -i vif+ -o tun+ -s $src -j $chain_name";
    iptables --check `echo $rule` || iptables -I `echo $rule`
  done

  # check rule doesn't exist first
  # ! must be inserted after other forwarding rules, this should be at the top of the forward chain.
  for target in REJECT-DOMAIN REJECT-HTTP; do
    rule="FORWARD -o tun+ -j $target";
    iptables --check `echo $rule` || iptables -I `echo $rule`;
  done

  # allow a local resolver through the tun device
  allow_local_resolver "stubby"
}

__set_vpn_rules "$@";

unset __whitelist_dst_set;
unset __dns_to_ipset;
unset allow_local_resolver;