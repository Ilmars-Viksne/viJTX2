#!/bin/bash

# Define a name and tag for your Docker image
IMAGE_NAME="microsam-jetson"
IMAGE_TAG="latest"

echo "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"

# Build the Docker image using the Dockerfile in the current directory
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo "Build complete."