#!/bin/sh

TABLE_NAME="REJECT-HTTP";

iptables -N $TABLE_NAME || iptables -F $TABLE_NAME

iptables -A $TABLE_NAME -p tcp --dport 80 -j LOG --log-prefix "[FORWARD:${TABLE_NAME}]" --log-level 6;
iptables -A $TABLE_NAME -p tcp --dport 80 -j REJECT --reject-with icmp-port-unreachable;
