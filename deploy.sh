#!/bin/bash

# Production deployment script for SQLAgent

set -e  # Exit on any error

echo "🚀 Starting SQLAgent production deployment..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if required environment files exist
if [ ! -f .env.production ]; then
    echo "❌ .env.production file not found. Please create it from .env.production template."
    exit 1
fi

# Copy production environment
cp .env.production .env

# Create necessary directories
mkdir -p logs ssl

# Install Python dependencies (for local development/testing)
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Redis dependencies
echo "📦 Installing Redis..."
sudo apt-get update
sudo apt-get install -y redis-server

# Start Redis service
echo "🔴 Starting Redis service..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test Redis connection
echo "🧪 Testing Redis connection..."
redis-cli ping

# Set up PostgreSQL (if not using Docker)
echo "🐘 Setting up PostgreSQL..."
sudo apt-get install -y postgresql postgresql-contrib

# Create database and user
sudo -u postgres createuser sqlagent || true
sudo -u postgres createdb sqlagent || true
sudo -u postgres psql -c "ALTER USER sqlagent PASSWORD 'sqlagent_password';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sqlagent TO sqlagent;" || true

# Run database migrations
echo "🗄️ Running database migrations..."
python -c "
import sys
sys.path.append('backend')
from database import engine
import models
models.Base.metadata.create_all(bind=engine)
print('✅ Database tables created successfully')
"

# Test the application
echo "🧪 Testing application startup..."
cd backend
python -c "
import main
print('✅ Application imports successful')
" || {
    echo "❌ Application test failed"
    exit 1
}

cd ..

# Start services with Docker Compose
echo "🐳 Starting services with Docker Compose..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Health check
echo "🏥 Performing health checks..."
curl -f http://localhost:8000/health || {
    echo "❌ Health check failed"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
}

echo "✅ SQLAgent is now running in production mode!"
echo ""
echo "📊 Service Status:"
echo "- API: http://localhost:8000"
echo "- Health Check: http://localhost:8000/health"
echo "- Redis: localhost:6379"
echo "- PostgreSQL: localhost:5432"
echo ""
echo "📝 Logs:"
echo "- API Logs: docker-compose -f docker-compose.prod.yml logs sqlagent_api"
echo "- Redis Logs: docker-compose -f docker-compose.prod.yml logs redis"
echo "- All Logs: docker-compose -f docker-compose.prod.yml logs"
echo ""
echo "🛑 To stop services:"
echo "docker-compose -f docker-compose.prod.yml down"