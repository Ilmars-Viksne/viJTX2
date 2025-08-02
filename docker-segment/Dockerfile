# Use an official NVIDIA L4T PyTorch base image suitable for Jetson TX2 (JetPack 4.6)
# This image includes CUDA, cuDNN, TensorRT, and PyTorch.
FROM nvcr.io/nvidia/l4t-pytorch:r32.7.1-pth1.10-py3

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required by OpenCV for displaying images
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir micro-sam opencv-python scikit-image tqdm

# Copy the modified Python script into the container's working directory
COPY segment_and_track.py .

# Create mount points for data
RUN mkdir /input /output

# Command to execute when the container starts
ENTRYPOINT ["python3", "segment_and_track.py"]