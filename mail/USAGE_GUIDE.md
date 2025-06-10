# Guide d'Utilisation Complet - Système de Mail Automatisé

## 🎯 Vue d'ensemble

Ce système permet d'automatiser complètement le workflow suivant :

1. **📤 Envoi de questions** - Récupère les challenges depuis l'API et les envoie aux étudiants
2. **📥 Réception des réponses** - Lit automatiquement les emails de réponse
3. **🤖 Évaluation automatique** - Utilise l'API d'évaluation pour noter les réponses
4. **📧 Envoi des résultats** - Renvoie les évaluations aux étudiants par email

## 🚀 Démarrage Rapide

### 1. Prérequis

```bash
# 1. Démarrer l'API
cd ..  # Retour à la racine du projet
python -m uvicorn app.main:app --reload --port 8000

# 2. Dans un autre terminal, aller dans le dossier mail
cd mail
```

### 2. Test Simple - Un Étudiant

```bash
# Envoyer une question à l'étudiant ID 2
python test_complete_workflow.py simple --user-id 2

# Ou sans attendre de réponse (mode test)
python test_complete_workflow.py simple --user-id 2 --no-wait
```

### 3. Test Batch - Plusieurs Étudiants

```bash
# Tester avec des IDs spécifiques
python test_complete_workflow.py batch --user-ids 2 5

# Tester avec tous les étudiants de la base
python test_complete_workflow.py batch --all-students
```

### 4. Mode Surveillance

```bash
# Surveiller les nouvelles réponses toutes les 60 secondes
python test_complete_workflow.py monitor --interval 60
```

## 📋 Scripts Disponibles

### 1. `demo_workflow.py` - Démonstration Interactive

```bash
# Démonstration complète automatique
python demo_workflow.py

# Mode interactif pour choisir les étapes
python demo_workflow.py --interactive
```

### 2. `test_complete_workflow.py` - Tests Avancés

```bash
# Toutes les options disponibles
python test_complete_workflow.py --help

# Test simple
python test_complete_workflow.py simple --user-id 2

# Test batch
python test_complete_workflow.py batch --all-students

# Mode surveillance
python test_complete_workflow.py monitor

# Générer un rapport
python test_complete_workflow.py report
```

### 3. Scripts Individuels pour Debug

```bash
# Tester la base de données
python database_utils.py

# Envoyer une question manuellement
python send_questions.py

# Lire les réponses
python read_replies.py

# Évaluer les réponses
python evaluate_responses.py

# Envoyer les évaluations
python send_evaluation.py
```

## 🔧 Configuration

### Variables d'Environnement (.env)

```env
EMAIL=votre_email@gmail.com
PASSWORD=votre_mot_de_passe_application
```

### Configuration Gmail

1. **Activer l'authentification à 2 facteurs** sur votre compte Gmail
2. **Générer un mot de passe d'application** :
   - Aller dans les paramètres Google
   - Sécurité → Mots de passe d'applications
   - Sélectionner "Autre" et nommer "Mail System"
   - Utiliser le mot de passe généré dans la variable `PASSWORD`

## 📊 Workflow Détaillé

### Étape 1 : Envoi de Question

```python
from mail import send_question_from_api
from database_utils import get_student_by_id

# Récupérer l'étudiant depuis la base
student = get_student_by_id(user_id=2)
print(f"Envoi à: {student['email']}")

# Envoyer la question
success = send_question_from_api(
    to=student['email'],
    user_id=2
)
```

### Étape 2 : Réception des Réponses

```python
from mail import read_replies, get_unread_count

# Vérifier les nouveaux messages
unread = get_unread_count()
print(f"Messages non lus: {unread}")

# Traiter les réponses
if unread > 0:
    read_replies()
```

### Étape 3 : Évaluation Automatique

```python
from mail import evaluate_pending_responses

# Évaluer toutes les réponses en attente
evaluated = evaluate_pending_responses()
print(f"Réponses évaluées: {evaluated}")
```

### Étape 4 : Envoi des Résultats

```python
from mail import send_evaluations_for_pending_responses

# Envoyer les évaluations aux étudiants
sent = send_evaluations_for_pending_responses()
print(f"Évaluations envoyées: {sent}")
```

## 🗃️ Base de Données

### Étudiants Disponibles

```bash
# Voir tous les étudiants
python database_utils.py
```

Exemple de sortie :
```
👥 Total utilisateurs: 5
   - student: 2
   - teacher: 1
   - admin: 2

📋 Étudiants trouvés: 2
   1. doc_student (docstudent@test.com) - ID: 2
      📚 Abonnements: SYD
   2. Mathis (Mathis.beaufour71@gmail.com) - ID: 5
      📚 Abonnements: TCP
```

### Utilisation Programmatique

```python
from database_utils import get_student_by_id, get_all_students

# Récupérer un étudiant spécifique
student = get_student_by_id(2)
print(student['email'])  # docstudent@test.com

# Récupérer tous les étudiants
students = get_all_students()
for student in students:
    print(f"{student['username']}: {student['email']}")
```

## 📈 Surveillance et Rapports

### Rapports Disponibles

```python
from mail import print_evaluation_report, print_evaluation_send_report

# Rapport d'évaluation
print_evaluation_report()

# Rapport d'envoi des évaluations
print_evaluation_send_report()
```

### Mode Surveillance Continue

```python
from test_complete_workflow import EmailWorkflowTester

tester = EmailWorkflowTester()
tester.setup_test_environment()

# Boucle de surveillance
while True:
    responses = tester.process_new_responses()
    if responses > 0:
        evaluated = tester.evaluate_all_responses()
        sent = tester.send_evaluation_results()
        print(f"Traité: {responses} réponses, {evaluated} évaluations")
    
    time.sleep(60)  # Attendre 1 minute
```

## 🔍 Débogage

### Logs Détaillés

Les logs sont configurés au niveau INFO. Pour plus de détails :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Vérification des Connexions

```python
from mail import test_api_connection
from read_replies import get_unread_count

# Tester l'API
if test_api_connection():
    print("✅ API accessible")
else:
    print("❌ API non accessible")

# Tester l'email
try:
    count = get_unread_count()
    print(f"✅ Email accessible - {count} messages non lus")
except Exception as e:
    print(f"❌ Email non accessible: {e}")
```

### Vérification de la Base de Données

```python
from database_utils import get_database_stats

stats = get_database_stats()
print(f"Utilisateurs: {stats['total_users']}")
print(f"Challenges: {stats['total_challenges']}")
```

## ⚠️ Résolution de Problèmes

### Problème : API non accessible

```bash
# S'assurer que l'API tourne
cd .. && python -m uvicorn app.main:app --reload --port 8000
```

### Problème : Erreur d'authentification email

1. Vérifier le fichier `.env`
2. Vérifier que le mot de passe d'application est correct
3. Tester avec `get_unread_count()`

### Problème : Base de données non trouvée

```python
# Vérifier le chemin dans database_utils.py
DATABASE_PATH = "../prod.db"  # Ajuster si nécessaire
```

### Problème : Aucune réponse reçue

1. Vérifier que l'email a été envoyé
2. Vérifier la boîte mail manuellement
3. Répondre à un email pour tester

## 📚 Exemples d'Usage Production

### Script de Production Quotidien

```python
#!/usr/bin/env python3
"""Script quotidien pour envoyer les challenges"""

from database_utils import get_all_students
from test_complete_workflow import EmailWorkflowTester

def daily_challenge_routine():
    tester = EmailWorkflowTester()
    
    if not tester.setup_test_environment():
        print("❌ Erreur de configuration")
        return
    
    # Récupérer tous les étudiants actifs
    students = get_all_students()
    user_ids = [s['id'] for s in students]
    
    # Envoyer les challenges
    results = tester.run_batch_workflow(user_ids)
    
    # Rapport
    successful = sum(1 for r in results if r['question_sent'])
    print(f"📊 {successful}/{len(results)} challenges envoyés")

if __name__ == "__main__":
    daily_challenge_routine()
```

### Script de Surveillance H24

```python
#!/usr/bin/env python3
"""Surveillance continue des réponses"""

import time
from test_complete_workflow import EmailWorkflowTester

def continuous_monitoring():
    tester = EmailWorkflowTester()
    tester.setup_test_environment()
    
    print("🔄 Surveillance continue démarrée...")
    
    while True:
        try:
            # Traiter les nouvelles réponses
            responses = tester.process_new_responses()
            evaluated = tester.evaluate_all_responses()
            sent = tester.send_evaluation_results()
            
            if responses > 0 or evaluated > 0 or sent > 0:
                print(f"📊 Activité: {responses} réponses, {evaluated} évaluations, {sent} envois")
            
            time.sleep(300)  # 5 minutes
            
        except KeyboardInterrupt:
            print("🛑 Surveillance arrêtée")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            time.sleep(60)  # Attendre 1 minute en cas d'erreur

if __name__ == "__main__":
    continuous_monitoring()
```

## 🎉 Conclusion

Le système est maintenant complètement opérationnel et prêt pour la production. Il peut :

- ✅ Envoyer des questions automatiquement depuis l'API
- ✅ Lire les réponses par email
- ✅ Évaluer automatiquement avec l'IA
- ✅ Renvoyer les résultats aux étudiants
- ✅ Fonctionner en mode surveillance continue
- ✅ Générer des rapports détaillés

Utilisez les scripts de test pour valider le fonctionnement avant de passer en production ! 