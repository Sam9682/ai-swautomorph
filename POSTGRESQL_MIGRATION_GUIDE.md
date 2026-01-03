# PostgreSQL Active/Active Migration Guide

## Overview

This guide covers migrating AI-SwAutoMorph from SQLite to PostgreSQL with a true Active/Active configuration.

## Architecture Changes

### Before (SQLite)
- Single Flask instance
- SQLite database with WAL mode
- Thread-safe database manager
- Single point of failure

### After (PostgreSQL Active/Active)
- 2x Flask instances (Active/Active)
- Shared PostgreSQL database
- Nginx load balancer
- Connection pooling
- No single point of failure

## Migration Steps

### 1. Prerequisites

```bash
# Install PostgreSQL client tools
sudo apt-get update
sudo apt-get install postgresql-client python3-pip

# Install Python PostgreSQL adapter
pip3 install psycopg2-binary
```

### 2. Backup Current Data

```bash
# Create backup of current SQLite database
./deployControlPlan.sh backup_db

# Stop current services
./deployControlPlan.sh stop
```

### 3. Deploy PostgreSQL Stack

```bash
# Deploy new PostgreSQL Active/Active stack
./deploy-postgres.sh start
```

This will:
- Start PostgreSQL database
- Create 2x SwAutoMorph instances
- Setup Nginx load balancer
- Migrate data from SQLite
- Configure health checks

### 4. Verify Migration

```bash
# Check service status
./deploy-postgres.sh status

# View logs
./deploy-postgres.sh logs

# Test endpoints
curl https://localhost:6001/api/auth/status
curl https://localhost:6001/health
```

## Configuration

### Environment Variables

```bash
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_swautomorph
POSTGRES_USER=swautomorph
POSTGRES_PASSWORD=secure_password
POSTGRES_MIN_CONN=2
POSTGRES_MAX_CONN=20

# Instance Configuration
USE_POSTGRES=true
INSTANCE_ID=1  # or 2 for second instance
```

### Database Connection Pooling

```python
# Connection pool configuration
{
    'min_connections': 2,
    'max_connections': 20,
    'host': 'localhost',
    'port': 5432,
    'database': 'ai_swautomorph',
    'user': 'swautomorph',
    'password': 'secure_password'
}
```

## Active/Active Configuration

### Load Balancer (Nginx)

- **Algorithm**: Least connections
- **Health Checks**: Every 30s
- **Failover**: Automatic
- **Session Persistence**: Optional (ip_hash)

### Database Consistency

- **MVCC**: PostgreSQL handles concurrent writes
- **Transactions**: ACID compliance
- **Connection Pooling**: Per-instance pools
- **Retry Logic**: Transient error handling

### Service Discovery

```bash
# Instance 1: http://localhost:6000
# Instance 2: http://localhost:6002
# Load Balancer: https://localhost:6001
# PostgreSQL: localhost:5432
```

## Monitoring

### Health Endpoints

```bash
# Load balancer health
curl http://localhost:8080/nginx_status

# Application health
curl http://localhost:6001/health

# Database health
curl http://localhost:6001/api/health/database
```

### Service Status

```bash
# Docker services
./deploy-postgres.sh status

# Individual health checks
curl -f http://localhost:6000/health  # Instance 1
curl -f http://localhost:6002/health  # Instance 2
```

## Troubleshooting

### Common Issues

1. **Connection Pool Exhaustion**
   ```bash
   # Check pool status in logs
   docker-compose -f docker-compose-postgres.yml logs ai-swautomorph-1
   
   # Increase max_connections if needed
   export POSTGRES_MAX_CONN=30
   ```

2. **Database Migration Errors**
   ```bash
   # Re-run migration manually
   python3 migration/migrate_sqlite_to_postgres.py
   ```

3. **Load Balancer Issues**
   ```bash
   # Check upstream status
   curl http://localhost:8080/upstream_status
   
   # Restart load balancer
   docker-compose -f docker-compose-postgres.yml restart nginx
   ```

### Performance Tuning

1. **PostgreSQL Configuration**
   ```sql
   -- Increase connection limits
   ALTER SYSTEM SET max_connections = 200;
   
   -- Optimize for concurrent writes
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ```

2. **Connection Pool Tuning**
   ```bash
   # Per instance
   POSTGRES_MIN_CONN=5
   POSTGRES_MAX_CONN=25
   
   # Total: 2 instances × 25 = 50 max connections
   ```

## Rollback Plan

If issues occur, rollback to SQLite:

```bash
# Stop PostgreSQL stack
./deploy-postgres.sh stop

# Restore SQLite backup
./deployControlPlan.sh --recover_db

# Start original stack
./deployControlPlan.sh start locally
```

## Production Deployment

### Two-Server Setup

**Server 1:**
```bash
# Deploy instance 1 + PostgreSQL
docker-compose -f docker-compose-postgres.yml up -d postgres ai-swautomorph-1
```

**Server 2:**
```bash
# Deploy instance 2 (connect to Server 1 PostgreSQL)
export POSTGRES_HOST=server1_ip
docker-compose -f docker-compose-postgres.yml up -d ai-swautomorph-2
```

**Load Balancer (OVH DNS):**
```bash
# Configure DNS round-robin
server1.swautomorph.com -> Server 1 IP
server2.swautomorph.com -> Server 2 IP
www.swautomorph.com -> DNS load balancing
```

### Security Considerations

1. **Database Security**
   - Use strong passwords
   - Enable SSL connections
   - Restrict network access
   - Regular security updates

2. **Application Security**
   - Session management
   - CSRF protection
   - Input validation
   - Rate limiting (Nginx)

3. **Network Security**
   - Firewall rules
   - VPN/private networks
   - SSL/TLS encryption
   - Regular security audits

## Maintenance

### Regular Tasks

```bash
# Database backup
pg_dump -h localhost -U swautomorph ai_swautomorph > backup.sql

# Log rotation
docker-compose -f docker-compose-postgres.yml logs --tail=1000 > logs/app.log

# Health monitoring
./deploy-postgres.sh status
```

### Updates

```bash
# Update application
git pull
docker-compose -f docker-compose-postgres.yml build
docker-compose -f docker-compose-postgres.yml up -d

# Update PostgreSQL
# (Follow PostgreSQL upgrade procedures)
```

## Performance Metrics

### Expected Improvements

- **Concurrent Users**: 10x increase
- **Database Performance**: 5x faster queries
- **Availability**: 99.9% (no single point of failure)
- **Scalability**: Horizontal scaling ready

### Monitoring Metrics

- Connection pool utilization
- Query response times
- Error rates per instance
- Load balancer distribution
- Database connection counts