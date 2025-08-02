# Dockerfile

# Use an official NVIDIA L4T base image that matches your JetPack version.
# Find the right tag for your Jetson TX2's L4T version by running:
# cat /etc/nv_tegra_release
# For example, if it shows R32 (release), T7 (Jahwoo), REVISION: 7.1, use r32.7.1
# See available tags here: https://ngc.nvidia.com/catalog/containers/nvidia:l4t-base
FROM nvcr.io/nvidia/l4t-base:r32.7.1

# Set the working directory in the container
WORKDIR /app

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python3, pip, and essential libraries for OpenCV.
# Instead of using pip for opencv, we install the pre-compiled Ubuntu package 'python3-opencv'.
# This is much faster and more reliable on ARM platforms like Jetson.
RUN apt-get update && \
    apt-get install -y \
    python3-pip \
    python3-opencv \
    libgl1-mesa-glx \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Copy the Python script into the container's working directory
COPY video_slicer.py .

# This command will be executed when the container starts
CMD ["python3", "video_slicer.py"]
