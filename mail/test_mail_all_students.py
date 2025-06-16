#!/usr/bin/env python3
"""
Test étape par étape pour envoyer des mails à tous les étudiants avec threading
"""

import logging
import requests
import time
from database_utils import get_all_students
import concurrent.futures
from queue import Queue
import threading

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration de l'API
API_BASE_URL = "http://localhost:8000/api"

def process_student(student, timeout_minutes=5):
    """Traite un étudiant individuel avec toutes les étapes"""
    try:
        print(f"\n{'='*60}")
        print(f"🎯 TRAITEMENT DE {student['username']} (ID: {student['id']})")
        print(f"{'='*60}")
        
        # Étape 1: Vérifier l'étudiant
        print(f"✅ Étudiant trouvé:")
        print(f"   - Nom: {student['username']}")
        print(f"   - Email: {student['email']}")
        print(f"   - Abonnements: {', '.join(student['subscriptions'])}")
        
        # Étape 2: Récupérer le challenge
        url = f"{API_BASE_URL}/challenges/today"
        params = {"user_id": student['id']}
        
        print(f"🔍 Récupération du challenge...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Erreur API: Status {response.status_code}")
            return False
            
        challenge_data = response.json()
        print("✅ Challenge récupéré:")
        print(f"   - Question: {challenge_data.get('question', 'N/A')[:100]}...")
        print(f"   - Matière: {challenge_data.get('matiere', 'N/A')}")
        
        # Étape 3: Envoyer l'email
        from send_questions import send_question_from_api
        
        print(f"📤 Envoi du challenge à {student['email']}...")
        success = send_question_from_api(
            to=student['email'],
            user_id=student['id']
        )
        
        if not success:
            print(f"❌ Échec de l'envoi pour {student['username']}")
            return False
            
        print(f"✅ Challenge envoyé à {student['username']}")
        
        # Étape 4: Attendre la réponse
        from email_reader import wait_for_reply, display_reply, save_reply_to_conversations
        
        print(f"⏳ Attente de la réponse de {student['username']}...")
        reply = wait_for_reply(student['email'], timeout_minutes)
        
        if reply:
            print(f"✅ Réponse reçue de {student['username']}")
            display_reply(reply)
            save_reply_to_conversations(reply)
            
            # Étape 5: Évaluer la réponse
            from evaluator import evaluate_and_display, send_feedback_email
            
            print(f"🧠 Évaluation de la réponse de {student['username']}...")
            evaluation = evaluate_and_display(
                challenge_data.get('question', ''),
                reply['body'],
                challenge_data.get('matiere', ''),
                user_id=student['id']
            )
            
            if evaluation:
                print(f"✅ Évaluation terminée pour {student['username']}")
                
                # Vérifier si la réponse est marquée comme "merdique"
                raw_response = evaluation.get('raw_api_response', {})
                data = raw_response.get('data', {})
                is_merdique = data.get('merdique', False)
                
                print(f"\n🔍 Vérification du statut 'merdique':")
                print(f"   - Raw API Response: {raw_response}")
                print(f"   - Data: {data}")
                print(f"   - Is merdique: {is_merdique}")
                
                if is_merdique:
                    print(f"⚠️ Réponse inappropriée détectée pour {student['username']}")
                    # Créer un message spécial pour les réponses inappropriées
                    inappropriate_response = {
                        'body': """Votre réponse ne respecte pas les règles de base de la communication académique.

⚠️ ATTENTION
• Les réponses inappropriées, hors sujet ou contenant des insultes ne seront pas tolérées
• Chaque question mérite une réponse sérieuse et réfléchie
• Le respect mutuel est essentiel dans un environnement d'apprentissage

📝 RAPPEL
• Lisez attentivement la question avant de répondre
• Utilisez les concepts du cours pour structurer votre réponse
• Prenez le temps de réfléchir et de formuler une réponse pertinente

Nous vous invitons à reformuler votre réponse de manière appropriée et constructive.

Cordialement,
Le Rhino""",
                        'from': reply['from'],
                        'question_id': reply.get('question_id')
                    }
                    
                    # Créer une évaluation spéciale pour le cas merdique
                    merdique_evaluation = {
                        'raw_api_response': {
                            'success': True,
                            'message': 'Réponse inappropriée détectée',
                            'data': {
                                'score': 0,
                                'note': 0,
                                'feedback': inappropriate_response['body'],
                                'points_forts': [],
                                'points_ameliorer': [],
                                'suggestions': [],
                                'merdique': True
                            }
                        },
                        'api_status': 'success',
                        'status_code': 200
                    }
                    
                    # Envoyer le feedback spécial avec l'évaluation merdique
                    feedback_sent = send_feedback_email(
                        to_email=student['email'],
                        evaluation=merdique_evaluation,
                        question=challenge_data.get('question', ''),
                        response=inappropriate_response['body'],
                        student_name=student['username'],
                        original_email=reply  # Important pour le threading
                    )
                else:
                    # Envoyer le feedback normal
                    feedback_sent = send_feedback_email(
                        to_email=student['email'],
                        evaluation=evaluation,
                        question=challenge_data.get('question', ''),
                        response=reply['body'],
                        student_name=student['username'],
                        original_email=reply  # Important pour le threading
                    )
                
                if feedback_sent:
                    print(f"✅ Feedback envoyé avec succès à {student['username']}")
                else:
                    print(f"❌ Échec de l'envoi du feedback à {student['username']}")
            else:
                print(f"❌ Échec de l'évaluation pour {student['username']}")
        else:
            print(f"⏰ Pas de réponse de {student['username']} dans le délai imparti")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement de {student['username']}: {e}")
        import traceback
        print(f"   Détails: {traceback.format_exc()}")
        return False

def send_to_all_students(timeout_minutes=5):
    """Envoie les challenges à tous les étudiants avec threading"""
    print("\n" + "🚀" * 30)
    print("ENVOI DES CHALLENGES À TOUS LES ÉTUDIANTS")
    print("🚀" * 30)
    
    try:
        # Récupérer tous les étudiants
        students = get_all_students()
        print(f"👥 {len(students)} étudiants trouvés")
        
        # Créer un thread pour chaque étudiant
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(students)) as executor:
            # Lancer le traitement de chaque étudiant dans un thread séparé
            futures = {
                executor.submit(process_student, student, timeout_minutes): student
                for student in students
            }
            
            # Suivre les résultats
            success_count = 0
            for future in concurrent.futures.as_completed(futures):
                student = futures[future]
                try:
                    if future.result():
                        success_count += 1
                except Exception as e:
                    print(f"❌ Erreur dans le thread de {student['username']}: {e}")
        
        # Résumé
        print("\n" + "📋" * 30)
        print("RÉSUMÉ FINAL")
        print("📋" * 30)
        print(f"✅ Étudiants traités avec succès: {success_count}/{len(students)}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        print(f"   Détails: {traceback.format_exc()}")
        return False

def main():
    """Fonction principale"""
    print("🔍 TEST ENVOI À TOUS LES ÉTUDIANTS - SYSTÈME MAIL")
    print("="*60)
    
    # Demander le timeout
    try:
        timeout_input = input("⏱️  Délai d'attente en minutes (défaut: 5): ").strip()
        timeout_minutes = int(timeout_input) if timeout_input else 5
    except ValueError:
        print("⚠️ Valeur invalide, utilisation du délai par défaut (5 minutes)")
        timeout_minutes = 5
    
    # Lancer l'envoi à tous les étudiants
    send_to_all_students(timeout_minutes)

if __name__ == "__main__":
    main() 