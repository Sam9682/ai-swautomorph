# 🏗️ AI-SwAutoMorph Architecture Design / Guide d'Architecture AI-SwAutoMorph

## English

<div class="center">
🚀 **Centralized Application Deployment Platform for GenAI Agents** 🤖
</div>

### 🌟 Overview

AI-SwAutoMorph is a **centralized application deployment and management platform** designed for GenAI agents. It provides automated deployment, lifecycle management, and SSO authentication for web applications through multiple interfaces (Web, CLI, API, MCP). The platform enables GenAI agents to autonomously deploy, manage, and access web applications without human intervention.

### 🏛️ Core Architecture

#### 1. 📦 Modular Flask Application

```
🏠 ai-swautomorph/
├── 📁 src/                          # Core application modules
│   ├── ⚙️ config.py                 # Configuration & multi-language support
│   ├── 🗄️ database.py               # Thread-safe database manager with WAL mode
│   ├── 🔐 auth.py                   # Authentication & SSO management
│   ├── 🌐 app.py                    # Flask application factory
│   ├── 🤖 automorph_application.py  # Q Chat integration for code modification
│   └── 📁 routes/                   # Route handlers (blueprints)
│       ├── 🏠 main_routes.py        # Dashboard & documentation viewer
│       ├── 👤 auth_routes.py        # User authentication
│       ├── 🔑 sso_routes.py         # Single Sign-On functionality
│       ├── 🔌 api_routes.py         # REST API with streaming support
│       └── 💰 billing_routes.py     # Billing and cost management
├── 📁 templates/                    # HTML templates with EN/FR support
│   ├── 🎨 base.html                 # Base template with navbar language switching
│   ├── 📊 dashboard.html            # Main dashboard with reorganized navigation
│   ├── 🚪 login.html                # Login page emphasizing AI agents
│   └── 📖 doc_viewer.html           # Markdown documentation viewer
├── 📁 static/                       # CSS, JS, and static files
├── 📁 docs/                         # Documentation with bilingual support
│   ├── 🏗️ ARCHITECTURE_GUIDE.md     # This file
│   ├── 🚀 DEPLOYMENT_GUIDE.md       # Deployment procedures
│   ├── 🗄️ DATABASE_IMPROVEMENTS.md  # Database architecture
│   └── 👥 USER_GUIDE.md             # AI agent usage guide
├── 📁 scripts/                      # CLI tools and utilities
│   ├── 💻 cli.py                    # Command-line interface
│   └── 🔌 mcp_server.py             # Model Context Protocol server
├── 📁 shared/                       # Shared deployment resources
└── 🚀 deployControlPlan.sh          # Main deployment control script
```

#### 2. 🤖 AI Agent Integration

The platform provides **two specialized AI agents**:

**🔧 Q Chat Developer Agent** (`/api/qchat_developer`):
- 💻 Code modification and feature development
- 🗣️ Natural language to code translation
- 🌿 Git branch management with timestamps
- 🧪 Automatic testing and deployment

**🚀 Q Chat Operations Agent** (`/api/qchat_operations`):
- ⚡ Deployment operations (START, STOP, RESTART)
- 🏗️ Infrastructure management
- 📊 Application monitoring and troubleshooting
- 📈 Server capacity management

#### 3. 🌍 Multi-Language Support

- **🔄 Navbar Language Switching**: FR/EN toggle in navigation bar
- **💾 Session-Based Language**: Language preference stored in Flask session
- **🎨 Template Integration**: All templates support `get_text()` function
- **📖 Documentation Viewer**: Markdown files with bilingual sections
- **⚡ Dynamic Content**: JavaScript-based language switching for documentation

#### 4. 🗄️ Database Schema

```sql
-- 🏢 Core entities with multi-server support
👥 Users: id, username, email, password_hash, first_name, last_name, suspended, created_at
📱 Applications: id, name, description, git_url, created_at
🔗 User_Applications: id, user_id, application_id, url, http_port, https_port, created_at
🚀 Deployments: id, user_id, application_name, status, deployment_path, git_url, server_id, created_at, updated_at
🖥️ Servers: id, SERVER_IP, SERVER_NAME, SERVER_CAPACITY_USER_MAX, SERVER_CAPACITY_APPLI_MAX, SERVER_STATUS, SERVER_TYPE, created_at
🔑 Auth_Tokens: id, user_id, token_hash, expires_at, created_at
💰 Application_Costs: id, application_id, cost_per_day, created_at, updated_at
📊 Billing_Activities: id, user_id, application_id, action, started_at, stopped_at, duration_seconds, cost_amount, created_at
📝 Users_Logs: id, user_id, username, action, datetime
```

#### 5. 🧭 Navigation Architecture

**📋 Navbar Organization**:
- 📱 Applications and 💰 Billing tabs in main navigation
- ⚙️ Configuration dropdown (👥 Users, 🖥️ Servers, 🗄️ Database) for admin
- ❓ Help dropdown with direct links to documentation
- 🌍 Language toggle (FR/EN) with session persistence
- 📱 Mobile-responsive navigation with hamburger menu

**🎯 Dashboard Reorganization**:
- ↗️ Moved from content-area tabs to navbar navigation
- 📦 Consolidated menus in dropdown format
- 🔗 Direct access to markdown documentation
- ✨ Streamlined user experience

---

## Français

<div class="center">
🚀 **Plateforme Centralisée de Déploiement d'Applications pour Agents GenAI** 🤖
</div>

### 🌟 Aperçu

AI-SwAutoMorph est une **plateforme centralisée de déploiement et de gestion d'applications** conçue pour les agents GenAI. Elle fournit un déploiement automatisé, une gestion du cycle de vie et une authentification SSO pour les applications web à travers plusieurs interfaces (Web, CLI, API, MCP). La plateforme permet aux agents GenAI de déployer, gérer et accéder de manière autonome aux applications web sans intervention humaine.

### 🏛️ Architecture Principale

#### 1. 📦 Application Flask Modulaire

```
🏠 ai-swautomorph/
├── 📁 src/                          # Modules d'application principaux
│   ├── ⚙️ config.py                 # Configuration et support multi-langues
│   ├── 🗄️ database.py               # Gestionnaire de base de données thread-safe avec mode WAL
│   ├── 🔐 auth.py                   # Authentification et gestion SSO
│   ├── 🌐 app.py                    # Factory d'application Flask
│   ├── 🤖 automorph_application.py  # Intégration Q Chat pour modification de code
│   └── 📁 routes/                   # Gestionnaires de routes (blueprints)
│       ├── 🏠 main_routes.py        # Tableau de bord et visualiseur de documentation
│       ├── 👤 auth_routes.py        # Authentification utilisateur
│       ├── 🔑 sso_routes.py         # Fonctionnalité Single Sign-On
│       ├── 🔌 api_routes.py         # API REST avec support streaming
│       └── 💰 billing_routes.py     # Facturation et gestion des coûts
├── 📁 templates/                    # Modèles HTML avec support EN/FR
│   ├── 🎨 base.html                 # Modèle de base avec changement de langue navbar
│   ├── 📊 dashboard.html            # Tableau de bord principal avec navigation réorganisée
│   ├── 🚪 login.html                # Page de connexion mettant l'accent sur les agents IA
│   └── 📖 doc_viewer.html           # Visualiseur de documentation Markdown
├── 📁 static/                       # Fichiers CSS, JS et statiques
├── 📁 docs/                         # Documentation avec support bilingue
│   ├── 🏗️ ARCHITECTURE_GUIDE.md     # Ce fichier
│   ├── 🚀 DEPLOYMENT_GUIDE.md       # Procédures de déploiement
│   ├── 🗄️ DATABASE_IMPROVEMENTS.md  # Architecture de base de données
│   └── 👥 USER_GUIDE.md             # Guide d'utilisation des agents IA
├── 📁 scripts/                      # Outils CLI et utilitaires
│   ├── 💻 cli.py                    # Interface en ligne de commande
│   └── 🔌 mcp_server.py             # Serveur Model Context Protocol
├── 📁 shared/                       # Ressources de déploiement partagées
└── 🚀 deployControlPlan.sh          # Script principal de contrôle de déploiement
```

#### 2. 🤖 Intégration des Agents IA

La plateforme fournit **deux agents IA spécialisés** :

**🔧 Agent Développeur Q Chat** (`/api/qchat_developer`):
- 💻 Modification de code et développement de fonctionnalités
- 🗣️ Traduction langage naturel vers code
- 🌿 Gestion des branches Git avec horodatage
- 🧪 Tests et déploiement automatiques

**🚀 Agent Opérations Q Chat** (`/api/qchat_operations`):
- ⚡ Opérations de déploiement (START, STOP, RESTART)
- 🏗️ Gestion d'infrastructure
- 📊 Surveillance et dépannage d'applications
- 📈 Gestion de capacité serveur

#### 3. 🌍 Support Multi-Langues

- **🔄 Changement de Langue Navbar**: Basculement FR/EN dans la barre de navigation
- **💾 Langue Basée sur Session**: Préférence de langue stockée dans la session Flask
- **🎨 Intégration Template**: Tous les templates supportent la fonction `get_text()`
- **📖 Visualiseur de Documentation**: Fichiers Markdown avec sections bilingues
- **⚡ Contenu Dynamique**: Changement de langue basé JavaScript pour la documentation

#### 4. 🗄️ Schéma de Base de Données

```sql
-- 🏢 Entités principales avec support multi-serveurs
👥 Users: id, username, email, password_hash, first_name, last_name, suspended, created_at
📱 Applications: id, name, description, git_url, created_at
🔗 User_Applications: id, user_id, application_id, url, http_port, https_port, created_at
🚀 Deployments: id, user_id, application_name, status, deployment_path, git_url, server_id, created_at, updated_at
🖥️ Servers: id, SERVER_IP, SERVER_NAME, SERVER_CAPACITY_USER_MAX, SERVER_CAPACITY_APPLI_MAX, SERVER_STATUS, SERVER_TYPE, created_at
🔑 Auth_Tokens: id, user_id, token_hash, expires_at, created_at
💰 Application_Costs: id, application_id, cost_per_day, created_at, updated_at
📊 Billing_Activities: id, user_id, application_id, action, started_at, stopped_at, duration_seconds, cost_amount, created_at
📝 Users_Logs: id, user_id, username, action, datetime
```

#### 5. 🧭 Architecture de Navigation

**📋 Organisation Navbar**:
- 📱 Onglets Applications et 💰 Facturation dans la navigation principale
- ⚙️ Menu déroulant Configuration (👥 Utilisateurs, 🖥️ Serveurs, 🗄️ Base de données) pour admin
- ❓ Menu déroulant Aide avec liens directs vers la documentation
- 🌍 Basculement de langue (FR/EN) avec persistance de session
- 📱 Navigation responsive mobile avec menu hamburger

**🎯 Réorganisation du Tableau de Bord**:
- ↗️ Déplacé des onglets de zone de contenu vers la navigation navbar
- 📦 Menus consolidés en format déroulant
- 🔗 Accès direct à la documentation markdown
- ✨ Expérience utilisateur rationalisée