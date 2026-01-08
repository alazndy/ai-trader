# Base Image
FROM python:3.9-slim

# Set Working Directory
WORKDIR /app

# Install System Dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Requirements
COPY requirements.txt .

# Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Streamlit specific
RUN pip install streamlit

# Copy Project Code
COPY . .

# Expose Port for Cloud Run (Default 8080)
EXPOSE 8080

# Environment Variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Entrypoint: Run the Cloud Launcher Script
# This script will start Streamlit (Web) AND the Bot (Background)
CMD ["python", "cloud_launcher.py"]
