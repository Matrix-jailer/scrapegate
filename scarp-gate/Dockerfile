# Use Python 3.11 slim for compatibility
FROM python:3.11-slim

# Install system dependencies for Scrapy, pyOpenSSL, and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl-dev \
    libffi-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy script
COPY scrapgate.py .

# Set environment variable for unbuffered Python output
ENV PYTHONUNBUFFERED=1

# Run the script
CMD ["python", "scrapgate.py"]
