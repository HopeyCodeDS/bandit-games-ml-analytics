# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install SSL certificates and wget
RUN apt-get update && apt-get install -y \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download the Azure MySQL SSL certificate
RUN wget https://dl.cacerts.digicert.com/DigiCertGlobalRootCA.crt.pem -O /etc/ssl/certs/DigiCertGlobalRootCA.crt.pem \
    && chmod 644 /etc/ssl/certs/DigiCertGlobalRootCA.crt.pem

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the consumer
CMD ["python", "analytics_consumer.py"]