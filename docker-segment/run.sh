#!/bin/bash

# The name of the image you built with build.sh
IMAGE_NAME="microsam-jetson:latest"

# Define the local directories for input and output
# IMPORTANT: Replace these paths with the actual paths on your machine
HOST_INPUT_DIR="${HOME}/microsam_files/input"
HOST_OUTPUT_DIR="${HOME}/microsam_files/output"

# Create the directories on the host if they don't exist
echo "Ensuring host directories exist..."
mkdir -p "${HOST_INPUT_DIR}"
mkdir -p "${HOST_OUTPUT_DIR}"
echo "Host Input:  ${HOST_INPUT_DIR}"
echo "Host Output: ${HOST_OUTPUT_DIR}"
echo ""

# Allow the container to connect to the host's X server for GUI display
xhost +

# Run the Docker container
echo "Starting container. The Python script will launch automatically."
echo "Place your images in '${HOST_INPUT_DIR}'."
echo "Results will be saved to '${HOST_OUTPUT_DIR}'."
echo "---------------------------------------------------"

docker run -it --rm \
    --runtime nvidia \
    --network host \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix/:/tmp/.X11-unix \
    -v "${HOST_INPUT_DIR}":/input \
    -v "${HOST_OUTPUT_DIR}":/output \
    "${IMAGE_NAME}"

# Revoke the X server access permission
xhost -

echo "---------------------------------------------------"
echo "Container stopped."