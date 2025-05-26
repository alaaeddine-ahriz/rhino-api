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
- `POST /api/matieres/update` - Mettre à jour l'index (enseignant+)

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

### Tests manuels avec Swagger

1. Allez sur http://localhost:8000/api/docs
2. Authentifiez-vous avec un token
3. Testez chaque endpoint

### Tests automatisés (à implémenter)

```bash
# Installer pytest
pip install pytest pytest-asyncio httpx

# Créer des tests
mkdir tests
touch tests/test_auth.py tests/test_matieres.py

# Lancer les tests
pytest
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
