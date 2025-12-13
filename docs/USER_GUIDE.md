# 🤖 AI-SwAutoMorph Agent Guide / Guide des Agents AI-SwAutoMorph

## English

### Table of Contents
- [Overview for AI Agents](#overview-for-ai-agents)
- [AI Agent Types](#ai-agent-types)
- [Q Chat Developer Agent](#q-chat-developer-agent)
- [Q Chat Operations Agent](#q-chat-operations-agent)
- [Agent Workflows](#agent-workflows)
- [Troubleshooting](#troubleshooting)

### Overview for AI Agents

AI-SwAutoMorph is specifically designed to enable GenAI agents to autonomously deploy, manage, and modify web applications without human intervention. The platform provides two specialized AI agents for complete application lifecycle management.

**Agent-Centric Design:** Built for autonomous AI agents to handle development, deployment, and operations tasks through intelligent automation.

### AI Agent Types

#### 🔧 Q Chat Developer Agent
**Purpose:** Code modification, feature development, and application enhancement

- Modifies source code based on natural language requests
- Adds new features and API endpoints
- Refactors and optimizes existing code
- Handles bug fixes and code improvements

#### 🚀 Q Chat Operations Agent
**Purpose:** Deployment operations, infrastructure management, and application lifecycle

- Handles deployment commands (START, STOP, RESTART)
- Manages application lifecycle and monitoring
- Performs infrastructure operations
- Executes deployment scripts and configurations

![Virtual Operations](https://www.swautomorph.com/static/VirtualOperations.png)

### Q Chat Developer Agent

#### Agent Capabilities
- **Code Analysis:** Understands existing codebase structure
- **Feature Development:** Adds new functionality based on requirements
- **API Creation:** Generates new REST endpoints and handlers
- **Code Refactoring:** Improves code quality and performance
- **Bug Resolution:** Identifies and fixes code issues

#### API Endpoint
```
POST /api/qchat_developer
```

**Request Body:**
```json
{
  "message": "Add a new API endpoint for user management",
  "application_name": "MyApp",
  "application_folder": "/path/to/app"
}
```

### Q Chat Operations Agent

#### Agent Capabilities
- **Deployment Management:** Handles START, STOP, RESTART operations
- **Infrastructure Operations:** Manages servers and resources
- **Monitoring:** Checks application status and logs
- **Scaling:** Manages application capacity and performance
- **Troubleshooting:** Diagnoses and resolves deployment issues

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

---

## Français

### Table des Matières
- [Aperçu pour les Agents IA](#aperçu-pour-les-agents-ia)
- [Types d'Agents IA](#types-dagents-ia)
- [Agent Développeur Q Chat](#agent-développeur-q-chat)
- [Agent Opérations Q Chat](#agent-opérations-q-chat)
- [Flux de Travail des Agents](#flux-de-travail-des-agents)
- [Dépannage](#dépannage)

### Aperçu pour les Agents IA

AI-SwAutoMorph est spécifiquement conçu pour permettre aux agents GenAI de déployer, gérer et modifier de manière autonome des applications web sans intervention humaine. La plateforme fournit deux agents IA spécialisés pour une gestion complète du cycle de vie des applications.

**Conception Axée sur les Agents:** Conçu pour les agents IA autonomes pour gérer les tâches de développement, déploiement et opérations grâce à l'automatisation intelligente.

### Types d'Agents IA

#### 🔧 Agent Développeur Q Chat
**Objectif:** Modification de code, développement de fonctionnalités et amélioration d'applications

- Modifie le code source basé sur des demandes en langage naturel
- Ajoute de nouvelles fonctionnalités et points de terminaison API
- Refactorise et optimise le code existant
- Gère les corrections de bugs et améliorations de code

#### 🚀 Agent Opérations Q Chat
**Objectif:** Opérations de déploiement, gestion d'infrastructure et cycle de vie des applications

- Gère les commandes de déploiement (START, STOP, RESTART)
- Gère le cycle de vie et la surveillance des applications
- Effectue les opérations d'infrastructure
- Exécute les scripts et configurations de déploiement

![Virtual Operations](https://www.swautomorph.com/static/VirtualOperations.png)

### Agent Développeur Q Chat

#### Capacités de l'Agent
- **Analyse de Code:** Comprend la structure de la base de code existante
- **Développement de Fonctionnalités:** Ajoute de nouvelles fonctionnalités basées sur les exigences
- **Création d'API:** Génère de nouveaux points de terminaison REST et gestionnaires
- **Refactorisation de Code:** Améliore la qualité et les performances du code
- **Résolution de Bugs:** Identifie et corrige les problèmes de code

#### Point de Terminaison API
```
POST /api/qchat_developer
```

**Corps de Requête:**
```json
{
  "message": "Ajouter un nouveau point de terminaison API pour la gestion des utilisateurs",
  "application_name": "MonApp",
  "application_folder": "/chemin/vers/app"
}
```

### Agent Opérations Q Chat

#### Capacités de l'Agent
- **Gestion de Déploiement:** Gère les opérations START, STOP, RESTART
- **Opérations d'Infrastructure:** Gère les serveurs et ressources
- **Surveillance:** Vérifie le statut et les journaux des applications
- **Mise à l'Échelle:** Gère la capacité et les performances des applications
- **Dépannage:** Diagnostique et résout les problèmes de déploiement

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