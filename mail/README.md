# Système de Gestion des Emails Automatisé

Ce système permet d'envoyer automatiquement des questions aux étudiants via email, de récupérer leurs réponses et de les évaluer automatiquement.

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Configurer les variables d'environnement :
   - Créer un fichier `.env` dans le dossier `mail/`
   - Ajouter vos identifiants email :
```
EMAIL=votre_email@gmail.com
PASSWORD=votre_mot_de_passe_app
```

## Utilisation

### Commandes principales

1. **Envoyer une question à un étudiant :**
```bash
python mail_system.py send --email student@example.com --user-id 1
```

2. **Lire les nouvelles réponses :**
```bash
python mail_system.py read
```

3. **Évaluer les réponses en attente :**
```bash
python mail_system.py evaluate
```

4. **Afficher le rapport d'évaluation :**
```bash
python mail_system.py report
```

5. **Exécuter le workflow complet :**
```bash
python mail_system.py workflow
```

6. **Mode surveillance (vérification automatique) :**
```bash
python mail_system.py monitor --interval 300
```

### Utilisation programmatique

```python
from mail import send_daily_challenge_to_user, read_replies, evaluate_pending_responses

# Envoyer une question
success = send_daily_challenge_to_user("student@example.com", user_id=1)

# Lire les réponses
read_replies()

# Évaluer les réponses
count = evaluate_pending_responses()
```

## Fonctionnalités

- ✅ Envoi automatique de questions via l'API
- ✅ Réception et parsing des réponses par email
- ✅ Évaluation automatique avec IA
- ✅ Suivi des conversations
- ✅ Rapports statistiques
- ✅ Mode surveillance en temps réel

## Configuration Gmail

Pour utiliser Gmail, vous devez :
1. Activer l'authentification à 2 facteurs
2. Générer un mot de passe d'application
3. Utiliser ce mot de passe dans la variable `PASSWORD`

## Structure des fichiers

- `config.py` : Configuration des emails et API
- `send_questions.py` : Envoi des questions
- `read_replies.py` : Lecture des réponses
- `evaluate_responses.py` : Évaluation des réponses
- `mail_system.py` : Orchestrateur principal
- `utils.py` : Fonctions utilitaires
- `conversations.json` : Stockage des conversations 