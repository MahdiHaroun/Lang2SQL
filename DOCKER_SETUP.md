# Docker Setup Guide for SQLAgent

This guide will help you set up and run the SQLAgent application using Docker and Docker Compose.

## Prerequisites

1. **Docker**: Install Docker on your system
   - Linux: `sudo apt-get install docker.io docker-compose-plugin`
   - macOS: Download Docker Desktop from https://docker.com
   - Windows: Download Docker Desktop from https://docker.com

2. **Docker Compose**: Usually comes with Docker Desktop, or install separately:
   - Linux: `sudo apt-get install docker-compose`

## Quick Start

### 1. Clone and Navigate to the Project
```bash
cd /home/mahdi/projects/SQLAgent
```

### 2. Create Environment File
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your actual configuration
nano .env
```

**Important**: Update the following values in your `.env` file:
- `GROQ_API_KEY`: Your Groq API key for LLM functionality
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`: Your Google OAuth credentials
- `SECRET_KEY`: Generate a secure random key for JWT tokens
- Other API keys as needed

### 3. Build and Start Services
```bash
# Build and start all services in detached mode
docker-compose up -d --build
```

### 4. Verify Services are Running
```bash
# Check the status of all containers
docker-compose ps

# View logs for all services
docker-compose logs

# View logs for a specific service
docker-compose logs sqlagent
docker-compose logs postgres
docker-compose logs redis
```

## Service URLs

Once running, you can access:

- **SQLAgent API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Redis Commander UI**: http://localhost:8081 (Redis management interface)

## Docker Commands

### Starting Services
```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis
```

### Stopping Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: This will delete your data!)
docker-compose down -v
```

### Viewing Logs
```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f sqlagent

# View last 100 lines of logs
docker-compose logs --tail=100 sqlagent
```

### Accessing Containers
```bash
# Execute commands in the SQLAgent container
docker-compose exec sqlagent bash

# Access PostgreSQL CLI
docker-compose exec postgres psql -U sqlagent_user -d sqlagent_db

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Rebuilding Services
```bash
# Rebuild and restart a specific service
docker-compose up -d --build sqlagent

# Rebuild all services
docker-compose up -d --build
```

## Development Workflow

### 1. Making Code Changes
When you make changes to your code:
```bash
# Rebuild and restart the SQLAgent service
docker-compose up -d --build sqlagent
```

### 2. Database Management
```bash
# View database logs
docker-compose logs postgres

# Backup database
docker-compose exec postgres pg_dump -U sqlagent_user sqlagent_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U sqlagent_user -d sqlagent_db < backup.sql
```

### 3. Redis Management
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# View Redis info
docker-compose exec redis redis-cli INFO
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   sudo lsof -i :8000
   
   # Stop the conflicting service or change ports in docker-compose.yml
   ```

2. **Permission Errors**
   ```bash
   # Add your user to docker group (Linux)
   sudo usermod -aG docker $USER
   # Then log out and log back in
   ```

3. **Container Won't Start**
   ```bash
   # Check detailed logs
   docker-compose logs sqlagent
   
   # Check container status
   docker-compose ps
   ```

4. **Database Connection Issues**
   ```bash
   # Check if PostgreSQL is running
   docker-compose logs postgres
   
   # Test connection from SQLAgent container
   docker-compose exec sqlagent ping postgres
   ```

### Reset Everything
If you need to start fresh:
```bash
# Stop all services and remove containers, networks, and volumes
docker-compose down -v

# Remove unused Docker resources
docker system prune -f

# Rebuild everything
docker-compose up -d --build
```

## Production Deployment

For production deployment:

1. **Update Environment Variables**:
   - Use strong, unique passwords
   - Set proper secret keys
   - Configure production database URLs

2. **Enable HTTPS**:
   - Add SSL certificates
   - Configure reverse proxy (nginx)

3. **Security**:
   - Remove development services (redis-commander)
   - Use Docker secrets for sensitive data
   - Enable firewall rules

4. **Monitoring**:
   - Add health checks
   - Configure log aggregation
   - Set up monitoring tools

## Additional Commands

### Scaling Services
```bash
# Scale SQLAgent to 3 instances
docker-compose up -d --scale sqlagent=3
```

### Resource Usage
```bash
# View resource usage
docker stats

# View specific container usage
docker stats sqlagent_container_name
```

### Cleanup
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune
```

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Verify environment variables in `.env`
3. Ensure all required ports are available
4. Check Docker and Docker Compose versions