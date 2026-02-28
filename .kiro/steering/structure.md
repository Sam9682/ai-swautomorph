# Project Structure

## Root Directory Layout

```
ai-swautomorph/
├── src/                    # Main application source code
├── scripts/                # CLI tools and utilities
├── templates/              # HTML templates (Jinja2)
├── static/                 # CSS, JS, and static assets
├── shared/                 # Context files for virtual AI agents
├── docs/                   # Comprehensive documentation
├── conf/                   # Configuration files
├── logs/                   # Application and service logs
├── ssl/                    # SSL certificates
├── migration/              # Database migration scripts
├── softfluid/              # Database backups and data
├── data/                   # Application data directory
├── .kiro/                  # Kiro AI assistant configuration
├── .venv/                  # Python virtual environment
├── ControlPlanFlaskApp.py  # Application entry point (delegates to src/main.py)
├── deployControlPlan.sh    # Main deployment script
├── docker-compose.yml      # Multi-container orchestration
├── gunicorn.conf.py        # Gunicorn server configuration
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Source Code Organization (`src/`)

### Core Application Files

- **main.py**: Application entry point with timestamped logging wrapper
- **ControlPlanFlaskApp_postgres.py**: Flask app factory with blueprint registration
- **database_postgres.py**: PostgreSQL manager with connection pooling (singleton pattern)
- **config_postgres.py**: Configuration settings and environment variables
- **auth.py**: Authentication utilities and decorators
- **nginx_manager.py**: Dynamic Nginx location management
- **orchestrator.py**: Application deployment orchestration logic
- **replication_manager.py**: Multi-server replication management
- **query_converter.py**: SQLite to PostgreSQL query conversion
- **db_health.py**: Database health monitoring
- **db_sync.py**: Database synchronization utilities
- **gitea_config.py**: Gitea integration configuration
- **create_gitea_repo.py**: Gitea repository creation utilities
- **platform_discovery.py**: Platform and service discovery

### Routes Directory (`src/routes/`)

Flask blueprints organized by functional domain:

- **main_routes.py**: Dashboard, documentation, and web UI
- **auth_routes.py**: User registration, login, logout, session management
- **sso_routes.py**: Single Sign-On token generation and validation
- **api_routes.py**: REST API endpoints with streaming support (applications, deployments, servers, nginx)
- **genai_routes.py**: Virtual AI agents (Developer and Operations assistants)
- **billing_routes.py**: Billing, cost tracking, and activity logging
- **orchestrator_routes.py**: Deployment orchestration endpoints
- **replication_routes.py**: Multi-server replication endpoints

## Scripts Directory (`scripts/`)

### CLI and Utilities

- **sf_cli.py**: Main command-line interface (register, list-apps, add-app, db-health, mount-s3fs, init-db)
- **mcp_server.py**: Model Context Protocol server for agent communication
- **orchestrator_cli.py**: Orchestrator command-line interface
- **test_platform.py**: Platform testing suite
- **test_orchestrator.py**: Orchestrator testing
- **test_nginx_locations.py**: Nginx location configuration tests
- **test_suites.py**: Comprehensive test suites
- **sync_nginx_locations.py**: Sync nginx locations from database

### Deployment and Infrastructure

- **postgresql_schema.sql**: PostgreSQL database schema definition
- **deploy_example_service.sh**: Example service deployment
- **start_swautomorph_controlplan.sh**: Start control plan service
- **stop_swautomorph_controlplan.sh**: Stop control plan service
- **swautomorph-controlplan.service**: Systemd service definition
- **setup_letsencrypt.sh**: Let's Encrypt SSL certificate setup
- **generate_ssl.sh**: Self-signed SSL certificate generation
- **kill_flask.sh**: Kill Flask processes
- **run_tests_example.sh**: Example test execution

### Infrastructure as Code

- **ovh_infrastructure.tf**: Terraform configuration for OVH cloud
- **terraform.tfvars.example**: Example Terraform variables

### Utilities

- **generate_hash.py**: Password hash generation
- **mount_s3fs.py**: S3 filesystem mounting for backups
- **fix_deployment_user_id.py**: Fix deployment user_id references
- **sso_client_example.py**: SSO client integration example

## Shared Context Files (`shared/`)

Context files for virtual AI agents (operations prompts):

- **START_context.md**: Application start operation
- **STOP_context.md**: Application stop operation
- **RESTART_context.md**: Application restart operation
- **LOGS_context.md**: Log viewing operation
- **PS_context.md**: Process status operation
- **MODIFY_CODE_context.md**: Code modification operation
- **SPECIFY_context.md**: Specification operation
- **BACKUP_DATABASE_context.md**: Database backup operation
- **RESTORE_DATABASE_context.md**: Database restore operation
- **CLEAN_DATABASE_context.md**: Database cleanup operation
- **MAKE_APP_COMPLIANT_context.md**: Application compliance operation
- **VERIFY_APP_COMPLIANCE_context.md**: Compliance verification operation
- **README_SPECIFY.md**: Specification documentation

## Documentation (`docs/`)

### User Guides

- **USER_GUIDE.md**: Comprehensive user guide for AI agents
- **QUICK_START_TESTS.md**: Quick start testing guide
- **QUICK_REFERENCE_BACKUP.md**: Backup quick reference

### Architecture and Design

- **ARCHITECTURE_GUIDE.md**: System architecture overview
- **MULTI_PLATFORM_ARCHITECTURE.md**: Multi-platform architecture
- **MULTI_DOMAIN_CONFIGURATION.md**: Multi-domain configuration

### Deployment and Operations

- **DEPLOYMENT_GUIDE.md**: Deployment procedures
- **REPLICATION_GUIDE.md**: Multi-server replication guide
- **REPLICATION_QUICKSTART.md**: Replication quick start
- **POSTGRESQL_MIGRATION_GUIDE.md**: SQLite to PostgreSQL migration

### Feature Documentation

- **VIRTUAL_AGENTS_API.md**: Virtual AI agents API reference
- **VIRTUAL_ADVISOR_QUICK_GUIDE.md**: Virtual advisor quick guide
- **NGINX_DYNAMIC_LOCATIONS.md**: Dynamic nginx locations guide
- **NGINX_DYNAMIC_LOCATIONS_IMPLEMENTATION.md**: Implementation details
- **S3_BACKUP_FLOW_DIAGRAM.md**: S3 backup flow diagram
- **DATABASE_IMPROVEMENTS.md**: Database enhancement documentation

### Implementation Summaries

- **IMPLEMENTATION_SUMMARY.md**: Overall implementation summary
- **IMPLEMENTATION_CHECKLIST.md**: Implementation checklist
- **IMPLEMENTATION_TEST_SUMMARY.md**: Test implementation summary
- **SPECIFY_FEATURE_IMPLEMENTATION.md**: Specification feature implementation
- **STREAMING_RESPONSE_IMPLEMENTATION.md**: Streaming response implementation
- **IP_BASED_S3_BACKUP_SUMMARY.md**: IP-based S3 backup summary
- **RECOVER_DB_S3_FEATURE.md**: Database recovery from S3

### Virtual Agents

- **README_VIRTUAL_ADVISOR.md**: Virtual advisor documentation
- **TEST_VIRTUAL_ADVISOR.md**: Virtual advisor testing
- **VIRTUAL_ADVISOR_CHANGES.md**: Virtual advisor changes
- **VIRTUAL_ADVISOR_UI_CHANGES.md**: Virtual advisor UI changes
- **VIRTUAL_DEVOPS_TEAM_APP_SELECTOR.md**: Virtual DevOps team app selector

### Orchestrator

- **LIGHT_ORCHESTRATOR.md**: Light orchestrator documentation
- **LIGHT_ORCHESTRATOR_IMPLEMENTATION.md**: Implementation details
- **LIGHT_ORCHESTRATOR_MODIFICATIONS.md**: Modifications and enhancements

## Configuration (`conf/`)

- **deploy.ini**: Main deployment configuration (domain, ports, Gitea, ranges)
- **gunicorn.pid**: Gunicorn process ID file

## Migration Scripts (`migration/`)

SQL migration scripts for database schema updates:

- **add_user_id_to_services.sql**: Add user_id column to services table
- **fix_deployment_user_id.sql**: Fix deployment user_id references
- **fix_instances_fkey.sql**: Fix instances foreign key constraints
- **fix_server_capacity.sql**: Fix server capacity columns
- **fix_services_constraint.sql**: Fix services table constraints

## Database Backups (`softfluid/db/backup/`)

Timestamped backup directories with:
- **complete_database.sql**: Full database dump
- **schema_only.sql**: Schema without data
- **data_only.sql**: Data without schema
- **backup.log**: Backup operation log

## Logs Directory (`logs/`)

Application logs organized by module:
- **api_routes.log**: API endpoint logs
- **genai_routes.log**: Virtual AI agent logs
- **billing_routes.log**: Billing operation logs
- **orchestrator_routes.log**: Orchestrator logs
- **replication_routes.log**: Replication logs
- **config_postgres.log**: Configuration logs
- **gunicorn_access.log**: Gunicorn access logs
- **gunicorn_error.log**: Gunicorn error logs
- **test_platform_*.log**: Test execution logs
- **print_output_swautomorph.log**: Application print output

## Naming Conventions

### Python Files
- **Snake_case**: All Python files use snake_case (e.g., `database_postgres.py`, `api_routes.py`)
- **Suffix patterns**: 
  - `_postgres.py`: PostgreSQL-specific implementations
  - `_routes.py`: Flask blueprint route definitions
  - `_manager.py`: Manager classes (nginx_manager, replication_manager)

### Database Tables
- **Snake_case**: All table and column names (e.g., `server_ip`, `user_id`, `application_name`)
- **Plural for tables**: Tables use plural names where appropriate (e.g., `users`, `applications`, `servers`)

### Configuration Files
- **Lowercase with extensions**: `deploy.ini`, `gunicorn.conf.py`, `docker-compose.yml`
- **Dot-prefixed for environment**: `.env`, `.env.postgres`, `.gitignore`

### Documentation
- **UPPERCASE.md**: Documentation files use uppercase with underscores (e.g., `USER_GUIDE.md`, `ARCHITECTURE_GUIDE.md`)
