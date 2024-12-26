FROM python:3.9-slim

LABEL authors="Opeyemi Momodu"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create models directory and ensure it exists
RUN mkdir -p models

# Copy model files
COPY models/*.pkl models/

# Expose the port the app runs on
EXPOSE 8002

# Command to run the application
CMD ["uvicorn", "unified_prediction_api:app", "--host", "0.0.0.0", "--port", "8002"]