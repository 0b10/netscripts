#!/bin/sh
# Allow the local resolver to make connections out, and receive packets back.
# Outgoing connections are constrained to the provided GID, but incomming packets
#  are only constrained by their state - RELATED,ESTABLISHED.

function __allow_local_resolver_egress() {
  # the resolver should be allowed to make a request
  local resolver_gid=$1

  local rule="OUTPUT -o tun+ --proto tcp --dport 853 -m owner --gid-owner $resolver_gid -j ACCEPT";
  iptables --check `echo $rule` || iptables -I `echo $rule`;
}

function __remove_drop_all_ingress() {
  # the resolver needs replies, this rull is inserted via the qubes-vpn-handler script
  local rule="INPUT -i tun+ -j DROP";
  iptables --check `echo $rule` && iptables -D `echo $rule`;
}

function __allow_established_ingress() {
  # the local resolver needs replies, but this rule will probably already exist
  local rule="INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT"
  iptables --check `echo $rule` || iptables -I `echo $rule`
}

function __set_default_input_policy() {
  # just in case it doesn't exist already
  iptables -P INPUT DROP
}

# ! USE THIS FUNCTION
function allow_local_resolver() {
  [[ -z $1 ]] && echo "you must provide a resolver gid for -m owned" && return 1;
  local resolver_gid=$1

  __allow_local_resolver_egress $resolver_gid
  __set_default_input_policy
  __allow_established_ingress
  __remove_drop_all_ingress
}
