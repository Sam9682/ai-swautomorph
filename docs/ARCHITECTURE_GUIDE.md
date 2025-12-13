# AI-SwAutoMorph Architecture Design / Guide d'Architecture AI-SwAutoMorph

## English

### Overview

AI-SwAutoMorph is a centralized application management platform that automates the deployment, evolution, and management of containerized applications using a standardized approach. The platform leverages Docker Compose, deployment scripts, GenAI integration, and multi-server deployment capabilities to provide seamless application lifecycle management.

### Core Architecture

#### 1. Modular Flask Application

```
ai-swautomorph/
├── src/                          # Core application modules
│   ├── config.py                 # Configuration & environment settings
│   ├── database.py               # Database schema & initialization with thread-safe manager
│   ├── auth.py                   # Authentication & SSO management
│   ├── app.py                    # Flask application factory
│   ├── main.py                   # Application entry point with timestamped logging
│   ├── automorph_application.py  # GenAI integration for code modification
│   ├── db_health.py              # Database health monitoring utilities
│   ├── create_gitea_repo.py      # Gitea repository management
│   ├── gitea_config.py           # Gitea configuration utilities
│   └── routes/                   # Route handlers (blueprints)
│       ├── main_routes.py        # Dashboard & main pages
│       ├── auth_routes.py        # User authentication
│       ├── sso_routes.py         # Single Sign-On functionality
│       ├── api_routes.py         # REST API endpoints with streaming support
│       └── billing_routes.py     # Billing and cost management
├── app.py                        # Legacy entry point (redirects to src/app.py)
├── deployControlPlan.sh          # Main deployment control script
├── scripts/                      # CLI tools and utilities
│   ├── cli.py                    # Command-line interface
│   ├── mcp_server.py             # Model Context Protocol server
│   ├── generate_ssl.sh           # SSL certificate generation
│   ├── fix_ssl_chain.sh          # SSL certificate chain fixing
│   ├── mount_s3fs.py             # S3 filesystem mounting
│   └── test_*.py                 # Testing utilities
├── shared/                       # Shared deployment resources
│   ├── deployApp.sh              # Universal deployment script
│   └── *_context.md              # Context templates for GenAI operations
├── templates/                    # HTML templates with multi-language support
├── static/                       # CSS, JS, and static files
├── ssl/                          # SSL certificates
├── logs/                         # Application logs with daily rotation
├── softfluid/db/                 # Database and backups
├── conf/                         # Configuration files
│   ├── deploy.ini                # Deployment configuration
│   └── app.pid                   # Application process ID
└── docker-compose.yml            # Docker containerization
```

#### 2. Database Schema

```sql
-- Core entities for application management
Users: id, username, email, password_hash, first_name, last_name, suspended, created_at
Applications: id, name, description, git_url, created_at
User_Applications: id, user_id, application_id, url, http_port, https_port, created_at
Deployments: id, user_id, application_name, status, deployment_path, git_url, server_id, created_at, updated_at
Servers: id, SERVER_IP, SERVER_NAME, SERVER_CAPACITY_USER_MAX, SERVER_CAPACITY_APPLI_MAX, SERVER_STATUS, SERVER_TYPE, created_at
Auth_Tokens: id, user_id, token_hash, expires_at, created_at
Application_Costs: id, application_id, cost_per_day, created_at, updated_at
Billing_Activities: id, user_id, application_id, action, started_at, stopped_at, duration_seconds, cost_amount, created_at
Users_Logs: id, user_id, username, action, datetime
```

---

## Français

### Aperçu

AI-SwAutoMorph est une plateforme centralisée de gestion d'applications qui automatise le déploiement, l'évolution et la gestion d'applications conteneurisées en utilisant une approche standardisée. La plateforme exploite Docker Compose, les scripts de déploiement, l'intégration GenAI et les capacités de déploiement multi-serveurs pour fournir une gestion transparente du cycle de vie des applications.

### Architecture Principale

#### 1. Application Flask Modulaire

```
ai-swautomorph/
├── src/                          # Modules d'application principaux
│   ├── config.py                 # Configuration et paramètres d'environnement
│   ├── database.py               # Schéma de base de données et initialisation avec gestionnaire thread-safe
│   ├── auth.py                   # Authentification et gestion SSO
│   ├── app.py                    # Factory d'application Flask
│   ├── main.py                   # Point d'entrée de l'application avec journalisation horodatée
│   ├── automorph_application.py  # Intégration GenAI pour modification de code
│   ├── db_health.py              # Utilitaires de surveillance de santé de base de données
│   ├── create_gitea_repo.py      # Gestion des dépôts Gitea
│   ├── gitea_config.py           # Utilitaires de configuration Gitea
│   └── routes/                   # Gestionnaires de routes (blueprints)
│       ├── main_routes.py        # Tableau de bord et pages principales
│       ├── auth_routes.py        # Authentification utilisateur
│       ├── sso_routes.py         # Fonctionnalité Single Sign-On
│       ├── api_routes.py         # Points de terminaison API REST avec support streaming
│       └── billing_routes.py     # Facturation et gestion des coûts
├── app.py                        # Point d'entrée hérité (redirige vers src/app.py)
├── deployControlPlan.sh          # Script principal de contrôle de déploiement
├── scripts/                      # Outils CLI et utilitaires
│   ├── cli.py                    # Interface en ligne de commande
│   ├── mcp_server.py             # Serveur Model Context Protocol
│   ├── generate_ssl.sh           # Génération de certificats SSL
│   ├── fix_ssl_chain.sh          # Correction de chaîne de certificats SSL
│   ├── mount_s3fs.py             # Montage du système de fichiers S3
│   └── test_*.py                 # Utilitaires de test
├── shared/                       # Ressources de déploiement partagées
│   ├── deployApp.sh              # Script de déploiement universel
│   └── *_context.md              # Modèles de contexte pour opérations GenAI
├── templates/                    # Modèles HTML avec support multi-langues
├── static/                       # Fichiers CSS, JS et statiques
├── ssl/                          # Certificats SSL
├── logs/                         # Journaux d'application avec rotation quotidienne
├── softfluid/db/                 # Base de données et sauvegardes
├── conf/                         # Fichiers de configuration
│   ├── deploy.ini                # Configuration de déploiement
│   └── app.pid                   # ID de processus d'application
└── docker-compose.yml            # Conteneurisation Docker
```

#### 2. Schéma de Base de Données

```sql
-- Entités principales pour la gestion d'applications
Users: id, username, email, password_hash, first_name, last_name, suspended, created_at
Applications: id, name, description, git_url, created_at
User_Applications: id, user_id, application_id, url, http_port, https_port, created_at
Deployments: id, user_id, application_name, status, deployment_path, git_url, server_id, created_at, updated_at
Servers: id, SERVER_IP, SERVER_NAME, SERVER_CAPACITY_USER_MAX, SERVER_CAPACITY_APPLI_MAX, SERVER_STATUS, SERVER_TYPE, created_at
Auth_Tokens: id, user_id, token_hash, expires_at, created_at
Application_Costs: id, application_id, cost_per_day, created_at, updated_at
Billing_Activities: id, user_id, application_id, action, started_at, stopped_at, duration_seconds, cost_amount, created_at
Users_Logs: id, user_id, username, action, datetime
```