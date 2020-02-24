#!/bin/sh

echo iptables -N REJECT-HTTP

echo iptables -A REJECT-HTTP -p tcp --dport 80 -j LOG --log-prefix "[FORWARD:REJECT-HTTP]" --log-level 6;
echo iptables -A REJECT-HTTP -p tcp --dport 80 -j REJECT --reject-with icmp-port-unreachable;
