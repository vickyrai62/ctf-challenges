# Production-Grade CTF Platform - Docker Deployment

## 🐳 Docker Configuration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements_final_spec.txt .
RUN pip install --no-cache-dir -r requirements_final_spec.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 ctfuser && chown -R ctfuser:ctfuser /app
USER ctfuser

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "run_final_spec:app"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=your-production-secret-key
      - DATABASE_URL=postgresql://ctfuser:ctfpass@db:5432/ctfplatform
      - REDIS_URL=redis://redis:6379
      - FLASK_DEBUG=False
    depends_on:
      - db
      - redis
    volumes:
      - ./instance:/app/instance

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ctfplatform
      - POSTGRES_USER=ctfuser
      - POSTGRES_PASSWORD=ctfpass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

## 🚀 Deployment Commands

### Development
```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f web
```

### Production
```bash
# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale web service
docker-compose up -d --scale web=3
```

## 🔧 Environment Configuration

### Production Environment Variables
```bash
# Security
SECRET_KEY=your-very-long-and-secure-secret-key-here
FLASK_DEBUG=False

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/ctfplatform

# Redis
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/ctf-platform.log
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Monitoring & Logging

### Health Check Endpoint
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
```

### Logging Configuration
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/ctf-platform.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
```

## 🔒 Security Hardening

### Security Headers
```python
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### Rate Limiting
```python
# Global rate limiting
@limiter.limit("100 per hour")
def protected_endpoint():
    pass

# User-specific rate limiting
@limiter.limit("10 per minute", key_func=lambda: f"user_{current_user.id}")
def user_endpoint():
    pass
```

## 📈 Performance Optimization

### Database Indexing
```sql
-- Important indexes for performance
CREATE INDEX idx_challenges_level_active ON challenges(level, is_active);
CREATE INDEX idx_submissions_user_challenge ON submissions(user_id, challenge_id);
CREATE INDEX idx_submissions_correct ON submissions(is_correct) WHERE is_correct = TRUE;
CREATE INDEX idx_users_score ON users(score DESC);
```

### Caching Strategy
```python
# Redis caching for leaderboard
def get_leaderboard():
    cache_key = "leaderboard:all"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Generate fresh leaderboard
    leaderboard = generate_leaderboard()
    redis_client.setex(cache_key, 300, json.dumps(leaderboard))
    return leaderboard
```

## 🔄 Backup Strategy

### Database Backup
```bash
# Daily backup
0 2 * * * pg_dump -U ctfuser ctfplatform > /backups/ctf_$(date +\%Y\%m\%d).sql

# Weekly backup
0 3 * * 0 pg_dump -U ctfuser ctfplatform > /backups/ctf_weekly_$(date +\%Y\%m\%d).sql
```

### Application Backup
```bash
# Backup application files
tar -czf /backups/app_$(date +\%Y\%m\%d).tar.gz /app/ctf-platform/
```

## 🚨 Monitoring Alerts

### Health Monitoring
```python
def check_system_health():
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    return all(checks.values()), checks
```

### Alert Configuration
```yaml
# Prometheus alerts
groups:
  - name: ctf-platform
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
```

This Docker configuration provides a complete production-ready deployment setup for your CTF platform with proper security, monitoring, and scalability considerations.
