# Use Node.js base image with Python (multi-stage build alternative)
# This is often cached on cloud platforms and avoids Docker Hub issues
FROM node:18-bullseye

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-venv \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

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
CMD ["gunicorn", "frontend.app:app", "--bind", "0.0.0.0:8080", "--workers", "1", "--log-level", "info"]