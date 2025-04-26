# Use the official Python image from the Docker Hub
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run uv when the container launches
CMD ["python", "src/wafflebot/main.py"]
