#!/bin/sh

TABLE_NAME="REJECT-DOMAIN"

iptables -N $TABLE_NAME || iptables -F $TABLE_NAME

for proto in tcp udp; do
  iptables -I $TABLE_NAME -p $proto --dport 53 -j LOG --log-prefix "[FORWARD:${TABLE_NAME}]" --log-level 6;
  iptables -I $TABLE_NAME -p $proto --dport 53 -j REJECT --reject-with icmp-port-unreachable
done