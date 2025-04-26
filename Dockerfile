# Use the official Python image from the Docker Hub
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install uv to handle the build process
RUN pip install --no-cache-dir uv

# Default command
CMD ["python", "src/file_downloader/main.py"]
