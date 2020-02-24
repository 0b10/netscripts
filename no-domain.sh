#!/bin/sh

echo iptables -N NO-DOMAIN
echo iptables -I FORWARD -j NO-DOMAIN

for proto in tcp udp; do
  echo iptables -I FORWARD -p $proto --dport 53 -j LOG --log-prefix "[FORWARD:NO-DOMAIN]" --log-level 6;
  echo iptables -I FORWARD -p $proto --dport 53 -j REJECT --reject-with icmp-port-unreachable
done