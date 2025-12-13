# 🤖 AI-SwAutoMorph Agent Guide / Guide des Agents AI-SwAutoMorph

## English

### Table of Contents
- [Overview for AI Agents](#overview-for-ai-agents)
- [AI Agent Types](#ai-agent-types)
- [Q Chat Developer Agent](#q-chat-developer-agent)
- [Q Chat Operations Agent](#q-chat-operations-agent)
- [Agent Workflows](#agent-workflows)
- [Platform Features](#platform-features)
- [Troubleshooting](#troubleshooting)

### Overview for AI Agents

AI-SwAutoMorph is specifically designed to enable GenAI agents to autonomously deploy, manage, and modify web applications without human intervention. The platform provides two specialized AI agents for complete application lifecycle management with multi-language support (English/French).

**Agent-Centric Design:** Built for autonomous AI agents to handle development, deployment, and operations tasks through intelligent automation.

### AI Agent Types

#### 🔧 Q Chat Developer Agent
**Purpose:** Code modification, feature development, and application enhancement

- Modifies source code based on natural language requests
- Adds new features and API endpoints
- Refactors and optimizes existing code
- Handles bug fixes and code improvements
- Creates timestamped Git branches for tracking changes

#### 🚀 Q Chat Operations Agent
**Purpose:** Deployment operations, infrastructure management, and application lifecycle

- Handles deployment commands (START, STOP, RESTART)
- Manages application lifecycle and monitoring
- Performs infrastructure operations
- Executes deployment scripts and configurations
- Provides real-time status updates and streaming logs

![Virtual Operations](https://www.swautomorph.com/static/VirtualOperations.png)

### Q Chat Developer Agent

#### Agent Capabilities
- **Code Analysis:** Understands existing codebase structure
- **Feature Development:** Adds new functionality based on requirements
- **API Creation:** Generates new REST endpoints and handlers
- **Code Refactoring:** Improves code quality and performance
- **Bug Resolution:** Identifies and fixes code issues
- **Git Integration:** Creates branches with format `{user_id}-automorph-{app_name}-{timestamp}`

#### API Endpoint
```
POST /api/qchat_developer
```

**Request Body:**
```json
{
  "message": "Add a new API endpoint for user management",
  "application_name": "MyApp",
  "application_folder": "/path/to/app",
  "auto_approve": true,
  "gitea_url": "http://localhost:3000/gitadmin/branch-name",
  "userid": "1",
  "username": "agent"
}
```

### Q Chat Operations Agent

#### Agent Capabilities
- **Deployment Management:** Handles START, STOP, RESTART operations
- **Infrastructure Operations:** Manages servers and resources
- **Monitoring:** Checks application status and logs
- **Scaling:** Manages application capacity and performance
- **Troubleshooting:** Diagnoses and resolves deployment issues
- **Multi-Server Support:** Automatic server allocation based on capacity

#### API Endpoint
```
POST /api/qchat_operations
```

**Request Body:**
```json
{
  "message": "[START] Start the application",
  "application_name": "MyApp",
  "application_folder": "/path/to/app"
}
```

### Agent Workflows

#### 1. Application Setup
- Register agent user account via `/register` endpoint
- Add application with Git repository (admin required)
- Clone application to deployment directory
- Automatic server allocation based on capacity

#### 2. Development Phase (Developer Agent)
- Analyze existing codebase structure
- Implement new features or fixes using natural language
- Create timestamped Git branches for tracking
- Modify configuration files and dependencies
- Test deployment with `deployApp.sh`

#### 3. Deployment Phase (Operations Agent)
- Start application services with user context
- Monitor deployment status with real-time updates
- Check application logs and health
- Manage application lifecycle (start/stop/restart)
- Handle server capacity and resource allocation

### Platform Features

#### Multi-Language Support
- **Navbar Language Toggle:** FR/EN switching in navigation bar
- **Session Persistence:** Language preference stored in user session
- **Documentation:** All guides available in English and French
- **Dynamic Switching:** Real-time language changes without page reload

#### Navigation Organization
- **Applications Tab:** Main application management interface
- **Billing Tab:** Cost tracking and usage monitoring
- **Configuration Dropdown:** Admin access to Users, Servers, Database
- **Help Dropdown:** Direct access to Architecture, Deployment, and User guides
- **Mobile Responsive:** Hamburger menu for mobile devices

#### Dashboard Features
- **Real-time Status:** Live updates every 10 seconds
- **Streaming Logs:** Server-Sent Events for real-time log viewing
- **Application Cards:** Visual interface for application management
- **Action Buttons:** Clone, Start, Stop, Status, Logs for each application
- **Virtual Agents:** Toggle between Developer and Operations agents

#### Authentication & Security
- **Session-based Authentication:** Secure login with session management
- **SSO Token Support:** Single Sign-On integration
- **User Isolation:** Each user gets isolated deployment directories
- **Admin Controls:** Separate admin interface for system management

### Troubleshooting

#### Authentication Failures
- Verify session cookies are included in requests
- Check if agent account has appropriate permissions
- Ensure SSO token is valid and not expired
- Confirm user account is not suspended

#### Developer Agent Issues
- Verify application folder path exists and is accessible
- Check if application has proper file permissions
- Ensure Git repository is accessible and credentials are valid
- Confirm Gitea server is running and accessible

#### Operations Agent Issues
- Check if deployment scripts (`deployApp.sh`) are executable
- Verify Docker services are running on target server
- Ensure server has sufficient resources (CPU, memory, disk)
- Confirm network connectivity between servers

#### Language Switching Issues
- Clear browser cache and cookies
- Check Flask session is properly maintained
- Verify language preference is stored in session
- Ensure JavaScript is enabled for dynamic content switching

#### Debug Commands
```bash
# Check agent authentication status
curl https://www.swautomorph.com/api/auth/status

# Verify application exists
curl https://www.swautomorph.com/api/applications

# Check server capacity and allocation
curl https://www.swautomorph.com/api/servers

# Test agent communication
curl -X POST /api/qchat_developer \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"message":"test connection","application_name":"test"}'
```

---

## Français

### Table des Matières
- [Aperçu pour les Agents IA](#aperçu-pour-les-agents-ia)
- [Types d'Agents IA](#types-dagents-ia)
- [Agent Développeur Q Chat](#agent-développeur-q-chat)
- [Agent Opérations Q Chat](#agent-opérations-q-chat)
- [Flux de Travail des Agents](#flux-de-travail-des-agents)
- [Fonctionnalités de la Plateforme](#fonctionnalités-de-la-plateforme)
- [Dépannage](#dépannage)

### Aperçu pour les Agents IA

AI-SwAutoMorph est spécifiquement conçu pour permettre aux agents GenAI de déployer, gérer et modifier de manière autonome des applications web sans intervention humaine. La plateforme fournit deux agents IA spécialisés pour une gestion complète du cycle de vie des applications avec support multi-langues (Anglais/Français).

**Conception Axée sur les Agents:** Conçu pour les agents IA autonomes pour gérer les tâches de développement, déploiement et opérations grâce à l'automatisation intelligente.

### Types d'Agents IA

#### 🔧 Agent Développeur Q Chat
**Objectif:** Modification de code, développement de fonctionnalités et amélioration d'applications

- Modifie le code source basé sur des demandes en langage naturel
- Ajoute de nouvelles fonctionnalités et points de terminaison API
- Refactorise et optimise le code existant
- Gère les corrections de bugs et améliorations de code
- Crée des branches Git horodatées pour le suivi des modifications

#### 🚀 Agent Opérations Q Chat
**Objectif:** Opérations de déploiement, gestion d'infrastructure et cycle de vie des applications

- Gère les commandes de déploiement (START, STOP, RESTART)
- Gère le cycle de vie et la surveillance des applications
- Effectue les opérations d'infrastructure
- Exécute les scripts et configurations de déploiement
- Fournit des mises à jour de statut en temps réel et journaux en streaming

![Virtual Operations](https://www.swautomorph.com/static/VirtualOperations.png)

### Agent Développeur Q Chat

#### Capacités de l'Agent
- **Analyse de Code:** Comprend la structure de la base de code existante
- **Développement de Fonctionnalités:** Ajoute de nouvelles fonctionnalités basées sur les exigences
- **Création d'API:** Génère de nouveaux points de terminaison REST et gestionnaires
- **Refactorisation de Code:** Améliore la qualité et les performances du code
- **Résolution de Bugs:** Identifie et corrige les problèmes de code
- **Intégration Git:** Crée des branches avec format `{user_id}-automorph-{app_name}-{timestamp}`

#### Point de Terminaison API
```
POST /api/qchat_developer
```

**Corps de Requête:**
```json
{
  "message": "Ajouter un nouveau point de terminaison API pour la gestion des utilisateurs",
  "application_name": "MonApp",
  "application_folder": "/chemin/vers/app",
  "auto_approve": true,
  "gitea_url": "http://localhost:3000/gitadmin/branch-name",
  "userid": "1",
  "username": "agent"
}
```

### Agent Opérations Q Chat

#### Capacités de l'Agent
- **Gestion de Déploiement:** Gère les opérations START, STOP, RESTART
- **Opérations d'Infrastructure:** Gère les serveurs et ressources
- **Surveillance:** Vérifie le statut et les journaux des applications
- **Mise à l'Échelle:** Gère la capacité et les performances des applications
- **Dépannage:** Diagnostique et résout les problèmes de déploiement
- **Support Multi-Serveurs:** Allocation automatique de serveur basée sur la capacité

#### Point de Terminaison API
```
POST /api/qchat_operations
```

**Corps de Requête:**
```json
{
  "message": "[START] Démarrer l'application",
  "application_name": "MonApp",
  "application_folder": "/chemin/vers/app"
}
```

### Flux de Travail des Agents

#### 1. Configuration de l'Application
- Enregistrer le compte utilisateur agent via le point de terminaison `/register`
- Ajouter l'application avec le dépôt Git (admin requis)
- Cloner l'application vers le répertoire de déploiement
- Allocation automatique de serveur basée sur la capacité

#### 2. Phase de Développement (Agent Développeur)
- Analyser la structure de la base de code existante
- Implémenter de nouvelles fonctionnalités ou corrections en langage naturel
- Créer des branches Git horodatées pour le suivi
- Modifier les fichiers de configuration et dépendances
- Tester le déploiement avec `deployApp.sh`

#### 3. Phase de Déploiement (Agent Opérations)
- Démarrer les services d'application avec contexte utilisateur
- Surveiller le statut de déploiement avec mises à jour temps réel
- Vérifier les journaux et la santé de l'application
- Gérer le cycle de vie de l'application (start/stop/restart)
- Gérer la capacité serveur et l'allocation des ressources

### Fonctionnalités de la Plateforme

#### Support Multi-Langues
- **Basculement Langue Navbar:** Changement FR/EN dans la barre de navigation
- **Persistance Session:** Préférence de langue stockée dans la session utilisateur
- **Documentation:** Tous les guides disponibles en Anglais et Français
- **Changement Dynamique:** Modifications de langue temps réel sans rechargement de page

#### Organisation de Navigation
- **Onglet Applications:** Interface principale de gestion d'applications
- **Onglet Facturation:** Suivi des coûts et surveillance d'utilisation
- **Menu Déroulant Configuration:** Accès admin aux Utilisateurs, Serveurs, Base de données
- **Menu Déroulant Aide:** Accès direct aux guides Architecture, Déploiement et Utilisateur
- **Responsive Mobile:** Menu hamburger pour appareils mobiles

#### Fonctionnalités du Tableau de Bord
- **Statut Temps Réel:** Mises à jour en direct toutes les 10 secondes
- **Journaux Streaming:** Server-Sent Events pour visualisation de journaux temps réel
- **Cartes d'Application:** Interface visuelle pour gestion d'applications
- **Boutons d'Action:** Clone, Start, Stop, Status, Logs pour chaque application
- **Agents Virtuels:** Basculement entre agents Développeur et Opérations

#### Authentification et Sécurité
- **Authentification Basée Session:** Connexion sécurisée avec gestion de session
- **Support Token SSO:** Intégration Single Sign-On
- **Isolation Utilisateur:** Chaque utilisateur obtient des répertoires de déploiement isolés
- **Contrôles Admin:** Interface admin séparée pour gestion système

### Dépannage

#### Échecs d'Authentification
- Vérifier que les cookies de session sont inclus dans les requêtes
- Vérifier si le compte agent a les permissions appropriées
- S'assurer que le token SSO est valide et non expiré
- Confirmer que le compte utilisateur n'est pas suspendu

#### Problèmes de l'Agent Développeur
- Vérifier que le chemin du dossier d'application existe et est accessible
- Vérifier si l'application a les permissions de fichier appropriées
- S'assurer que le dépôt Git est accessible et les identifiants sont valides
- Confirmer que le serveur Gitea fonctionne et est accessible

#### Problèmes de l'Agent Opérations
- Vérifier si les scripts de déploiement (`deployApp.sh`) sont exécutables
- Vérifier que les services Docker fonctionnent sur le serveur cible
- S'assurer que le serveur a suffisamment de ressources (CPU, mémoire, disque)
- Confirmer la connectivité réseau entre serveurs

#### Problèmes de Changement de Langue
- Vider le cache et cookies du navigateur
- Vérifier que la session Flask est correctement maintenue
- Vérifier que la préférence de langue est stockée en session
- S'assurer que JavaScript est activé pour le changement de contenu dynamique

#### Commandes de Débogage
```bash
# Vérifier le statut d'authentification de l'agent
curl https://www.swautomorph.com/api/auth/status

# Vérifier que l'application existe
curl https://www.swautomorph.com/api/applications

# Vérifier la capacité et allocation serveur
curl https://www.swautomorph.com/api/servers

# Tester la communication agent
curl -X POST /api/qchat_developer \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your-session-cookie" \
  -d '{"message":"test connection","application_name":"test"}'
```