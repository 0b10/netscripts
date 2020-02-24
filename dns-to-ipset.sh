#!/bin/sh

function __dns_to_ipset() {
  echo "${@}"
  local arr=("$@")
  for domain in "$@";
    do echo domain;
  done;
}

