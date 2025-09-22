# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create and activate virtual environment, then install dependencies
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make start script executable if it exists
RUN if [ -f start.sh ]; then chmod +x start.sh; fi

# Expose port
EXPOSE 8080

# Run the application
CMD ["./start.sh"]