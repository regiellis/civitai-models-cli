@echo off
setlocal enabledelayedexpansion

REM Build the Docker image
docker build -t civitai-models-manager .

REM Run the Docker container with the specified arguments
docker run -it --rm ^
    --cap-drop=ALL ^
    -v %cd%:/home/civitaiuser ^
    -v %cd%/docker:/home/civitaiuser/docker:ro ^
    -v \\.\pipe\docker_engine:/var/run/docker.sock ^
    --name running-civitai-models-manager civitai-models-manager %* && ^
    docker exec -it running-civitai-models-manager pip install .

pause