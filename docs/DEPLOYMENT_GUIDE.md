# Application Deployment Guide / Guide de Déploiement d'Applications

## English

### Overview

The AI-SwAutoMorph platform supports deploying applications across multiple servers with automatic capacity management, real-time monitoring, and GenAI-powered code evolution. Users can clone, start, stop, and monitor applications in their own isolated directories with full multi-server support.

### Features

#### For All Users
- **Clone Applications**: Clone git repositories to your personal deployment directory
- **Multi-Server Deployment**: Automatic server allocation based on capacity
- **Start/Stop Applications**: Control application lifecycle using deployApp.sh scripts
- **Real-time Monitoring**: Live status updates and streaming logs
- **GenAI Code Evolution**: Modify applications using natural language through Q Chat
- **Isolated Deployments**: Each user gets their own deployment directory
- **Billing Tracking**: Automatic cost tracking for application usage

#### For Administrators
- **Server Management**: Add, configure, and monitor multiple deployment servers
- **User Management**: Create users, manage permissions, and track usage
- **Application Management**: Add git repository URLs and manage application catalog
- **Database Administration**: Direct database access and health monitoring
- **Cost Management**: Configure application costs and view billing reports

### Usage

#### From Dashboard

1. **Clone Application**:
   - Click the "📥 Clone" button on any application card
   - System automatically allocates optimal server
   - Repository cloned with SSL certificates synced
   - Status shows as "cloning" then "cloned" when complete

2. **Start Application**:
   - Click the "▶️ Start" button
   - Runs `./deployApp.sh start {user_id} "{user_name}" {user_email}` 
   - Real-time status updates and streaming logs available
   - Billing tracking automatically starts

---

## Français

### Aperçu

La plateforme AI-SwAutoMorph prend en charge le déploiement d'applications sur plusieurs serveurs avec gestion automatique de capacité, surveillance en temps réel et évolution de code alimentée par GenAI. Les utilisateurs peuvent cloner, démarrer, arrêter et surveiller les applications dans leurs propres répertoires isolés avec support multi-serveurs complet.

### Fonctionnalités

#### Pour Tous les Utilisateurs
- **Cloner des Applications**: Cloner des dépôts git vers votre répertoire de déploiement personnel
- **Déploiement Multi-Serveurs**: Allocation automatique de serveur basée sur la capacité
- **Démarrer/Arrêter Applications**: Contrôler le cycle de vie des applications avec les scripts deployApp.sh
- **Surveillance Temps Réel**: Mises à jour de statut en direct et journaux en streaming
- **Évolution de Code GenAI**: Modifier les applications en langage naturel via Q Chat
- **Déploiements Isolés**: Chaque utilisateur obtient son propre répertoire de déploiement
- **Suivi de Facturation**: Suivi automatique des coûts d'utilisation des applications

#### Pour les Administrateurs
- **Gestion de Serveurs**: Ajouter, configurer et surveiller plusieurs serveurs de déploiement
- **Gestion d'Utilisateurs**: Créer des utilisateurs, gérer les permissions et suivre l'utilisation
- **Gestion d'Applications**: Ajouter des URLs de dépôts git et gérer le catalogue d'applications
- **Administration de Base de Données**: Accès direct à la base de données et surveillance de santé
- **Gestion des Coûts**: Configurer les coûts d'applications et voir les rapports de facturation

### Utilisation

#### Depuis le Tableau de Bord

1. **Cloner une Application**:
   - Cliquer sur le bouton "📥 Clone" sur n'importe quelle carte d'application
   - Le système alloue automatiquement le serveur optimal
   - Dépôt cloné avec certificats SSL synchronisés
   - Le statut affiche "cloning" puis "cloned" une fois terminé

2. **Démarrer une Application**:
   - Cliquer sur le bouton "▶️ Start"
   - Exécute `./deployApp.sh start {user_id} "{user_name}" {user_email}` 
   - Mises à jour de statut en temps réel et journaux en streaming disponibles
   - Le suivi de facturation démarre automatiquement