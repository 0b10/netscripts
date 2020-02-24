#!/bin/sh

function __set_vpn_rules() {
  local CWD=`dirname $0`;

  source "${CWD}/config.sh";
  source "${CWD}/dns-to-ipset.sh";
  source "${CWD}/whitelist-dst-set.sh";

  [[ -z $IRC_HOST_IP ]] && echo "you must set IRC_HOST_IP first, via the config" && return 1;
  [[ -z $MATRIX_HOST_IP ]] && echo "you must set MATRIX_HOST_IP first,  via the config" && return 1;

  # for domain in "${IRC_WHITELIST_DOMAINS[@]}"; do
    # echo $domain
  # done
  __dns_to_ipset "${IRC_WHITELIST_DOMAINS[@]}"

  # allow IRC dst hosts: $1:chain_name $2:ipset_name
  __whitelist_dst_set "WHITELIST-DST-IRC" "irc-whitelist";
  echo iptables -I FORWARD -s $IRC_HOST_IP -j WHITELIST-DST-IRC;

  # allow Matrix dst hosts: $1:chain_name $2:ipset_name
  __whitelist_dst_set "WHITELIST-DST-MATRIX" "matrix-whitelist";
  echo iptables -I FORWARD -s $MATRIX_HOST_IP -j WHITELIST-DST-MATRIX;

}

__set_vpn_rules "$@";

unset __whitelist_dst_set;
unset __dns_to_ipset;
unset IRC_WHITELIST_DOMAINS;
unset IRC_HOST_IP;
unset MATRIX_HOST_IP;