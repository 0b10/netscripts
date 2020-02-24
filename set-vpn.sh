#!/bin/sh

function __set_vpn_rules() {
  [[ -z $IRC_HOST_IP ]] && echo "you must set IRC_HOST_IP first, via the env" && return 1;
  [[ -z $MATRIX_HOST_IP ]] && echo "you must set MATRIX_HOST_IP first,  via the env" && return 1;

  local CWD=`dirname $0`;
  source "${CWD}/whitelist-dst-set.sh";

  # allow IRC dst hosts: $1:chain_name $2:ipset_name
  __whitelist_dst_set "WHITELIST-DST-IRC" "irc-whitelist";
  echo iptables -I FORWARD -s $IRC_HOST_IP -j WHITELIST-DST-IRC;

  # allow Matrix dst hosts: $1:chain_name $2:ipset_name
  __whitelist_dst_set "WHITELIST-DST-MATRIX" "matrix-whitelist";
  echo iptables -I FORWARD -s $MATRIX_HOST_IP -j WHITELIST-DST-MATRIX;

}

__set_vpn_rules "$@";

unset __whitelist_dst_set;