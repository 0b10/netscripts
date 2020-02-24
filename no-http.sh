#!/bin/sh

echo iptables -N NO-HTTP
echo iptables -I FORWARD -j NO-HTTP

echo iptables -A NO-HTTP -p tcp --dport 80 -j LOG --log-prefix "[FORWARD:HTTP]" --log-level 6;
echo iptables -A NO-HTTP -p tcp --dport 80 -j REJECT --reject-with icmp-port-unreachable;
