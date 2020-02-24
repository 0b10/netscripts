#!/bin/sh

echo iptables -N DNS
echo iptables -I FORWARD -j DNS

for proto in tcp udp; do
  echo iptables -I FORWARD -p $proto --dport 53 -j LOG --log-prefix "[FORWARD:DNS]" --log-level 6;
  echo iptables -I FORWARD -p $proto --dport 53 -j REJECT --reject-with icmp-port-unreachable
done