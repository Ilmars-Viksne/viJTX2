# Jetson Video Slicer in Docker

This project provides a Dockerized Python application to split a video file into individual frames. It is specifically designed to run on an **NVIDIA Jetson TX2** and leverages Docker to create a self-contained, portable environment.

The application displays each frame in a GUI window and allows the user to interrupt the process at any time by pressing the 'q' key.

## Features

-   **Video to Frames**: Splits any standard video format (e.g., MP4, AVI) into a sequence of JPEG images.
-   **Interactive**: The script runs in the console and prompts the user for input.
-   **GUI Feedback**: Displays each frame in a window as it is being processed.
-   **Interruptible**: The user can stop the process cleanly at any point by pressing 'q' or 'Q' on the video window.
-   **Dockerized for Jetson**: Uses an NVIDIA L4T base image to ensure compatibility with the Jetson hardware and display.
-   **Portable**: All dependencies are managed within the Docker container.

## Prerequisites

-   **Hardware**: An NVIDIA Jetson TX2 Developer Kit.
-   **Software**:
    -   [NVIDIA JetPack](https://developer.nvidia.com/embedded/jetpack) installed on the Jetson TX2.
    -   [Docker](https://docs.docker.com/engine/install/ubuntu/) installed and running on the Jetson.

## Project Structure

The project should be organized with the following structure:

```
jetson-video-slicer/
├── Dockerfile
└── video_slicer.py
```

## Setup and Installation

Follow these steps on your Jetson TX2 terminal to set up and build the application.

### Step 1: Get the Project Files

Clone this repository or manually create the `jetson-video-slicer` directory and place the `Dockerfile` and `video_slicer.py` files inside it.

```bash
# Example of cloning a repository
# git clone <your-repo-url>
# cd jetson-video-slicer
```

### Step 2: Create Host Directories for Data

The Docker container is designed to work with shared folders on your host machine. This allows you to easily pass video files to the container and retrieve the output frames.

```bash
# Create directories in your home folder
mkdir -p ~/video_slicer_app/videos
mkdir -p ~/video_slicer_app/frames
```

-   `~/video_slicer_app/videos`: Place the videos you want to process in this folder.
-   `~/video_slicer_app/frames`: The script will save the output frames here.

### Step 3: Place a Video File

Copy a video file you want to process into the `videos` directory you just created.

```bash
# Example:
cp /path/to/your/sample.mp4 ~/video_slicer_app/videos/
```

### Step 4: Build the Docker Image

Navigate to the project's root directory (`jetson-video-slicer`) and run the `docker build` command. This will create a Docker image named `video-slicer-app`.

```bash
# Make sure you are in the directory containing the Dockerfile
docker build -t video-slicer-app .
```

> **Note on the Dockerfile:** The `Dockerfile` installs OpenCV using `apt-get install python3-opencv` instead of `pip install opencv-python`. This is a faster and more reliable method on the Jetson platform, as it uses a pre-compiled version of the library. If you are using a different version of JetPack/L4T, you may need to update the `FROM` instruction tag. You can find your L4T version by running `cat /etc/nv_tegra_release` and find corresponding tags on [NVIDIA's NGC catalog](https://ngc.nvidia.com/catalog/containers/nvidia:l4t-base).

## How to Run the Application

### Step 1: Authorize Display Access

To allow the Docker container to open a GUI window on your Jetson's desktop, you must grant it access to the host's X server.

```bash
# Run this command once per session before starting the container
sudo xhost +si:localuser:root
```

### Step 2: Run the Docker Container

Execute the following command to start the container. It maps the shared directories and display settings, allowing the application to run correctly.

```bash
docker run -it --rm \
    --runtime nvidia \
    -v ~/video_slicer_app/videos:/app/videos \
    -v ~/video_slicer_app/frames:/app/frames \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    video-slicer-app
```

### Command Flags Explained

-   `--runtime nvidia`: **Crucial for Jetson.** Enables access to the NVIDIA GPU and hardware.
-   `-v ...:/app/...`: Maps your host directories (`~/video_slicer_app/...`) to the directories inside the container (`/app/...`).
-   `-v /tmp/.X11-unix...`: Mounts the X11 socket required for GUI applications.
-   `-e DISPLAY=$DISPLAY`: Passes your host's display variable to the container.
-   `-it --rm`: Runs the container in interactive mode and automatically removes it on exit.

## How to Use the Application

Once the container is running:

1.  The script will start automatically and prompt you in the terminal:
    ```
    --- Video Slicer Docker App ---
    Place your videos in the host directory mapped to /app/videos
    Frames will be saved in the host directory mapped to /app/frames

    Enter the filename of the video (must be in the 'videos' folder):
    ```
2.  Type the name of the video file you placed in the `videos` folder (e.g., `sample.mp4`) and press Enter.
3.  A window titled **"Video Frame"** will appear on your desktop, showing the frames being processed.
4.  To **stop the process**, click on the "Video Frame" window to make it active and press the **`q`** or **`Q`** key.
5.  When the process is finished or interrupted, the output frames will be available in a new subfolder inside your `~/video_slicer_app/frames` directory. For example, for `sample.mp4`, the frames will be in `~/video_slicer_app/frames/sample/`.
