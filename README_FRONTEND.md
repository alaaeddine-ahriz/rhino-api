# 🦏 Le Rhino API - Guide Frontend

**API FastAPI pour la gestion de cours et génération de questions via RAG (Retrieval-Augmented Generation)**

Ce guide est destiné à l'équipe **front-end** pour comprendre et intégrer l'API Rhino dans leurs applications.

## 📋 Table des matières

- [🚀 Démarrage rapide](#-démarrage-rapide)
- [🔐 Système d'authentification](#-système-dauthentification)
- [👥 Rôles utilisateur et permissions](#-rôles-utilisateur-et-permissions)
- [📚 Routes et endpoints disponibles](#-routes-et-endpoints-disponibles)
- [💾 Modèles de données](#-modèles-de-données)
- [🔄 Flux d'utilisation typiques](#-flux-dutilisation-typiques)
- [📝 Exemples d'intégration](#-exemples-dintégration)
- [⚠️ Gestion d'erreurs](#️-gestion-derreurs)

## 🚀 Démarrage rapide

### URL de base de l'API
```
http://localhost:8000
```

### Documentation interactive
- **Swagger UI** : http://localhost:8000/api/docs
- **ReDoc** : http://localhost:8000/api/redoc

### Format de réponse standard
Toutes les réponses de l'API suivent ce format :
```json
{
  "success": boolean,
  "message": string,
  "data": object | array | null
}
```

## 🔐 Système d'authentification

L'API utilise un système d'authentification simple basé sur l'ID utilisateur pour l'instant (développement).

### Comment s'authentifier

1. **Obtenir l'ID utilisateur** : Chaque utilisateur a un ID unique en base de données
2. **Inclure l'ID dans les requêtes** : Ajouter `user_id` comme paramètre de requête

```javascript
// Exemple avec fetch
const response = await fetch('/api/matieres?user_id=1', {
  headers: {
    'Content-Type': 'application/json'
  }
});
```

### Utilisateurs de test disponibles

| ID | Username | Email | Rôle |
|-----|----------|-------|------|
| 1 | student1 | student1@example.com | student |
| 2 | student2 | student2@example.com | student |
| 3 | teacher1 | teacher1@example.com | teacher |
| 4 | teacher2 | teacher2@example.com | teacher |
| 5 | admin1 | admin1@example.com | admin |

## 👥 Rôles utilisateur et permissions

### 🎓 Étudiant (`student`)
**Permissions :**
- ✅ Consulter les matières
- ✅ Consulter les documents
- ✅ Poser des questions au système RAG
- ✅ Voir les challenges du jour
- ✅ Soumettre des réponses aux challenges
- ✅ Consulter les classements
- ❌ Gérer les matières et documents
- ❌ Créer des challenges

**Ce qu'un étudiant peut faire :**
- Naviguer dans les cours disponibles
- Poser des questions sur le contenu des cours
- Participer aux challenges quotidiens
- Voir sa progression et son classement

### 👨‍🏫 Enseignant (`teacher`)
**Permissions :**
- ✅ Toutes les permissions des étudiants
- ✅ Créer, modifier, supprimer des matières
- ✅ Uploader et gérer des documents
- ✅ Créer des challenges
- ✅ Générer des questions de réflexion
- ✅ Calculer les classements
- ❌ Gérer les utilisateurs et tokens

**Ce qu'un enseignant peut faire :**
- Gérer le contenu pédagogique (matières, documents)
- Créer des challenges pour les étudiants
- Monitorer la progression des étudiants
- Générer du contenu pédagogique automatiquement

### 👨‍💼 Administrateur (`admin`)
**Permissions :**
- ✅ Toutes les permissions des enseignants
- ✅ Gérer les utilisateurs
- ✅ Accès complet à tous les endpoints

**Ce qu'un admin peut faire :**
- Administration complète du système
- Gestion des utilisateurs
- Configuration avancée

## 📚 Routes et endpoints disponibles

### 🔐 Gestion des utilisateurs
| Méthode | Endpoint | Permissions | Description |
|---------|----------|-------------|-------------|
| `POST` | `/api/users/register` | Tous | Inscription d'un nouvel utilisateur |
| `PUT` | `/api/users/subscriptions` | Tous | Mise à jour des abonnements aux matières |
| `PUT` | `/api/users/{user_id}` | Tous | Mise à jour des informations utilisateur |

### 📚 Gestion des matières
| Méthode | Endpoint | Permissions | Description |
|---------|----------|-------------|-------------|
| `GET` | `/api/matieres?user_id={id}` | Tous | Liste toutes les matières disponibles |
| `POST` | `/api/matieres?user_id={id}` | Enseignant+ | Créer une nouvelle matière |
| `GET` | `/api/matieres/{matiere_name}?user_id={id}` | Tous | Informations détaillées d'une matière |
| `DELETE` | `/api/matieres/{matiere_name}?user_id={id}` | Enseignant+ | Supprimer une matière |
| `POST` | `/api/matieres/{matiere_name}/update?user_id={id}` | Enseignant+ | Réindexer les documents d'une matière |

### 📄 Gestion des documents
| Méthode | Endpoint | Permissions | Description |
|---------|----------|-------------|-------------|
| `GET` | `/api/matieres/{matiere}/documents?user_id={id}` | Tous | Liste les documents d'une matière |
| `POST` | `/api/matieres/{matiere}/documents?user_id={id}` | Enseignant+ | Uploader un nouveau document |
| `DELETE` | `/api/matieres/{matiere}/documents/{doc_id}?user_id={id}` | Enseignant+ | Supprimer un document |
| `GET` | `/api/matieres/{matiere}/documents/{doc_id}/content?user_id={id}` | Tous | Obtenir le contenu d'un document |

### ❓ Questions et RAG
| Méthode | Endpoint | Permissions | Description |
|---------|----------|-------------|-------------|
| `POST` | `/api/question?user_id={id}` | Tous | Poser une question au système RAG |
| `POST` | `/api/question/reflection?user_id={id}` | Tous | Générer une question de réflexion |

### 📝 Évaluations
| Méthode | Endpoint | Permissions | Description |
|---------|----------|-------------|-------------|
| `POST` | `/api/evaluation/response?user_id={id}` | Tous | Évaluer une réponse d'étudiant |

### 🏆 Challenges
| Méthode | Endpoint | Permissions | Description |
|---------|----------|-------------|-------------|
| `GET` | `/api/challenges/today?user_id={id}` | Tous | Challenge du jour pour l'utilisateur |
| `GET` | `/api/challenges/today?user_id={id}` | Tous | Version simplifiée du challenge du jour |
| `GET` | `/api/challenges?user_id={id}&matiere={opt}` | Tous | Liste tous les challenges (filtrable) |
| `POST` | `/api/challenges?user_id={id}` | Enseignant+ | Créer un nouveau challenge |
| `POST` | `/api/challenges/{id}/response?user_id={id}` | Tous | Soumettre une réponse à un challenge |
| `GET` | `/api/challenges/{id}/leaderboard?user_id={id}` | Tous | Classement d'un challenge |
| `GET` | `/api/challenges/next?user_id={id}&matiere={name}` | Tous | Prochain challenge pour une matière |

### 🏅 Classements
| Méthode | Endpoint | Permissions | Description |
|---------|----------|-------------|-------------|
| `POST` | `/api/leaderboard/calcule?user_id={id}` | Enseignant+ | Calculer le classement d'un challenge |

## 💾 Modèles de données

### Utilisateur
```typescript
interface User {
  id: string;
  username: string;
  email?: string;
  full_name?: string;
  role: 'student' | 'teacher' | 'admin';
  subscriptions: string; // Liste séparée par des virgules
}
```

### Matière
```typescript
interface Matiere {
  name: string;
  description?: string;
  document_count: number;
  last_update?: string;
  path?: string;
}
```

### Document
```typescript
interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_path: string;
  upload_date: string;
  file_size: number;
  matiere: string;
  indexed: boolean;
}
```

### Challenge
```typescript
interface Challenge {
  challenge_id: string;
  ref: string;
  date: string; // Automatically set to creation date
  question: string;
  matiere: string;
  matieres: string[];
}

interface ChallengeCreate {
  question: string;
  matiere: string;
  // Note: date is automatically set to current date, no need to provide it
}
```

### Question Request
```typescript
interface QuestionRequest {
  query: string;
  matiere: string;
  max_tokens?: number;
}
```

### Evaluation Request
```typescript
interface EvaluationRequest {
  question: string;
  reponse_etudiant: string;
  matiere: string;
  criteres_evaluation?: string[];
}
```

## 🔄 Flux d'utilisation typiques

### 🎓 Parcours Étudiant

1. **Connexion et récupération des matières**
```javascript
// Récupérer les matières disponibles
const matieresResponse = await fetch('/api/matieres?user_id=1');
const matieres = await matieresResponse.json();
```

2. **Challenge du jour**
```javascript
// Récupérer le challenge du jour
const challengeResponse = await fetch('/api/challenges/today?user_id=1');
const challenge = await challengeResponse.json();
```

3. **Soumission de réponse**
```javascript
// Soumettre une réponse au challenge
const responseSubmit = await fetch(`/api/challenges/${challengeId}/response?user_id=1`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    response: "Ma réponse au challenge..."
  })
});
```

4. **Consultation du classement**
```javascript
// Voir le classement
const leaderboard = await fetch(`/api/challenges/${challengeId}/leaderboard?user_id=1`);
```

### 👨‍🏫 Parcours Enseignant

1. **Créer une nouvelle matière**
```javascript
const newMatiere = await fetch('/api/matieres?user_id=3', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: "JAVASCRIPT",
    description: "Cours de JavaScript"
  })
});
```

2. **Uploader des documents**
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('description', 'Document de cours');

const upload = await fetch('/api/matieres/JAVASCRIPT/documents?user_id=3', {
  method: 'POST',
  body: formData
});
```

3. **Créer un challenge**
```javascript
const newChallenge = await fetch('/api/challenges?user_id=3', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: "Expliquez le concept de closure en JavaScript",
    matieres: ["JAVASCRIPT"],
    date: "2024-01-15"
  })
});
```

## 📝 Exemples d'intégration

### React Hook personnalisé pour l'API

```typescript
import { useState, useEffect } from 'react';

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export function useRhinoAPI<T>(endpoint: string, userId: number) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api${endpoint}?user_id=${userId}`);
        const result: ApiResponse<T> = await response.json();
        
        if (result.success) {
          setData(result.data);
          setError(null);
        } else {
          setError(result.message);
        }
      } catch (err) {
        setError('Erreur de connexion à l\'API');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint, userId]);

  return { data, loading, error };
}

// Utilisation
function MatieresComponent({ userId }: { userId: number }) {
  const { data: matieres, loading, error } = useRhinoAPI<{ matieres: Matiere[] }>('/matieres', userId);

  if (loading) return <div>Chargement...</div>;
  if (error) return <div>Erreur: {error}</div>;

  return (
    <ul>
      {matieres?.matieres.map(matiere => (
        <li key={matiere.name}>{matiere.name} ({matiere.document_count} documents)</li>
      ))}
    </ul>
  );
}
```

### Service API complet

```typescript
class RhinoAPIService {
  private baseURL = '/api';
  
  constructor(private userId: number) {}

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = new URL(endpoint, this.baseURL);
    url.searchParams.set('user_id', this.userId.toString());
    
    const response = await fetch(url.toString(), {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.message);
    }
    
    return result.data;
  }

  // Matières
  async getMatieres() {
    return this.request<{ matieres: Matiere[] }>('/matieres');
  }

  async createMatiere(matiere: { name: string; description?: string }) {
    return this.request('/matieres', {
      method: 'POST',
      body: JSON.stringify(matiere),
    });
  }

  // Documents
  async getDocuments(matiere: string) {
    return this.request<{ documents: Document[]; count: number }>(`/matieres/${matiere}/documents`);
  }

  async uploadDocument(matiere: string, file: File, description?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (description) formData.append('description', description);

    return this.request(`/matieres/${matiere}/documents`, {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  // Questions
  async askQuestion(query: string, matiere: string) {
    return this.request('/question', {
      method: 'POST',
      body: JSON.stringify({ query, matiere }),
    });
  }

  // Challenges
  async getTodayChallenge() {
    return this.request<{ challenge: Challenge; user_info: any }>('/challenges/today');
  }

  async submitChallengeResponse(challengeId: string, response: string) {
    return this.request(`/challenges/${challengeId}/response`, {
      method: 'POST',
      body: JSON.stringify({ response }),
    });
  }

  async getChallengeLeaderboard(challengeId: string) {
    return this.request(`/challenges/${challengeId}/leaderboard`);
  }
}

// Utilisation
const apiService = new RhinoAPIService(1); // userId = 1

// Récupérer les matières
const matieres = await apiService.getMatieres();

// Poser une question
const response = await apiService.askQuestion("Qu'est-ce qu'une fonction?", "JAVASCRIPT");
```

## ⚠️ Gestion d'erreurs

### Codes d'erreur HTTP communs

| Code | Description | Action recommandée |
|------|-------------|-------------------|
| `400` | Requête malformée | Vérifier les paramètres envoyés |
| `403` | Permissions insuffisantes | Vérifier le rôle de l'utilisateur |
| `404` | Ressource non trouvée | Vérifier que la ressource existe |
| `409` | Conflit (ex: matière existe déjà) | Informer l'utilisateur du conflit |
| `500` | Erreur serveur | Réessayer plus tard ou contacter l'admin |

### Exemple de gestion d'erreurs

```typescript
async function handleAPICall<T>(apiCall: () => Promise<T>): Promise<T | null> {
  try {
    return await apiCall();
  } catch (error) {
    if (error instanceof Error) {
      switch (error.message) {
        case 'You don\'t have permission to access this resource':
          alert('Vous n\'avez pas les permissions nécessaires');
          break;
        case 'Email déjà utilisé':
          alert('Cet email est déjà utilisé');
          break;
        default:
          console.error('Erreur API:', error.message);
          alert('Une erreur s\'est produite. Veuillez réessayer.');
      }
    }
    return null;
  }
}

// Utilisation
const result = await handleAPICall(() => apiService.createMatiere({
  name: "PYTHON",
  description: "Cours de Python"
}));
```

### Format de réponse d'erreur

```json
{
  "success": false,
  "message": "Description de l'erreur en français",
  "data": null
}
```

## 🔄 Technologies utilisées

### Backend
- **FastAPI** : Framework web moderne pour Python
- **SQLModel** : ORM basé sur SQLAlchemy et Pydantic
- **Pinecone** : Base de données vectorielle pour le RAG
- **OpenAI** : API pour les embeddings et génération de texte
- **LangChain** : Framework pour les applications LLM

### Types de fichiers supportés
- **PDF** : Documents PDF
- **DOCX** : Documents Word
- **PPTX** : Présentations PowerPoint
- **ODT** : Documents OpenDocument

### Fonctionnalités clés
- **RAG** : Recherche augmentée par génération pour répondre aux questions
- **Système de challenges** : Défis quotidiens pour les étudiants
- **Indexation vectorielle** : Recherche sémantique dans les documents
- **Évaluation automatique** : Feedback intelligent sur les réponses

---

## 📞 Support

Pour toute question technique ou problème d'intégration, contactez l'équipe backend ou consultez la documentation Swagger à l'adresse : http://localhost:8000/api/docs