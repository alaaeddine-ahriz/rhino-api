# Le Rhino API – Backend

## Introduction

Le backend FastAPI de l'application PWA « Le Rhino » gère l'indexation de cours, la génération et l'évaluation de questions, ainsi que l'administration de contenus (matières et documents). Cette API expose des endpoints clairs pour chaque fonctionnalité.

## Technologies et outils

- **Python 3.10+** : Langage principal pour le backend.
- **FastAPI** : Framework web asynchrone permettant la construction d'API REST rapides et documentées automatiquement.
- **Uvicorn** : Serveur ASGI léger et performant qui exécute l'application FastAPI en mode asynchrone, gérant la boucle d'événements et les requêtes concurrentes.
- **Pinecone** : Service vectoriel pour la création et la gestion d'index de recherche sémantique.
- **OpenAI embeddings** : Génération d'embeddings pour la recherche RAG.
- **Stockage local** : Organisation des cours et documents dans le système de fichiers, dossier par matière.
- **Pydantic** : Validation et sérialisation des données entrantes et sortantes à l'aide de modèles stricts (typage, contraintes, conversion automatique), garantissant l'intégrité des échanges.

## Prérequis

- Compte Pinecone (clé API)
- Clé OpenAI pour embeddings
- Python 3.10 ou supérieur
- `pip install -r requirements.txt`

## Installation

1. Cloner le dépôt :
    
    ```bash
    git clone https://github.com/alaaeddine-ahriz/rhino-v1-deprecated.git
    ```
    
2. Se placer dans le dossier :
    
    ```bash
    cd rhino-backend
    ```
    
3. Installer les dépendances :
    
    ```bash
    pip install -r requirements.txt
    ```
    
4. Copier le fichier d'environnement :
    
    ```bash
    cp .env.example .env
    ```
    
5. Remplir les variables d'environnement.

## Configuration

Variables d'environnement à définir dans `.env` :

```
# Pinecone
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
INDEX_NAME=rhino-index

# OpenAI
OPENAI_API_KEY=

# Auth
TOKEN_SECRET_KEY=
TOKEN_ALGORITHM=HS256
TOKEN_EXPIRE_MINUTES=60
```

## Structure du backend

Le point d'entrée se situe dans `main.py`. Le code suit une architecture modulaire avec :

- Initialisation de l'infrastructure Pinecone et embeddings.
- Gestion de l'arborescence locale des matières et documents.
- Endpoints REST exposant chaque fonctionnalité.

### Principales fonctions (stubs)

- `initialize_pinecone()`: connexion à Pinecone.
- `setup_embeddings()`: configuration du client OpenAI embeddings.
- `create_or_get_index(...)`: création ou récupération de l'index Pinecone.
- `initialiser_structure_dossiers()`: création des dossiers de cours.

- `interroger_matiere(...)`: recherche contextuelle dans une matière.
- `generer_question_reflexion(...)`: génération d'une question de réflexion.
- `evaluer_reponse(...)`: évaluation d'une réponse via IA/RAG et production d'un feedback détaillé.

## Endpoints de l'API

Tous les chemins sont préfixés par `/api` et retournent un modèle `ApiResponse`.

### Authentification

| Méthode | Chemin | Description |
| --- | --- | --- |
| POST | `/auth/token` | Génère un token JWT pour un utilisateur valide. |

### Matières

| Méthode | Chemin | Description |
| --- | --- | --- |
| GET | `/matieres` | Liste toutes les matières disponibles. |
| POST | `/matieres` | Crée une nouvelle matière (dossier). |
| DELETE | `/matieres/{id}` | Supprime une matière et tous ses documents. |

### Documents

| Méthode | Chemin | Description |
| --- | --- | --- |
| GET | `/matieres/{matiere}/documents` | Liste les documents uploadés pour la matière. |
| POST | `/matieres/{matiere}/documents` | Upload d'un document (PDF, DOCX, etc.). |
| DELETE | `/matieres/{matiere}/documents/{document_id}` | Supprime un document spécifié. |
| POST | `/matieres/{matiere}/documents/reindex` | Réindexe tous les documents d'une matière dans la base vectorielle. |

### Questions

| Méthode | Chemin | Description |
| --- | --- | --- |
| POST | `/question` | Recherche et renvoie une réponse libre. |
| POST | `/question/reflection` | Génère une question de réflexion sur un concept. |

### Évaluation

| Méthode | Chemin | Description |
| --- | --- | --- |
| POST | `/evaluation/response` | Évalue la réponse d'un étudiant et retourne un JSON. |

### Leaderboard

| Méthode | Chemin | Description |
| --- | --- | --- |
| POST | `/leaderboard/calcule` | Calcule et renvoie le classement d'un challenge donné. |

### Challenges

| Méthode | Chemin | Payload / Paramètres | Description |
| --- | --- | --- | --- |
| GET | `/challenges/today` | — | Récupère le challenge du jour selon la date serveur (`challengeId`, `date`, `question`, `matieres`). |
| GET | `/challenges` | QueryParam facultatif `matiere` | Liste tous les challenges, filtrables par matière ou plage de dates. |
| POST | `/challenges` | `{ "question": "Question text", "matiere": "MATH" }` | Crée un nouveau challenge pour une matière (date automatiquement définie). |
| POST | `/challenges/{challengeId}/response` | `{ "userId": "<id>", "response": "<texte>" }` | Soumet la réponse d'un utilisateur et l'enregistre ; peut déclencher une évaluation. |
| GET | `/challenges/{challengeId}/leaderboard` | — | Récupère le classement pour un challenge spécifique (`userId`, `score`, `rang`). |

## Flows utilisateur typiques

### Parcours Étudiant

1. **Connexion** : l'étudiant s'authentifie en envoyant ses identifiants à `POST /auth/token` et reçoit un JWT.
2. **Récupération du challenge du jour** : appel à `GET /challenges/today` pour obtenir la question et les matières associées.
3. **Soumission de la réponse** : envoi de la réponse via `POST /challenges/{challengeId}/response`.
4. **Évaluation** : la réponse peut être évaluée automatiquement ou manuellement. L'étudiant peut consulter son feedback via `POST /evaluation/response`.
5. **Classement** : consultation du classement du challenge avec `GET /challenges/{challengeId}/leaderboard`.

### Parcours Enseignant

1. **Connexion** : l'enseignant s'authentifie via `POST /auth/token` et obtient un JWT.
2. **Gestion des matières** : création de nouvelles matières via `POST /matieres` ou réindexation d'une matière existante avec `POST /matieres/{matiere}/documents/reindex`.
3. **Gestion des documents** : upload de supports pédagogiques (`POST /matieres/{matiere}/documents`) et suppression si nécessaire (`DELETE /matieres/{matiere}/documents/{document_id}`).
4. **Création de questions ou de challenges** : génération de questions de réflexion via `POST /question/reflection` ou création de challenges ciblés avec `POST /challenges`.
5. **Suivi des réponses** : récupération des réponses soumises par les étudiants (logique d'accès aux enregistrements de `POST /challenges/{challengeId}/response`).
6. **Évaluation des réponses** : évaluation manuelle ou semi-automatique via `POST /evaluation/response` pour fournir un feedback structuré.
7. **Analyse du classement** : consultation du leaderboard via `GET /challenges/{challengeId}/leaderboard` pour suivre la progression de la promotion.

## Authentification par token

1. L'utilisateur envoie ses identifiants à `/auth/token`.
2. Le serveur valide (stub) et renvoie un JWT.
3. Le token doit être inclus dans `Authorization: Bearer <token>`.
4. Toutes les routes sont protégées par un middleware JWT.

## Évolutions futures

- Intégration CAS / SSO.
- Notifications push.
- Gamification et badges.
- Interfaces utilisateur et d'administration dédiée.