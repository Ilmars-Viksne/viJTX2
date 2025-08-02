# Dockerized Micro-SAM for Jetson TX2

This project provides a Docker-based solution for running a Python segmentation script using `micro-sam` on an NVIDIA Jetson TX2.

It separates the build and run processes, and ensures that all input and output files are stored on your host machine, not inside the container.

## File Structure

Place all the following files in the same directory:

```
.
├── Dockerfile
├── build.sh
├── run.sh
├── segment_and_track.py
└── README.md```

## Prerequisites

1.  A Jetson TX2 with NVIDIA JetPack 4.6.x installed.
2.  Docker installed and configured on the Jetson.
3.  An internet connection to download the base image and dependencies.

## Step 1: Set Up Host Directories

The container is designed to read from and write to specific directories on your host machine.

1.  **Create the main folder:**
    ```bash
    mkdir -p ~/microsam_files/input
    mkdir -p ~/microsam_files/output
    ```

2.  **Place your data:**
    *   Put your source images (e.g., `my_image.jpg`) or folders of images (e.g., `tracking_frames/`) inside `~/microsam_files/input`.

The `run.sh` script is pre-configured to use these paths. If you wish to use different paths, you **must** edit the `HOST_INPUT_DIR` and `HOST_OUTPUT_DIR` variables in `run.sh`.

## Step 2: Build the Docker Image

This step bundles the script and its dependencies into a reusable image. You only need to do this once (or whenever you change the `Dockerfile` or Python script).

1.  **Make the build script executable:**
    ```bash
    chmod +x build.sh
    ```

2.  **Run the build script:**
    ```bash
    ./build.sh
    ```
    This process will take some time as it downloads the base image and installs all the required libraries.

## Step 3: Run the Application

This step launches the container from the image you just built.

1.  **Make the run script executable:**
    ```bash
    chmod +x run.sh
    ```

2.  **Execute the script:**
    ```bash
    ./run.sh
    ```

### How It Works

*   The script will start the container, which automatically executes the `segment_and_track.py` script.
*   Your `~/microsam_files/input` directory is mapped to the `/input` directory inside the container.
*   Your `~/microsam_files/output` directory is mapped to the `/output` directory inside the container.
*   **When the script prompts you for a file or folder name, provide the name relative to the `/input` directory.**
    *   If your image is at `~/microsam_files/input/cat.jpg`, you should enter `cat.jpg` at the prompt.
    *   If your frames are in `~/microsam_files/input/race_car_frames/`, you should enter `race_car_frames` at the prompt.
*   Any GUI windows (like from `cv2.imshow`) will appear on your Jetson's desktop.
*   Output files will appear in your `~/microsam_files/output` directory.
*   Once you quit the Python script, the container will automatically stop and be removed.