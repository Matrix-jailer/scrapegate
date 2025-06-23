# Use Python 3.11 for compatibility
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy script and requirements
COPY scrapgate.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Telegram bot (if needed)
EXPOSE 8080

# Run the script
CMD ["python", "scrapgate.py"]