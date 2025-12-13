# Database Architecture and Improvements / Architecture et Améliorations de Base de Données

## English

### Overview

The AI-SwAutoMorph platform uses a comprehensive SQLite database with thread-safe connection management, automatic retry logic, and health monitoring to prevent database lock issues and ensure reliable operation across multiple concurrent users and deployments.

### Database Schema

#### Core Tables

##### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    suspended INTEGER DEFAULT 1,        -- 0=active, 1=suspended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### Applications Table
```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    git_url TEXT,                       -- Git repository URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Thread-Safe Connection Manager

```python
class DatabaseManager:
    """Thread-safe database manager with connection pooling"""
    
    def __init__(self):
        self._local = threading.local()
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections"""
        conn = self._get_connection()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise
```

---

## Français

### Aperçu

La plateforme AI-SwAutoMorph utilise une base de données SQLite complète avec gestion de connexions thread-safe, logique de retry automatique et surveillance de santé pour prévenir les problèmes de verrouillage de base de données et assurer un fonctionnement fiable avec plusieurs utilisateurs et déploiements simultanés.

### Schéma de Base de Données

#### Tables Principales

##### Table Users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    suspended INTEGER DEFAULT 1,        -- 0=actif, 1=suspendu
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

##### Table Applications
```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    git_url TEXT,                       -- URL du dépôt Git
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Gestionnaire de Connexions Thread-Safe

```python
class DatabaseManager:
    """Gestionnaire de base de données thread-safe avec pool de connexions"""
    
    def __init__(self):
        self._local = threading.local()
    
    @contextmanager
    def get_db_connection(self):
        """Gestionnaire de contexte pour les connexions de base de données"""
        conn = self._get_connection()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            raise
```