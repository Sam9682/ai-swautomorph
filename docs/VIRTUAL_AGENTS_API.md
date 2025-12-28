# 🤖 Virtual AI Agents API Reference / Référence API des Agents IA Virtuels

## English

<div class="center">
🚀 **Virtual AI Agents for Autonomous Application Management** 🌟
</div>

### 📋 Table of Contents
- [🌟 Overview](#overview)
- [🔧 Q Chat Developer Agent](#q-chat-developer-agent)
- [🚀 Q Chat Operations Agent](#q-chat-operations-agent)
- [📡 Streaming API](#streaming-api)
- [🎯 Context-Aware Prompts](#context-aware-prompts)
- [💰 Billing Integration](#billing-integration)
- [🔧 Error Handling](#error-handling)

### 🌟 Overview

AI-SwAutoMorph provides two specialized virtual AI agents designed for autonomous application management:

- **🔧 Q Chat Developer Agent**: Code modification, feature development, and application enhancement
- **🚀 Q Chat Operations Agent**: Deployment operations, infrastructure management, and application lifecycle

Both agents support:
- ⚡ **Streaming responses** with Server-Sent Events
- 🎯 **Context-aware prompts** from shared configuration files
- ⏱️ **Timeout management** with graceful cleanup (30 minutes)
- 💰 **Automatic billing** activity recording
- 🔄 **Fallback modes** for error scenarios

### 🔧 Q Chat Developer Agent

**Endpoint**: `POST /api/qchat_developer`

**Purpose**: Autonomous code modification and feature development using natural language instructions.

#### 🛠️ Capabilities
- 💻 **Code Analysis**: Understands existing codebase structure
- ⚡ **Feature Development**: Adds new functionality based on requirements
- 🔌 **API Creation**: Generates new REST endpoints and handlers
- 🔄 **Code Refactoring**: Improves code quality and performance
- 🐛 **Bug Resolution**: Identifies and fixes code issues
- 🌿 **Git Integration**: Creates branches with format `{user_id}-automorph-{app_name}-{timestamp}`

#### 📝 Request Format
```json
{
  "message": "Add a new API endpoint for user management with CRUD operations",
  "application_name": "MyApp",
  "application_folder": "/home/ubuntu/deployments/user123/myapp",
  "action_operation": "MODIFY_CODE"
}
```

#### 📋 Request Parameters
- **message** (required): Natural language description of the code changes needed
- **application_name** (required): Name of the application to modify
- **application_folder** (required): Full path to the application directory
- **action_operation** (optional): Specific operation type (defaults to "MODIFY_CODE")

#### 🎯 Context Loading
The agent automatically loads context from `/home/ubuntu/ai-swautomorph/shared/MODIFY_CODE_context.md` which includes:
- Application-specific configuration
- User context and permissions
- Git repository information
- Development guidelines and standards

#### 📡 Streaming Response
```javascript
// JavaScript example for handling streaming response
const eventSource = new EventSource('/api/qchat_developer', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(requestData)
});

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.chunk) {
    console.log('Progress:', data.chunk);
  }
  if (data.done) {
    console.log('Completed:', data.success);
    eventSource.close();
  }
  if (data.error) {
    console.error('Error:', data.error);
    eventSource.close();
  }
};
```

#### 🔄 Timeout Management
- **Duration**: 30 minutes (1800 seconds)
- **Graceful Termination**: SIGTERM followed by SIGKILL if needed
- **Cleanup**: Automatic process group termination
- **Logging**: Timeout events logged with timestamps

### 🚀 Q Chat Operations Agent

**Endpoint**: `POST /api/qchat_operations`

**Purpose**: Autonomous deployment operations and infrastructure management.

#### 🛠️ Capabilities
- 🚀 **Deployment Management**: START, STOP, RESTART operations
- 🏗️ **Infrastructure Operations**: Server and resource management
- 📊 **Monitoring**: Application status and health checks
- 📋 **Log Management**: Real-time log viewing and analysis
- 🔍 **Process Status**: PS command execution and monitoring
- 🔧 **Troubleshooting**: Automated problem diagnosis

#### 📝 Request Format
```json
{
  "message": "[START] Start the application with full monitoring",
  "application_name": "MyApp",
  "application_folder": "/home/ubuntu/deployments/user123/myapp",
  "action_operation": "START"
}
```

#### 📋 Request Parameters
- **message** (required): Natural language description or command
- **application_name** (required): Name of the application to manage
- **application_folder** (required): Full path to the application directory
- **action_operation** (optional): Specific operation (START, STOP, RESTART, PS, LOGS)

#### 🎯 Context-Aware Operations

The agent loads different context files based on the operation:

**Available Context Files**:
- `START_context.md` - Application startup procedures
- `STOP_context.md` - Graceful shutdown procedures
- `RESTART_context.md` - Restart and recovery procedures
- `PS_context.md` - Process status monitoring
- `LOGS_context.md` - Log analysis and monitoring

**Fallback Mode**: If no specific context is found, the agent operates in Q&A mode for general assistance.

#### 💰 Billing Integration
Automatic billing activity recording for:
- **START** operations: Records application startup time and costs
- **STOP** operations: Calculates duration and final costs
- **Cost Calculation**: Based on application-specific rates from `application_costs` table

### 📡 Streaming API

Both agents support real-time streaming responses using Server-Sent Events (SSE).

#### 🔌 Response Format
```
data: {"chunk": "Starting Q Chat Developer session..."}

data: {"chunk": "Found Q Chat at: /home/ubuntu/.local/bin/qchat"}

data: {"chunk": "Executing Q Chat command..."}

data: {"chunk": "Code modification completed successfully"}

data: {"done": true, "success": true, "returncode": 0}
```

#### 📋 Response Fields
- **chunk**: Progress message or output line
- **done**: Boolean indicating completion
- **success**: Boolean indicating success/failure
- **returncode**: Process exit code
- **error**: Error message if operation failed

#### 🌐 HTTP Headers
```
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
Connection: keep-alive
```

### 🎯 Context-Aware Prompts

The virtual agents use context-aware prompts loaded from the `shared/` directory:

#### 📁 Context File Structure
```
shared/
├── MODIFY_CODE_context.md    # Developer agent context
├── START_context.md          # Start operation context
├── STOP_context.md           # Stop operation context
├── RESTART_context.md        # Restart operation context
├── PS_context.md             # Process status context
└── LOGS_context.md           # Log analysis context
```

#### 🔄 Variable Substitution
Context files support dynamic variable replacement:
- `{USER_ID}` - Current user ID
- `{USER_NAME}` - User's full name
- `{USER_EMAIL}` - User's email address
- `{APPLICATION_FOLDER}` - Application directory path
- `{TAIL_LINES}` - Number of log lines to display (default: 100)

#### 🛡️ Security Features
- **Path Traversal Protection**: Sanitizes action names to prevent directory traversal
- **Input Validation**: Validates all user inputs before processing
- **Permission Checks**: Verifies user permissions for operations
- **Process Isolation**: Uses process groups for secure execution

### 💰 Billing Integration

#### 📊 Automatic Activity Recording
```sql
-- Billing activities table structure
CREATE TABLE billing_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    duration_seconds INTEGER,
    cost_amount REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 💳 Cost Calculation
- **START Action**: Records start time, calculates ongoing costs
- **STOP Action**: Records stop time, calculates total duration and cost
- **Rate Lookup**: Uses `application_costs` table for per-day rates
- **Prorated Billing**: Calculates costs based on actual usage time

### 🔧 Error Handling

#### ⚠️ Common Error Scenarios
1. **Authentication Failure**: Missing or invalid session
2. **Permission Denied**: User lacks required permissions
3. **Application Not Found**: Invalid application name or path
4. **Timeout Exceeded**: Operation exceeds 30-minute limit
5. **Process Failure**: Q Chat execution fails
6. **Context Loading Error**: Missing or invalid context files

#### 🛠️ Error Response Format
```json
{
  "error": "Authentication required",
  "code": 401,
  "details": "User session not found or expired"
}
```

#### 🔄 Retry Mechanisms
- **Database Locks**: Automatic retry with exponential backoff
- **Process Failures**: Graceful cleanup and error reporting
- **Network Issues**: Connection timeout handling
- **Resource Constraints**: Memory and CPU limit management

---

## Français

<div class="center">
🚀 **Agents IA Virtuels pour la Gestion Autonome d'Applications** 🌟
</div>

### 📋 Table des Matières
- [🌟 Aperçu](#aperçu)
- [🔧 Agent Développeur Q Chat](#agent-développeur-q-chat)
- [🚀 Agent Opérations Q Chat](#agent-opérations-q-chat)
- [📡 API de Streaming](#api-de-streaming)
- [🎯 Prompts Contextuels](#prompts-contextuels)
- [💰 Intégration Facturation](#intégration-facturation)
- [🔧 Gestion d'Erreurs](#gestion-derreurs)

### 🌟 Aperçu

AI-SwAutoMorph fournit deux agents IA virtuels spécialisés conçus pour la gestion autonome d'applications :

- **🔧 Agent Développeur Q Chat** : Modification de code, développement de fonctionnalités et amélioration d'applications
- **🚀 Agent Opérations Q Chat** : Opérations de déploiement, gestion d'infrastructure et cycle de vie des applications

Les deux agents supportent :
- ⚡ **Réponses en streaming** avec Server-Sent Events
- 🎯 **Prompts contextuels** depuis des fichiers de configuration partagés
- ⏱️ **Gestion des timeouts** avec nettoyage gracieux (30 minutes)
- 💰 **Facturation automatique** avec enregistrement d'activité
- 🔄 **Modes de fallback** pour les scénarios d'erreur

### 🔧 Agent Développeur Q Chat

**Point de terminaison** : `POST /api/qchat_developer`

**Objectif** : Modification autonome de code et développement de fonctionnalités utilisant des instructions en langage naturel.

#### 🛠️ Capacités
- 💻 **Analyse de Code** : Comprend la structure de la base de code existante
- ⚡ **Développement de Fonctionnalités** : Ajoute de nouvelles fonctionnalités basées sur les exigences
- 🔌 **Création d'API** : Génère de nouveaux points de terminaison REST et gestionnaires
- 🔄 **Refactorisation de Code** : Améliore la qualité et les performances du code
- 🐛 **Résolution de Bugs** : Identifie et corrige les problèmes de code
- 🌿 **Intégration Git** : Crée des branches avec format `{user_id}-automorph-{app_name}-{timestamp}`

#### 📝 Format de Requête
```json
{
  "message": "Ajouter un nouveau point de terminaison API pour la gestion des utilisateurs avec opérations CRUD",
  "application_name": "MonApp",
  "application_folder": "/home/ubuntu/deployments/user123/monapp",
  "action_operation": "MODIFY_CODE"
}
```

### 🚀 Agent Opérations Q Chat

**Point de terminaison** : `POST /api/qchat_operations`

**Objectif** : Opérations de déploiement autonomes et gestion d'infrastructure.

#### 🛠️ Capacités
- 🚀 **Gestion de Déploiement** : Opérations START, STOP, RESTART
- 🏗️ **Opérations d'Infrastructure** : Gestion des serveurs et ressources
- 📊 **Surveillance** : Statut et vérifications de santé des applications
- 📋 **Gestion des Logs** : Visualisation et analyse des logs en temps réel
- 🔍 **Statut des Processus** : Exécution et surveillance de la commande PS
- 🔧 **Dépannage** : Diagnostic automatisé des problèmes

#### 📝 Format de Requête
```json
{
  "message": "[START] Démarrer l'application avec surveillance complète",
  "application_name": "MonApp",
  "application_folder": "/home/ubuntu/deployments/user123/monapp",
  "action_operation": "START"
}
```

### 💰 Intégration Facturation

#### 📊 Enregistrement Automatique d'Activité
- **Action START** : Enregistre l'heure de début, calcule les coûts en cours
- **Action STOP** : Enregistre l'heure d'arrêt, calcule la durée totale et le coût
- **Recherche de Tarif** : Utilise la table `application_costs` pour les tarifs par jour
- **Facturation Proratisée** : Calcule les coûts basés sur le temps d'utilisation réel

### 🔧 Gestion d'Erreurs

#### ⚠️ Scénarios d'Erreur Courants
1. **Échec d'Authentification** : Session manquante ou invalide
2. **Permission Refusée** : L'utilisateur manque des permissions requises
3. **Application Non Trouvée** : Nom d'application ou chemin invalide
4. **Timeout Dépassé** : L'opération dépasse la limite de 30 minutes
5. **Échec de Processus** : L'exécution Q Chat échoue
6. **Erreur de Chargement de Contexte** : Fichiers de contexte manquants ou invalides