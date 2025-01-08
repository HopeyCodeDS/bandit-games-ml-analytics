# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install SSL certificates
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY analytics_consumer.py .
COPY analytics_test.py .
COPY cleanup_rabbitmq.py .
COPY test_publisher.py .
COPY test_queries.py .

# Run the consumer
CMD ["python", "analytics_consumer.py"]