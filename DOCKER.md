# 🐳 Docker Deployment Guide

Complete guide for running ALSS using Docker and Docker Compose.

## 📋 Prerequisites

- **Docker** 20.10+ installed
- **Docker Compose** 2.0+ installed
- **Git** (for cloning the repository)

## 🚀 Quick Start with Docker

### 1️⃣ Clone the Repository

```bash
git clone <your-repo-url>
cd ALSS_web2
```

### 2️⃣ Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Important:** Generate secure keys for production:

```bash
# Generate SECRET_KEY and JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3️⃣ Build and Run with Docker Compose

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check container status
docker-compose ps
```

### 4️⃣ Initialize Database

```bash
# Access the container
docker-compose exec web bash

# Inside container: Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Create admin user (if script exists)
python create_admin.py

# Exit container
exit
```

### 5️⃣ Access the Application

Open your browser to:
- **Application**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin/dashboard

---

## 🔧 Docker Commands Reference

### Building & Starting

```bash
# Build images
docker-compose build

# Start containers in background
docker-compose up -d

# Start with rebuild
docker-compose up -d --build

# Start and view logs
docker-compose up
```

### Stopping & Removing

```bash
# Stop containers
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop, remove containers and volumes (⚠️ DELETES DATA!)
docker-compose down -v
```

### Viewing Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs -f web

# View last 100 lines
docker-compose logs --tail=100
```

### Container Management

```bash
# List running containers
docker-compose ps

# Access container shell
docker-compose exec web bash

# Run one-off command
docker-compose exec web flask routes

# Restart specific service
docker-compose restart web
```

---

## 🗃️ Database Management

### Backup Database

```bash
# Create backup directory
mkdir -p backups

# Backup SQLite database
docker-compose exec web cp /app/database/alss.db /app/database/alss_backup.db
docker cp alss_web:/app/database/alss_backup.db ./backups/alss_$(date +%Y%m%d_%H%M%S).db
```

### Restore Database

```bash
# Stop the application
docker-compose stop web

# Restore database
docker cp ./backups/alss_20260210_123000.db alss_web:/app/database/alss.db

# Start the application
docker-compose start web
```

### Reset Database

```bash
docker-compose exec web flask db downgrade base
docker-compose exec web flask db upgrade
```

---

## 🔒 Production Deployment

### Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Generate unique ENCRYPTION_KEY
- [ ] Set FLASK_ENV=production
- [ ] Enable HTTPS (use nginx reverse proxy)
- [ ] Configure firewall rules
- [ ] Set up regular database backups
- [ ] Enable audit logging
- [ ] Review and limit exposed ports

### Using Nginx Reverse Proxy

Uncomment the nginx service in `docker-compose.yml` and create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream flask_app {
        server web:5000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://flask_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Enable HTTPS with Let's Encrypt

```bash
# Install certbot
docker-compose exec nginx apk add certbot

# Generate certificate
docker-compose exec nginx certbot certonly --webroot -w /var/www/html -d your-domain.com
```

---

## 🔄 Updates & Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Run migrations if needed
docker-compose exec web flask db upgrade
```

### View Resource Usage

```bash
# Container stats
docker stats alss_web

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs web

# Check if port is already in use
netstat -an | grep 5000  # Linux/Mac
netstat -an | findstr 5000  # Windows

# Use different port
# Edit docker-compose.yml: ports: - "5001:5000"
```

### Database Permission Issues

```bash
# Fix permissions
docker-compose exec web chown -R alss:alss /app/database
docker-compose restart web
```

### Out of Memory

```bash
# Check container memory
docker stats alss_web

# Increase memory limit in docker-compose.yml
# Add under web service:
#   deploy:
#     resources:
#       limits:
#         memory: 1G
```

### Health Check Failing

```bash
# Test health endpoint manually
docker-compose exec web curl http://localhost:5000/health

# Check application logs
docker-compose logs web --tail=50
```

---

## 📊 Monitoring

### View Application Metrics

```bash
# CPU and Memory usage
docker stats alss_web

# Container processes
docker-compose exec web ps aux

# Disk usage
docker-compose exec web df -h
```

### Health Checks

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' alss_web

# View health check logs
docker inspect --format='{{json .State.Health}}' alss_web | jq
```

---

## 🧪 Development with Docker

### Development Mode

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
    volumes:
      - .:/app  # Mount source code for live reload
    command: flask run --host=0.0.0.0
```

Run in development mode:

```bash
docker-compose -f docker-compose.dev.yml up
```

---

## 📖 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask in Docker Best Practices](https://flask.palletsprojects.com/en/latest/deploying/)

---

## 💡 Pro Tips

- 🔄 **Regular backups**: Automate daily database backups
- 📊 **Monitoring**: Set up monitoring with Prometheus/Grafana
- 🔒 **Secrets management**: Use Docker secrets for sensitive data
- 🚀 **CI/CD**: Integrate with GitHub Actions for automated deployment
- 📈 **Scaling**: Use Docker Swarm or Kubernetes for multi-instance deployment

---

**Your ALSS application is now containerized! 🎉**
