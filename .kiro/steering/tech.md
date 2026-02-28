# Technology Stack

## Core Technologies

- **Backend**: Python 3 with Flask web framework
- **Database**: PostgreSQL 15 (primary), SQLite (legacy/migration support)
- **Web Server**: Gunicorn with Nginx reverse proxy
- **Containerization**: Docker with docker-compose
- **Version Control**: Gitea (self-hosted Git service)
- **Security**: ModSecurity WAF with OWASP CRS rules

## Key Python Libraries

```
Flask - Web framework
Werkzeug - WSGI utilities
psycopg2-binary - PostgreSQL adapter
Flask-CORS - Cross-origin resource sharing
gunicorn - WSGI HTTP server
requests - HTTP client
click - CLI framework
simple-term-menu - Interactive CLI menus
python-dotenv - Environment variable management
```

## Architecture Patterns

- **Modular Blueprint Architecture**: Routes organized in separate blueprints (auth, api, sso, genai, billing, orchestrator, replication)
- **Singleton Pattern**: Database manager uses thread-safe singleton with connection pooling
- **Context Managers**: Database connections managed via `@contextmanager` for automatic cleanup
- **Factory Pattern**: Flask app created via `create_app()` factory function
- **Timestamped Logging**: Custom stdout wrapper adds timestamps to all print statements

## Database Conventions

- **Connection Pooling**: PostgreSQL uses psycopg2.pool.ThreadedConnectionPool (min 2, max 20 connections)
- **Thread Safety**: All database operations use thread-local connections with locking
- **Query Conversion**: SQLite queries automatically converted to PostgreSQL syntax via `query_converter.py`
- **Schema Naming**: Snake_case for tables/columns (e.g., `server_ip`, `user_id`)
- **Port Calculation**: Dynamic port assignment based on user_id and app_id using formula from deploy.ini

## Common Commands

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 ./scripts/sf_cli.py init-db

# Run development server
python3 ControlPlanFlaskApp.py
# or
python3 src/main.py

# Run with Gunicorn (production)
gunicorn -c gunicorn.conf.py src.main:create_app()
```

### Testing

```bash
# Run test platform
python3 ./scripts/test_platform.py

# Run orchestrator tests
python3 ./scripts/test_orchestrator.py

# Run nginx location tests
python3 ./scripts/test_nginx_locations.py

# Run test suites
python3 ./scripts/test_suites.py
```

### Deployment

```bash
# Interactive deployment (recommended)
./deployControlPlan.sh start

# Local deployment (no Docker)
./deployControlPlan.sh start locally

# Docker deployment
./deployControlPlan.sh start docker

# Check service status
./deployControlPlan.sh ps

# View logs
./deployControlPlan.sh logs

# Restart services
./deployControlPlan.sh restart

# Stop services
./deployControlPlan.sh stop
```

### Database Management

```bash
# Database health check
python3 ./scripts/sf_cli.py db-health

# Create backup
./deployControlPlan.sh backup_db

# Recover from backup
./deployControlPlan.sh --recover_db
python3 recover_db.py

# Migrate SQLite to PostgreSQL
python3 ./migration/migrate_sqlite_to_postgres.py
```

### CLI Operations

```bash
# Register user
python3 ./scripts/sf_cli.py register --username user --email user@example.com --password pass

# List applications
python3 ./scripts/sf_cli.py list-apps

# Add application
python3 ./scripts/sf_cli.py add-app --name MyApp --url https://myapp.com

# Validate SSO token
python3 ./scripts/sf_cli.py validate-token --token TOKEN

# Mount S3 for backups
python3 ./scripts/sf_cli.py mount-s3fs softfluid /mnt/s3

# Sync nginx locations
python3 ./scripts/sync_nginx_locations.py
```

## Configuration Files

- **deploy.ini**: Main deployment configuration (domain, ports, ranges, Gitea settings)
- **.env / .env.postgres**: Environment variables (SECRET_KEY, POSTGRES_* credentials)
- **gunicorn.conf.py**: Gunicorn server configuration (workers, timeouts, logging)
- **docker-compose.yml**: Multi-container orchestration (app, postgres, nginx, gitea)

## Environment Variables

```bash
# Flask
FLASK_ENV=production|development
SECRET_KEY=<32-byte-hex>
FLASK_RUN_PORT=5000

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_swautomorph
POSTGRES_USER=swautomorph
POSTGRES_PASSWORD=<password>
POSTGRES_MIN_CONN=2
POSTGRES_MAX_CONN=20

# Application
USE_POSTGRES=true
AI_ENGINE=kiro-cli
```

## Port Allocation Formula

```python
# From deploy.ini and database_postgres.py
PORT_RANGE_BEGIN = RANGE_START + user_id * RANGE_RESERVED
HTTP_PORT = PORT_RANGE_BEGIN + app_id * RANGE_PORTS_PER_APPLICATION
HTTPS_PORT = HTTP_PORT + 1
HTTP_PORT2 = HTTPS_PORT + 1
HTTPS_PORT2 = HTTP_PORT2 + 1
```

## Logging Conventions

- **Location**: `logs/` directory with daily rotation
- **Format**: Timestamped entries via custom stdout wrapper
- **Files**: Separate logs per module (api_routes.log, genai_routes.log, etc.)
- **Gunicorn**: Access and error logs in logs/gunicorn_*.log
