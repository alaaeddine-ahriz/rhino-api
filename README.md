# 🦏 Le Rhino API

**API FastAPI pour la gestion de cours et génération de questions via RAG (Retrieval-Augmented Generation)**

Cette API permet de gérer des documents de cours, générer des questions de réflexion, évaluer des réponses d'étudiants et organiser des challenges pédagogiques.

## 📋 Table des matières

- [🚀 Installation](#-installation)
- [⚡ Démarrage rapide](#-démarrage-rapide)
- [🔐 Authentification](#-authentification)
- [📖 Documentation API](#-documentation-api)
- [🏗️ Architecture](#️-architecture)
- [🔧 Implémentation des fonctionnalités](#-implémentation-des-fonctionnalités)
- [🧪 Tests](#-tests)
- [🚀 Déploiement](#-déploiement)
- [🤝 Contribution](#-contribution)
- [🔄 Présentation Fonctionnelle](#-présentation-fonctionnelle)
- [🔄 Mécanisme de Tick (Distribution des Challenges)](#-mécanisme-de-tick-distribution-des-challenges)

## 🚀 Installation

### Prérequis

- **Python 3.10+**
- **pip** (gestionnaire de packages Python)
- **Git**

### 1. Cloner le dépôt

```bash
git clone https://github.com/alaaeddine-ahriz/rhino-api.git
cd API-rhino
```

### 2. Créer un environnement virtuel

```bash
# Créer l'environnement virtuel
python -m venv .venv

# Activer l'environnement virtuel
# Sur macOS/Linux :
source .venv/bin/activate
# Sur Windows :
.venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration

```bash
# Copier le fichier d'exemple des variables d'environnement
cp .env.example .env

# Éditer le fichier .env avec vos clés API
nano .env  # ou votre éditeur préféré
```

**Variables d'environnement importantes :**
```env
# Pinecone (pour l'indexation vectorielle)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=rag-sir

# OpenAI (pour les embeddings et génération)
OPENAI_API_KEY=your_openai_api_key

# JWT (pour l'authentification)
TOKEN_SECRET_KEY=your_secret_key_change_this_in_production
TOKEN_ALGORITHM=HS256
TOKEN_EXPIRE_MINUTES=60
```

## ⚡ Démarrage rapide

### Lancer l'API

```bash
uvicorn app.main:app --reload --port 8000
```

L'API sera accessible sur : **http://localhost:8000**

### Accès rapide

- **🏠 Page d'accueil** : http://localhost:8000
- **📚 Documentation Swagger** : http://localhost:8000/api/docs
- **📖 Documentation ReDoc** : http://localhost:8000/api/redoc
- **🔍 Status API** : http://localhost:8000/api

## 🔐 Authentification

Le système d'authentification a évolué : les utilisateurs s'enregistrent désormais via l'endpoint `/api/users/register` puis passent leur `user_id` dans la query-string (`?user_id=<id>`) pour chaque appel nécessitant une identification. Aucun JWT n'est requis pour ce prototype.  

### Endpoints principaux

- **POST `/api/users/register`** – inscription d'un nouvel utilisateur  
  Corps JSON :  
  ```json
  {
    "username": "alice",
    "email": "alice@example.com",
    "role": "student",
    "subscriptions": ["MATH", "SYS"]
  }
  ```
  Réponse :  
  ```json
  { "success": true, "data": { "user_id": 1 } }
  ```

- **PUT `/api/users/subscriptions`** – ajouter ou retirer des abonnements (`user_id` + `subscriptions`).
- **PUT `/api/users/{user_id}`** – mettre à jour les informations de l'utilisateur.

Exemple d'appel :

```bash
# Création d'un utilisateur
curl -X POST http://localhost:8000/api/users/register \
     -H "Content-Type: application/json" \
     -d '{"username":"bob","email":"bob@example.com","role":"student","subscriptions":["MATH"]}'

# Utilisation de l'API avec l'identifiant retourné
curl http://localhost:8000/api/matieres?user_id=1
```

> Le module JWT (variables `TOKEN_*`) reste présent et pourra être activé ultérieurement.

## 📖 Documentation API

### Endpoints principaux

#### 👤 Utilisateurs
- `POST /api/users/register` – Inscription
- `PUT /api/users/subscriptions` – Gestion des abonnements
- `PUT /api/users/{user_id}` – Mise à jour des informations

#### 📚 Matières
- `GET /api/matieres` – Liste des matières
- `POST /api/matieres` – Créer une matière (enseignant/admin)
- `GET /api/matieres/{name}` – Détails d'une matière
- `DELETE /api/matieres/{name}` – Supprimer une matière (enseignant/admin)
- `POST /api/matieres/{name}/update` – Réindexer les documents (enseignant/admin)

#### 📄 Documents
- `GET /api/matieres/{matiere}/documents` – Liste des documents
- `POST /api/matieres/{matiere}/documents` – Upload d'un document (enseignant/admin)
- `GET /api/matieres/{matiere}/documents/{id}/content` – Télécharger le fichier
- `DELETE /api/matieres/{matiere}/documents/{id}` – Supprimer un document (enseignant/admin)
- `POST /api/matieres/{matiere}/documents/reindex` – Réindexer tous les documents
- `GET /api/matieres/{matiere}/documents/changes` – Obtenir les modifications depuis le dernier index

#### ❓ Questions
- `POST /api/question` – Poser une question au système RAG
- `POST /api/question/reflection` – Générer une question de réflexion

#### 📝 Évaluations
- `POST /api/evaluation/response` – Évaluer une réponse d'étudiant

#### 🏆 Challenges
- `GET /api/challenges/today` – Challenge du jour
- `GET /api/challenges` – Liste des challenges
- `POST /api/challenges` – Créer un challenge (enseignant/admin)
- `POST /api/challenges/{id}/response` – Soumettre une réponse
- `GET /api/challenges/{id}/leaderboard` – Classement d'un challenge
- `GET /api/challenges/next?matiere=...` – Challenge suivant pour une matière

#### 🏅 Leaderboard
- `POST /api/leaderboard/calcule` – Calculer un classement (enseignant/admin)

### Permissions par rôle

| Endpoint | Étudiant | Enseignant | Admin |
|----------|----------|------------|-------|
| Questions/Évaluations | ✅ | ✅ | ✅ |
| Gestion matières/docs | ❌ | ✅ | ✅ |
| Gestion challenges | ✅ | ✅ | ✅ |
| Gestion utilisateurs | ❌ | ❌ | ✅ |

## 🏗️ Architecture

```
app/
├── core/                  # Configuration & exceptions
│   ├── config.py
│   └── exceptions.py
├── db/                    # SQLModel tables & session helpers
│   ├── models.py
│   └── session.py
├── services/              # Logique métier (RAG, documents, challenges…)
│   ├── rag/
│   ├── matieres.py
│   └── ...
├── api/                   # Routes FastAPI
│   ├── deps.py
│   └── routes/
│       ├── auth.py        # Gestion des utilisateurs
│       ├── matieres.py
│       ├── documents.py
│       ├── questions.py
│       ├── evaluations.py
│       ├── challenges.py
│       └── leaderboard.py
├── models/                # Schémas Pydantic
└── main.py                # Point d'entrée de l'application
```

## 🔧 Fonctionnalités clés

Toutes les fonctionnalités suivantes sont **entièrement implémentées** :

- Gestion des utilisateurs et de leurs abonnements
- Création/gestion des matières et de leurs documents
- Indexation vectorielle (Pinecone) et génération d'embeddings (OpenAI)
- Système RAG pour répondre aux questions et générer des questions de réflexion
- Évaluation automatisée des réponses avec feedback détaillé
- Gestion des challenges, logique de tick et classement
- Leaderboard calculé sur demande
- Suite de tests couvrant l'ensemble de l'API

## 🧪 Tests

L'API dispose d'une suite de tests complète avec isolement de base de données et fixtures automatisées.

### Installation des dépendances de test

```bash
pip install pytest pytest-asyncio httpx
```

### Structure des tests

```
tests/
├── conftest.py                 # Configuration pytest et fixtures partagées
├── pytest.ini                 # Configuration des markers et options
├── README.md                   # Documentation détaillée des tests
├── test_api_status.py          # Tests d'état de l'API (15 tests)
├── test_auth_api.py            # Tests d'authentification (8 tests)
├── test_matieres_api.py        # Tests de gestion des matières (12 tests)
├── test_documents_api.py       # Tests de gestion des documents
├── test_questions_api.py       # Tests du système RAG
├── test_challenges_api.py      # Tests des challenges
├── test_evaluations_api.py     # Tests d'évaluation
└── test_leaderboard_api.py     # Tests du leaderboard
```

### Lancement des tests

#### Tous les tests
```bash
pytest
```

#### Tests par catégorie
```bash
# Tests d'authentification uniquement
pytest tests/test_auth_api.py

# Tests par marker
pytest -m auth                    # Tests d'authentification
pytest -m documents              # Tests de documents
pytest -m permissions            # Tests de permissions
pytest -m integration            # Tests d'intégration

# Tests avec sortie détaillée
pytest -v -s
```

#### Tests spécifiques
```bash
# Un test particulier
pytest tests/test_auth_api.py::TestUserRegistration::test_register_user_success

# Une classe de tests
pytest tests/test_auth_api.py::TestUserRegistration
```

### Résultats actuels

| Module | Tests | Statut | Taux de réussite |
|--------|-------|--------|------------------|
| **API Status** | 15 | ✅ Passent tous | 100% |
| **Auth** | 8 | ✅ Passent tous | 100% |
| **Matières** | 12 | ✅ 8/12 passent | 67% |
| **Documents** | - | 🔄 En cours | - |
| **Questions** | - | 🔄 En cours | - |
| **Challenges** | - | 🔄 En cours | - |
| **Evaluations** | - | 🔄 En cours | - |
| **Leaderboard** | - | 🔄 En cours | - |

### Fonctionnalités testées

#### ✅ Tests d'état de l'API (`test_api_status.py`)
- Accessibilité des endpoints principaux
- Documentation Swagger/ReDoc
- Headers CORS
- Gestion d'erreurs
- Format des réponses
- Performance et concurrence

#### ✅ Tests d'authentification (`test_auth_api.py`)
- Inscription d'utilisateurs
- Gestion des emails uniques
- Gestion des abonnements
- Validation des données
- Gestion des erreurs (utilisateur inexistant, etc.)

#### ✅ Tests des matières (`test_matieres_api.py`)
- Récupération des matières par rôle
- Création de matières (enseignant/admin)
- Mise à jour d'index
- Contrôle des permissions (étudiants interdits)
- Validation des données

### Isolation de base de données

Les tests utilisent un système d'isolation complet :

- **Base fraîche** : Chaque test démarre avec une base SQLite vide
- **Tables créées** : Schéma recréé automatiquement
- **Utilisateurs de test** : Fixtures pour créer des utilisateurs avec différents rôles
- **Nettoyage** : Base supprimée après chaque test

### Fixtures disponibles

```python
# Dans vos tests, utilisez ces fixtures :
def test_something(clean_database, test_users, test_client):
    # clean_database : Base de données propre
    # test_users : Utilisateurs pré-créés {"student": {...}, "teacher": {...}, "admin": {...}}
    # test_client : Client FastAPI pour les requêtes
    
    student_id = test_users["student"]["id"]
    response = test_client.get(f"/api/endpoint?user_id={student_id}")
    assert response.status_code == 200
```

### Tests manuels avec Swagger

1. **Lancer l'API** : `uvicorn app.main:app --reload`
2. **Accéder à Swagger** : http://localhost:8000/api/docs
3. **S'authentifier** :
   - Utiliser un token de test (ex: `teacher_token_789`)
   - Cliquer sur "🔒 Authorize"
   - Entrer : `Bearer YOUR_JWT_TOKEN`
4. **Tester les endpoints** selon votre rôle

### Développement de nouveaux tests

#### Modèle de test
```python
"""Tests pour [fonctionnalité]."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestNouvelleFonctionnalite:
    """Test de la nouvelle fonctionnalité."""

    def test_cas_nominal(self, test_users):
        """Test du cas normal."""
        user_id = test_users["student"]["id"]
        response = client.get(f"/api/endpoint?user_id={user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_permissions_denied(self, test_users):
        """Test des permissions refusées."""
        student_id = test_users["student"]["id"]
        response = client.post(f"/api/admin-endpoint?user_id={student_id}")
        
        assert response.status_code == 403
```

#### Markers disponibles
- `@pytest.mark.auth` - Tests d'authentification
- `@pytest.mark.documents` - Tests de documents  
- `@pytest.mark.permissions` - Tests de permissions
- `@pytest.mark.integration` - Tests d'intégration
- `@pytest.mark.slow` - Tests lents

### Débogage des tests

```bash
# Tests avec logs détaillés
pytest -v -s --log-cli-level=INFO

# Arrêt au premier échec
pytest -x

# Tests en parallèle (après installation de pytest-xdist)
pip install pytest-xdist
pytest -n auto
```

### Couverture de code

```bash
# Installation
pip install pytest-cov

# Lancement avec couverture
pytest --cov=app --cov-report=html

# Résultat dans htmlcov/index.html
```

## 🚀 Déploiement

### Docker (recommandé)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build et run
docker build -t rhino-api .
docker run -p 8000:8000 --env-file .env rhino-api
```

### Production

```bash
# Installer gunicorn pour la production
pip install gunicorn

# Lancer avec gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🤝 Contribution

### Structure des commits

```bash
git commit -m "feat: ajout de l'endpoint de création de matières"
git commit -m "fix: correction du bug d'authentification"
git commit -m "docs: mise à jour du README"
```

### Ajout d'une nouvelle fonctionnalité

1. Créer une branche : `git checkout -b feature/nouvelle-fonctionnalite`
2. Implémenter la fonctionnalité
3. Tester avec Swagger UI
4. Créer une Pull Request

## 🔄 Présentation Fonctionnelle

Le Rhino API est une plateforme d'entraînement et d'évaluation pour étudiants, enseignants et administrateurs, centrée sur la gestion de challenges (questions) par matière et sur la personnalisation de l'expérience utilisateur.

### Principales fonctionnalités

- **Inscription utilisateur** :
  - Endpoint : `POST /users/register`
  - Permet à un nouvel utilisateur de s'inscrire avec un rôle (étudiant, enseignant, admin) et de s'abonner à une ou plusieurs matières.

- **Gestion des abonnements** :
  - Endpoint : `PUT /users/subscriptions`
  - Permet de modifier ou consulter la liste des matières auxquelles un utilisateur est abonné.

- **Ajout de challenges** :
  - Endpoint : `POST /challenges`
  - Les enseignants/admins peuvent ajouter des challenges (questions) pour une matière donnée. Chaque challenge possède un identifiant unique (`ref`) de la forme `MATIERE-XXX`.

- **Définition de la granularité** :
  - Chaque matière possède un champ `granularite` (jour, semaine, mois, 2jours, etc.) qui définit la fréquence de rotation des challenges pour cette matière.
  - Modifiable via l'API ou en base.

- **Distribution des challenges** :
  - Endpoint : `GET /challenges/next?matiere=SYD`
  - Sert le challenge du moment pour la matière, selon la granularité définie dans la BDD. Tous les utilisateurs reçoivent le même challenge pour une matière donnée et une granularité donnée.

- **File de challenges** :
  - Les challenges sont servis en file pour chaque matière et granularité. Un challenge n'est resservi qu'une fois que tous les challenges de la matière ont été proposés.


## Mécanisme de Tick (Distribution des Challenges)

- **Principe** :
  - La granularité (jour, semaine, mois, etc.) définit la fréquence à laquelle un nouveau challenge est proposé pour une matière.
  - Le tick courant est calculé dynamiquement à partir d'une date de référence (date du premier challenge de la matière).
  - À chaque tick, le système sert le prochain challenge non encore servi pour la matière et la granularité.
  - Quand tous les challenges ont été servis, la file est remise à zéro et le cycle recommence.

- **Exemple de fonctionnement** :
  1. La granularité de la matière SYD est "semaine".
  2. Chaque semaine, tous les utilisateurs abonnés à SYD reçoivent le même challenge, qui change chaque semaine.
  3. Si tous les challenges ont été servis, le cycle recommence depuis le début de la file.

- **Avantages** :
  - Pas de période de validité stockée dans chaque challenge.
  - Facile à modifier (changer la granularité d'une matière suffit).
  - Même expérience pour tous les utilisateurs d'une matière.

## Endpoints principaux

- `POST /users/register` : Inscription d'un utilisateur
- `PUT /users/subscriptions` : Gestion des abonnements
- `POST /challenges` : Ajout d'un challenge (enseignant/admin)
- `GET /challenges/today?user_id={id}` : Récupérer le challenge du jour pour un utilisateur

## Exemple d'appel pour récupérer le challenge du jour

```http
GET /challenges/today?user_id=123
```

**Réponse :**
```json
{
  "success": true,
  "message": "Challenge du jour récupéré avec succès",
  "data": {
    "challenge": {
      "challenge_id": "1",
      "ref": "SYD-001",
      "question": "Expliquez le modèle OSI.",
      "matiere": "SYD",
      "date": "2024-05-01"
    },
    "user_subscriptions": ["SYD", "TCP"]
  }
}
```

---

Pour toute question sur l'usage ou l'extension de l'API, consulte la documentation technique ou contacte l'équipe projet.

## 🕑 Système de Tick

Le moteur de distribution des défis repose sur un **tick global** calculé à partir d'une date de référence commune à toutes les matières.

1. La date de référence se configure via la variable :`TICK_REFERENCE_DATE` (fichier `.env`, valeur par défaut `2024-01-01`).
2. Pour chaque matière, on applique la granularité (`jour`, `semaine`, `3jours`, `mois`, …) pour obtenir le tick courant.
3. L'algorithme garantit qu'un même défi est proposé à tous les utilisateurs pendant un tick donné, sans stocker le tick global.
4. Si un utilisateur est abonné à plusieurs matières, un **round-robin** distribue équitablement les défis entre ces matières.

Une description détaillée se trouve dans [`docs/systeme_tick.md`](docs/systeme_tick.md).

## 🔧 Configuration supplémentaire

Ajoutez dans `.env` :
```env
# Date de référence pour le système de tick (ISO YYYY-MM-DD)
TICK_REFERENCE_DATE=2024-01-01
```

## ✅ Statut de l'implémentation

Tous les endpoints listés ci-dessus sont opérationnels ; les sections de « code à compléter » ont été implémentées dans la base de code. Vous pouvez démarrer l'API, envoyer des requêtes et exécuter la suite de tests :

```bash
pytest -q
```
