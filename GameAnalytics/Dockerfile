FROM python:3.9-slim

WORKDIR /app

# Install system dependencies and SSL certificates
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API file
COPY player_statistics_API_new.py ./main.py

# Create .env file with environment variables
# Note: These will be overridden by the container app environment variables
RUN echo "DB_USER=root" >> .env && \
    echo "DB_PASSWORD=root" >> .env && \
    echo "DB_HOST=platform_analytics_mysql" >> .env && \
    echo "DB_PORT=3306" >> .env && \
    echo "SSL_CA=/etc/ssl/certs/ca-certificates.crt" >> .env  # Add SSL cert path

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]