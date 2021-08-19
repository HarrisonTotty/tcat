#!/usr/bin/env bash
# Builds the tcat Jupyter Lab environment image.

set -e
trap 'exit 100' INT

if [ ! -f Dockerfile ]; then
    echo 'Please execute this script within the too directory of the tcat repository.'
    exit 1
fi

docker build -t tcatenv:latest .
