#!/usr/bin/env bash
# A handy script for building a docker image bundled with this project.

set -e

trap 'exit 100' INT

VERSION=$(grep -oP '^version\s*=\s*"\d+\.\d+\.\d+"$' pyproject.toml | awk -F '"' '{ print $2 }')

docker build -t "docker.totty.dev/tcat:${VERSION}" .
