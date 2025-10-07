# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Copy the application code
COPY . .

# Set Python path to include both the app directory and backend directory
ENV PYTHONPATH="/app:/app/backend:$PYTHONPATH"

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Change to backend directory for execution
WORKDIR /app/backend

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application from the backend directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]