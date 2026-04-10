# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (swaks)
RUN apt-get update && apt-get install -y swaks && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code
COPY . .

# Make the wrapper script executable
RUN chmod +x run_forever.sh

# Define the command to run your application
#CMD python3 test.py
CMD ["tail", "-f", "/dev/null"]
