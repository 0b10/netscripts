#!/bin/sh

function __set_vpn_rules() {
  local cwd=`dirname $0`;

  source "${cwd}/whitelist-dst-set.sh";
  config="${cwd}/get-config.py"
  get_config="python3 ${cwd}/get-config.py"

  # whitelist dst hosts
  names=`$get_config --get-names`;
  for name in ${names[@]}; do
    src=`$get_config --get-src $name`;
    ipset_name=`$get_config --get-white-ipset $name`;

    __whitelist_dst_set $name $ipset_name;  # $1:chain_name $2:ipset_name
    echo iptables -I FORWARD -i vif+ -o tun+ -s $src -j $name;
  done
}

__set_vpn_rules "$@";

unset __whitelist_dst_set;
unset __dns_to_ipset;
unset IRC_WHITELIST_DOMAINS;
unset IRC_HOST_IP;
unset MATRIX_HOST_IP;