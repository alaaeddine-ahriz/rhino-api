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

Le système utilise des **tokens pré-générés** stockés en base de données.

### Tokens de test disponibles

| Rôle | Username | Token |
|------|----------|-------|
| 👨‍🎓 Étudiant | student1 | `student_token_123` |
| 👨‍🎓 Étudiant | student2 | `student_token_456` |
| 👨‍🏫 Enseignant | teacher1 | `teacher_token_789` |
| 👨‍🏫 Enseignant | teacher2 | `teacher_token_101` |
| 👨‍💼 Admin | admin1 | `admin_token_999` |

### Comment s'authentifier

1. **Via Swagger UI :**
   - Allez sur `/api/docs`
   - Utilisez l'endpoint `POST /api/auth/token`
   - Entrez un token (ex: `{"token": "teacher_token_789"}`)
   - Copiez le JWT retourné
   - Cliquez "🔒 Authorize" → `Bearer YOUR_JWT_TOKEN`

2. **Via curl :**
```bash
# Obtenir un JWT
curl -X POST "http://localhost:8000/api/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"token": "teacher_token_789"}'

# Utiliser le JWT
curl -X GET "http://localhost:8000/api/matieres" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📖 Documentation API

### Endpoints principaux

#### 🔐 Authentification
- `POST /api/auth/token` - Obtenir un JWT avec un token pré-généré
- `GET /api/auth/tokens` - Lister tous les tokens (admin seulement)

#### 📚 Matières
- `GET /api/matieres` - Liste des matières
- `POST /api/matieres` - Créer une matière (enseignant+)
- `DELETE /api/matieres/{id}` - Supprimer une matière (enseignant+)
- `POST /api/matieres/{matiere}/documents/reindex` - Réindexer les documents d'une matière (enseignant+)

#### 📄 Documents
- `GET /api/matieres/{matiere}/documents` - Documents d'une matière
- `POST /api/matieres/{matiere}/documents` - Upload document (enseignant+)
- `DELETE /api/matieres/{matiere}/documents/{id}` - Supprimer document (enseignant+)

#### ❓ Questions
- `POST /api/question` - Poser une question au système RAG
- `POST /api/question/reflection` - Générer une question de réflexion

#### 📝 Évaluations
- `POST /api/evaluation/response` - Évaluer une réponse d'étudiant

#### 🏆 Challenges
- `GET /api/challenges/today` - Challenge du jour
- `GET /api/challenges` - Liste des challenges
- `POST /api/challenges` - Créer un challenge (enseignant+)
- `POST /api/challenges/{id}/response` - Soumettre une réponse
- `GET /api/challenges/{id}/leaderboard` - Classement d'un challenge

#### 🏅 Leaderboard
- `POST /api/leaderboard/calcule` - Calculer un classement (enseignant+)

### Permissions par rôle

| Endpoint | Étudiant | Enseignant | Admin |
|----------|----------|------------|-------|
| Questions/Évaluations | ✅ | ✅ | ✅ |
| Gestion matières/docs | ❌ | ✅ | ✅ |
| Gestion tokens | ❌ | ❌ | ✅ |

## 🏗️ Architecture

```
app/
├── core/                  # Configuration et utilitaires
│   ├── config.py         # Variables d'environnement
│   ├── security.py       # JWT et sécurité
│   └── exceptions.py     # Exceptions personnalisées
├── models/               # Modèles Pydantic
│   ├── auth.py          # Authentification
│   ├── matiere.py       # Matières
│   ├── document.py      # Documents
│   ├── question.py      # Questions
│   ├── evaluation.py    # Évaluations
│   └── challenge.py     # Challenges
├── api/                 # Routes et dépendances
│   ├── deps.py          # Dépendances (auth, permissions)
│   └── routes/          # Endpoints organisés par domaine
│       ├── auth.py
│       ├── matieres.py
│       ├── documents.py
│       ├── questions.py
│       ├── evaluations.py
│       ├── challenges.py
│       └── leaderboard.py
└── main.py              # Point d'entrée de l'application
```

## 🔧 Implémentation des fonctionnalités

La structure actuelle fournit les **endpoints et la validation**, mais les fonctionnalités métier restent à implémenter. Voici comment procéder :

### 1. 📚 Gestion des matières

**Fichier :** `app/api/routes/matieres.py`

```python
# Remplacer les placeholders par les vraies fonctions
from main import initialiser_structure_dossiers, mettre_a_jour_matiere

@router.post("/", response_model=ApiResponse)
async def create_matiere(matiere: MatiereCreate, current_user: UserInDB = Depends(get_teacher_user)):
    try:
        # Appeler la vraie fonction
        initialiser_structure_dossiers(matiere.name)
        return {"success": True, "message": f"Matière {matiere.name} créée"}
    except Exception as e:
        raise HTTPException(500, f"Erreur: {str(e)}")
```

### 2. 📄 Upload de documents

**Fichier :** `app/api/routes/documents.py`

```python
import shutil
from pathlib import Path

@router.post("/matieres/{matiere}/documents", response_model=ApiResponse)
async def upload_document(matiere: str, file: UploadFile = File(...), current_user: UserInDB = Depends(get_teacher_user)):
    try:
        # Créer le dossier de la matière
        matiere_dir = Path(f"cours/{matiere}")
        matiere_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier
        file_path = matiere_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Appeler la fonction d'indexation
        from main import mettre_a_jour_matiere
        mettre_a_jour_matiere(matiere)
        
        return {"success": True, "message": f"Document {file.filename} uploadé"}
    except Exception as e:
        raise HTTPException(500, f"Erreur: {str(e)}")
```

### 3. ❓ Questions RAG

**Fichier :** `app/api/routes/questions.py`

```python
from main import interroger_matiere, generer_question_reflexion

@router.post("/question", response_model=ApiResponse)
async def ask_question(request: QuestionRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        # Appeler la vraie fonction RAG
        result = interroger_matiere(
            matiere=request.matiere,
            query=request.query,
            output_format=request.output_format,
            save_output=request.save_output
        )
        return {"success": True, "message": "Réponse générée", "data": result}
    except Exception as e:
        raise HTTPException(500, f"Erreur: {str(e)}")
```

### 4. 📝 Évaluations

**Fichier :** `app/api/routes/evaluations.py`

```python
from main import evaluer_reponse_etudiant

@router.post("/evaluation/response", response_model=ApiResponse)
async def evaluate_student_response(request: EvaluationRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        result = evaluer_reponse_etudiant(
            matiere=request.matiere,
            question=request.question,
            reponse_etudiant=request.student_response,
            save_output=request.save_output
        )
        return {"success": True, "message": "Évaluation générée", "data": result}
    except Exception as e:
        raise HTTPException(500, f"Erreur: {str(e)}")
```

### 5. 🗄️ Base de données pour les challenges

Créer un système de persistance simple :

```python
# app/services/challenge_service.py
import json
from pathlib import Path
from datetime import date
from typing import List, Dict

CHALLENGES_DB = Path("challenges.json")

def save_challenge(challenge_data: Dict):
    """Sauvegarder un challenge."""
    challenges = load_challenges()
    challenges.append(challenge_data)
    with open(CHALLENGES_DB, "w") as f:
        json.dump(challenges, f, indent=2)

def load_challenges() -> List[Dict]:
    """Charger tous les challenges."""
    if not CHALLENGES_DB.exists():
        return []
    with open(CHALLENGES_DB, "r") as f:
        return json.load(f)

def get_today_challenge() -> Dict:
    """Récupérer le challenge du jour."""
    today = date.today().isoformat()
    challenges = load_challenges()
    return next((c for c in challenges if c["date"] == today), None)
```

### 6. 🔧 Ajout des dépendances complètes

Quand vous êtes prêt à implémenter les fonctionnalités complètes :

```bash
# Décommenter les dépendances dans requirements.txt
pip install pinecone-client langchain langchain-openai openai pdfplumber python-docx
```

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
- `GET /challenges/next?matiere=...` : Récupérer le challenge du moment pour une matière

## Exemple d'appel pour récupérer le challenge du moment

```http
GET /challenges/next?matiere=SYD
```

**Réponse :**
```json
{
  "success": true,
  "message": "Challenge servi",
  "data": {
    "challenge": {
      "id": 1,
      "ref": "SYD-001",
      "question": "Expliquez le modèle OSI.",
      "matiere": "SYD",
      "date": "2024-05-01"
    }
  }
}
```

---

Pour toute question sur l'usage ou l'extension de l'API, consulte la documentation technique ou contacte l'équipe projet.
