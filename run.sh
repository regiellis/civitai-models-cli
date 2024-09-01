#!/bin/bash
set -e

docker build -t "civitai-models-manager" .
docker run -it --rm \
    --cap-drop=ALL \
    -v "$(pwd):/home/civitaiuser" \
    -v "$(pwd)/docker:/home/civitaiuser/docker:ro" \
    -v "/var/run/docker.sock:/var/run/docker.sock" \
    --name running-civitai-models-manager "civitai-models-manager" "$@" && \
    docker exec -it running-civitai-models-manager pip install .
