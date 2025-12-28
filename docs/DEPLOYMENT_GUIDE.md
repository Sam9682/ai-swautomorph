# Application Deployment Guide / Guide de Déploiement d'Applications

## English

### Overview

The AI-SwAutoMorph platform supports deploying applications across multiple servers with automatic capacity management, real-time monitoring, and GenAI-powered code evolution. Users can clone, start, stop, and monitor applications in their own isolated directories with full multi-server support and bilingual interface (English/French).

### Features

#### For All Users
- **Clone Applications**: Clone git repositories to your personal deployment directory
- **Multi-Server Deployment**: Automatic server allocation based on capacity
- **Start/Stop Applications**: Control application lifecycle using deployApp.sh scripts
- **Real-time Monitoring**: Live status updates and streaming logs via Server-Sent Events
- **GenAI Code Evolution**: Modify applications using natural language through Q Chat agents
- **Isolated Deployments**: Each user gets their own deployment directory
- **Billing Tracking**: Automatic cost tracking for application usage
- **Multi-Language Support**: Full English/French interface with navbar language switching

#### For Administrators
- **Server Management**: Add, configure, and monitor multiple deployment servers
- **User Management**: Create users, manage permissions, and track usage
- **Application Management**: Add git repository URLs and manage application catalog
- **Database Administration**: Direct database access and health monitoring
- **Cost Management**: Configure application costs and view billing reports
- **Documentation Management**: Bilingual markdown documentation with live editing

### Multi-Server Architecture

#### Server Types and Status
- **STAND_BY**: Server ready for new deployments
- **ACTIVE**: Server currently hosting deployments
- **MAINTENANCE**: Server temporarily unavailable

#### Capacity Management
```
Server Constraints:
- SERVER_CAPACITY_USER_MAX: Maximum users per server
- SERVER_CAPACITY_APPLI_MAX: Maximum applications per server
- Automatic allocation based on current utilization
```

#### Automatic Server Allocation
The platform automatically selects the optimal server based on:
1. Current server capacity utilization
2. Server status (prefers STAND_BY over ACTIVE)
3. Network connectivity and performance
4. Geographic location and latency

### How It Works

#### Directory Structure
```
/home/ubuntu/deployments/
├── username1/
│   ├── ai-haccp/
│   │   ├── deployApp.sh
│   │   ├── ssl/                  # Auto-synced SSL certificates
│   │   └── [application files]
│   └── ai-foodflow/
│       ├── deployApp.sh
│       └── [application files]
└── username2/
    └── ai-haccp/
        ├── deployApp.sh
        └── [application files]
```

#### Deployment Process

1. **Server Allocation**: System selects optimal server based on capacity
2. **Clone**: Downloads the git repository to `/home/ubuntu/deployments/{username}/{app-name}/`
3. **SSL Sync**: Automatically copies SSL certificates to deployment directory
4. **Deploy Commands**: Runs `deployApp.sh` with the specified command (start/stop/status/restart)
5. **Monitoring**: Tracks deployment status and provides real-time logs
6. **Billing**: Records usage for cost tracking with precise time measurement

### Usage

#### From Dashboard

1. **Clone Application**:
   - Click the "📥 Clone" button on any application card
   - System automatically allocates optimal server
   - Repository cloned with SSL certificates synced
   - Status shows as "cloning" then "cloned" when complete
   - Real-time progress updates via streaming

2. **Start Application**:
   - Click the "▶️ Start" button
   - Runs `./deployApp.sh start {user_id} "{user_name}" {user_email}` 
   - Real-time status updates and streaming logs available
   - Billing tracking automatically starts
   - Port allocation: HTTP_PORT = RANGE_START + user_id * RANGE_RESERVED + app_id * RANGE_PORTS_PER_APPLICATION

3. **Stop Application**:
   - Click the "⏹️ Stop" button
   - Runs `./deployApp.sh stop` in the application directory
   - Billing tracking automatically stops and calculates costs
   - Graceful shutdown with cleanup

4. **Check Status**:
   - Click the "📊 Status" button
   - Runs `./deployApp.sh ps` and shows current state with JSON output
   - Real-time application health monitoring
   - Docker container status and resource usage

5. **View Logs**:
   - Click the "📋 Logs" button
   - Opens modal with deployment status and streaming logs
   - Real-time log updates using Server-Sent Events
   - Filterable and searchable log output

6. **GenAI Code Evolution**:
   - Select application and click "Virtual Developer" toggle
   - Use natural language to request code modifications
   - System creates Git branch: `{user_id}-automorph-{app_name}-{timestamp}`
   - Automatic code modification, testing, and redeployment

#### API Endpoints

##### Server Management
```bash
# Get available servers
GET /api/servers

# Allocate server for deployment
POST /api/server/allocate
Content-Type: application/json
{
  "application_name": "AI HACCP"
}
```

##### Deployment Management
```bash
# Get user deployments
GET /api/deployments

# Create deployment with server allocation
POST /api/deployments
Content-Type: application/json
{
  "action": "clone|start|stop|status|restart|ps|logs",
  "application_name": "AI HACCP",
  "git_url": "https://github.com/Sam9682/ai-haccp.git",
  "server_id": 1,
  "stream": true  // Optional: enable real-time streaming
}
```

##### Enhanced GenAI Integration
```bash
# Q Chat Developer for code modification with context-aware prompts
POST /api/qchat_developer
Content-Type: application/json
{
  "message": "Add a health check endpoint with monitoring",
  "application_name": "AI HACCP",
  "application_folder": "/home/ubuntu/deployments/user/ai-haccp",
  "action_operation": "MODIFY_CODE"
}

# Q Chat Operations for deployment operations with streaming
POST /api/qchat_operations
Content-Type: application/json
{
  "message": "[START] Start the application with full monitoring",
  "application_name": "AI HACCP",
  "application_folder": "/home/ubuntu/deployments/user/ai-haccp",
  "action_operation": "START"
}

# Streaming deployment with real-time progress
POST /api/deployments
Content-Type: application/json
{
  "action": "start",
  "application_name": "AI HACCP",
  "stream": true,
  "server_id": 1
}
```

### Requirements

#### Application Requirements
Applications must include a `deployApp.sh` script that supports:
- `./deployApp.sh start {user_id} "{user_name}" {user_email}` - Start the application
- `./deployApp.sh stop` - Stop the application  
- `./deployApp.sh ps` - Show application status (JSON format preferred)
- `./deployApp.sh restart {user_id} "{user_name}" {user_email}` - Restart the application
- `./deployApp.sh logs` - Show application logs

#### System Requirements
- Git installed on all deployment servers
- Docker and Docker Compose (if applications use containers)
- SSH access between servers for remote deployment
- SSL certificates for HTTPS support
- Sufficient disk space for application deployments
- Network access to git repositories

### Troubleshooting

#### Common Issues

1. **Clone Failed**:
   - Check git URL is accessible from target server
   - Verify network connectivity between servers
   - Ensure sufficient disk space on target server
   - Check SSH key authentication for remote servers

2. **Deploy Commands Fail**:
   - Verify `deployApp.sh` exists and is executable
   - Check application dependencies are installed on target server
   - Review deployment logs for specific errors
   - Ensure Docker/Docker Compose is available if needed

3. **Language Switching Issues**:
   - Clear browser cache and cookies
   - Verify Flask session is maintained
   - Check JavaScript is enabled for dynamic content
   - Ensure language preference is stored in session

4. **Server Allocation Issues**:
   - Check server capacity limits in database
   - Verify server status is STAND_BY or ACTIVE
   - Ensure network connectivity to target servers
   - Review server health and resource availability

### Status Meanings

- `pending`: Command queued for execution
- `running`: Command currently executing
- `cloning`: Git clone in progress
- `cloned`: Repository successfully cloned
- `completed`: Command completed successfully
- `failed`: Command failed with error
- `timeout`: Command exceeded time limit
- `error`: System error occurred

---

## Français

### Aperçu

La plateforme AI-SwAutoMorph prend en charge le déploiement d'applications sur plusieurs serveurs avec gestion automatique de capacité, surveillance en temps réel et évolution de code alimentée par GenAI. Les utilisateurs peuvent cloner, démarrer, arrêter et surveiller les applications dans leurs propres répertoires isolés avec support multi-serveurs complet et interface bilingue (Anglais/Français).

### Fonctionnalités

#### Pour Tous les Utilisateurs
- **Cloner des Applications**: Cloner des dépôts git vers votre répertoire de déploiement personnel
- **Déploiement Multi-Serveurs**: Allocation automatique de serveur basée sur la capacité
- **Démarrer/Arrêter Applications**: Contrôler le cycle de vie des applications avec les scripts deployApp.sh
- **Surveillance Temps Réel**: Mises à jour de statut en direct et journaux en streaming via Server-Sent Events
- **Évolution de Code GenAI**: Modifier les applications en langage naturel via les agents Q Chat
- **Déploiements Isolés**: Chaque utilisateur obtient son propre répertoire de déploiement
- **Suivi de Facturation**: Suivi automatique des coûts d'utilisation des applications
- **Support Multi-Langues**: Interface complète Anglais/Français avec changement de langue navbar

#### Pour les Administrateurs
- **Gestion de Serveurs**: Ajouter, configurer et surveiller plusieurs serveurs de déploiement
- **Gestion d'Utilisateurs**: Créer des utilisateurs, gérer les permissions et suivre l'utilisation
- **Gestion d'Applications**: Ajouter des URLs de dépôts git et gérer le catalogue d'applications
- **Administration de Base de Données**: Accès direct à la base de données et surveillance de santé
- **Gestion des Coûts**: Configurer les coûts d'applications et voir les rapports de facturation
- **Gestion de Documentation**: Documentation markdown bilingue avec édition en direct

### Architecture Multi-Serveurs

#### Types et Statuts de Serveurs
- **STAND_BY**: Serveur prêt pour nouveaux déploiements
- **ACTIVE**: Serveur hébergeant actuellement des déploiements
- **MAINTENANCE**: Serveur temporairement indisponible

#### Gestion de Capacité
```
Contraintes Serveur:
- SERVER_CAPACITY_USER_MAX: Maximum d'utilisateurs par serveur
- SERVER_CAPACITY_APPLI_MAX: Maximum d'applications par serveur
- Allocation automatique basée sur l'utilisation actuelle
```

#### Allocation Automatique de Serveur
La plateforme sélectionne automatiquement le serveur optimal basé sur :
1. Utilisation actuelle de la capacité serveur
2. Statut serveur (préfère STAND_BY à ACTIVE)
3. Connectivité réseau et performance
4. Localisation géographique et latence

### Fonctionnement

#### Structure de Répertoires
```
/home/ubuntu/deployments/
├── username1/
│   ├── ai-haccp/
│   │   ├── deployApp.sh
│   │   ├── ssl/                  # Certificats SSL auto-synchronisés
│   │   └── [fichiers application]
│   └── ai-foodflow/
│       ├── deployApp.sh
│       └── [fichiers application]
└── username2/
    └── ai-haccp/
        ├── deployApp.sh
        └── [fichiers application]
```

#### Processus de Déploiement

1. **Allocation Serveur**: Le système sélectionne le serveur optimal basé sur la capacité
2. **Clone**: Télécharge le dépôt git vers `/home/ubuntu/deployments/{username}/{app-name}/`
3. **Sync SSL**: Copie automatiquement les certificats SSL vers le répertoire de déploiement
4. **Commandes Deploy**: Exécute `deployApp.sh` avec la commande spécifiée (start/stop/status/restart)
5. **Surveillance**: Suit le statut de déploiement et fournit des journaux temps réel
6. **Facturation**: Enregistre l'utilisation pour suivi des coûts avec mesure de temps précise

### Utilisation

#### Depuis le Tableau de Bord

1. **Cloner une Application**:
   - Cliquer sur le bouton "📥 Clone" sur n'importe quelle carte d'application
   - Le système alloue automatiquement le serveur optimal
   - Dépôt cloné avec certificats SSL synchronisés
   - Le statut affiche "cloning" puis "cloned" une fois terminé
   - Mises à jour de progression temps réel via streaming

2. **Démarrer une Application**:
   - Cliquer sur le bouton "▶️ Start"
   - Exécute `./deployApp.sh start {user_id} "{user_name}" {user_email}` 
   - Mises à jour de statut temps réel et journaux en streaming disponibles
   - Le suivi de facturation démarre automatiquement
   - Allocation de port: HTTP_PORT = RANGE_START + user_id * RANGE_RESERVED + app_id * RANGE_PORTS_PER_APPLICATION

3. **Arrêter une Application**:
   - Cliquer sur le bouton "⏹️ Stop"
   - Exécute `./deployApp.sh stop` dans le répertoire d'application
   - Le suivi de facturation s'arrête automatiquement et calcule les coûts
   - Arrêt gracieux avec nettoyage

4. **Vérifier le Statut**:
   - Cliquer sur le bouton "📊 Status"
   - Exécute `./deployApp.sh ps` et affiche l'état actuel avec sortie JSON
   - Surveillance de santé d'application temps réel
   - Statut conteneur Docker et utilisation des ressources

5. **Voir les Journaux**:
   - Cliquer sur le bouton "📋 Logs"
   - Ouvre modal avec statut de déploiement et journaux en streaming
   - Mises à jour de journaux temps réel utilisant Server-Sent Events
   - Sortie de journaux filtrable et recherchable

6. **Évolution de Code GenAI**:
   - Sélectionner l'application et cliquer sur le toggle "Virtual Developer"
   - Utiliser le langage naturel pour demander des modifications de code
   - Le système crée une branche Git: `{user_id}-automorph-{app_name}-{timestamp}`
   - Modification de code automatique, test et redéploiement

### Dépannage

#### Problèmes Courants

1. **Échec de Clone**:
   - Vérifier que l'URL git est accessible depuis le serveur cible
   - Vérifier la connectivité réseau entre serveurs
   - S'assurer d'un espace disque suffisant sur le serveur cible
   - Vérifier l'authentification par clé SSH pour serveurs distants

2. **Échec des Commandes Deploy**:
   - Vérifier que `deployApp.sh` existe et est exécutable
   - Vérifier que les dépendances d'application sont installées sur le serveur cible
   - Examiner les journaux de déploiement pour erreurs spécifiques
   - S'assurer que Docker/Docker Compose est disponible si nécessaire

3. **Problèmes de Changement de Langue**:
   - Vider le cache et cookies du navigateur
   - Vérifier que la session Flask est maintenue
   - Vérifier que JavaScript est activé pour le contenu dynamique
   - S'assurer que la préférence de langue est stockée en session

4. **Problèmes d'Allocation Serveur**:
   - Vérifier les limites de capacité serveur en base de données
   - Vérifier que le statut serveur est STAND_BY ou ACTIVE
   - S'assurer de la connectivité réseau vers les serveurs cibles
   - Examiner la santé serveur et disponibilité des ressources

### Significations des Statuts

- `pending`: Commande en file d'attente pour exécution
- `running`: Commande en cours d'exécution
- `cloning`: Clone git en cours
- `cloned`: Dépôt cloné avec succès
- `completed`: Commande terminée avec succès
- `failed`: Commande échouée avec erreur
- `timeout`: Commande a dépassé la limite de temps
- `error`: Erreur système survenue