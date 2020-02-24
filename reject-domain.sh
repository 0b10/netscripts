#!/bin/sh

echo iptables -N REJECT-DOMAIN

for proto in tcp udp; do
  echo iptables -I REJECT-DOMAIN -p $proto --dport 53 -j LOG --log-prefix "[FORWARD:REJECT-DOMAIN]" --log-level 6;
  echo iptables -I REJECT-DOMAIN -p $proto --dport 53 -j REJECT --reject-with icmp-port-unreachable
done