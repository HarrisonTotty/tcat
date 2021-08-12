#!/usr/bin/env bash
# Runs an instance of the tcat jupyter environment image.

set -e
trap 'exit 100' INT

if [ "$#" -ne 1 ]; then
    echo 'USAGE: ./run.sh <working directory>'
    echo 'EXAMPLE: ./run.sh "${HOME}/projects/tcat-private"'
    exit 0
fi

working_dir="$1"

if [ ! -f Dockerfile ]; then
    echo 'Please execute this script within the too directory of the tcat repository.'
    exit 1
fi

docker build -t tcatenv:latest .

docker run \
    --rm \
    -p 8888:8888 \
    -v "${working_dir}:/home/jovyan/work" \
    tcatenv:latest start.sh jupyter lab --LabApp.token=''
