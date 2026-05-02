#!/usr/bin/env bash

# BASH STRICT MODE
set -o errexit # abort on nonzero exitstatus
set -o nounset # abort on unbound variable
set -o pipefail

IMAGE_NAME=bi-builder
CONTAINER_NAME="${IMAGE_NAME}"

function cleanup() (
    SCRIPT_STATUS=$?

    set +o errexit # do NOT abort on nonzero exitstatus

    echo 'Cleaning up docker image and container...'
    docker image rm "${IMAGE_NAME}" &>/dev/null
    docker kill "${CONTAINER_NAME}" &>/dev/null
    docker container rm "${CONTAINER_NAME}" &>/dev/null

    if [ "$SCRIPT_STATUS" -eq 0 ]; then
        echo 'bi successfully built! output files are in the dist/ dir'
    else
        echo 'bi failed to be built! please read previous output for debugging'
    fi
)

# Make sure the image and container are removed whether or not the script succeeded
trap cleanup EXIT

docker buildx build -t "$IMAGE_NAME" .
docker run -dit --name="${CONTAINER_NAME}" "${IMAGE_NAME}" sh
docker cp "${CONTAINER_NAME}":/tmp/dist/ .
