#!/usr/bin/env python3
"""
Script pour envoyer les challenges à tous les étudiants et gérer leurs réponses
"""

import logging
import requests
import time
import os
# from database_utils import get_all_students
from send_questions import send_question_from_api
from email_reader import wait_for_reply, display_reply, save_reply_to_conversations
from evaluator import evaluate_and_display, send_feedback_email
from utils import load_conversations, save_conversations
from config import EMAIL, PASSWORD
import threading
from queue import Queue
import concurrent.futures

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration de l'API
API_PORT = os.getenv('PORT', '8000')
API_BASE_URL = f"http://localhost:{API_PORT}/api"

# File d'attente pour les feedbacks à envoyer
feedback_queue = Queue()

def send_challenge_to_all_students():
    """Envoie le challenge à tous les étudiants"""
    print("\n" + "="*60)
    print("📧 ENVOI DES CHALLENGES À TOUS LES ÉTUDIANTS")
    print("="*60)
    
    try:
        # Récupérer tous les étudiants (désactivé - utilisation de l'API uniquement)
        # students = get_all_students()
        # print(f"👥 {len(students)} étudiants trouvés")
        print("⚠️ Récupération des étudiants désactivée - utilisation de l'API uniquement")
        print("👥 Cette fonction nécessite une liste d'étudiants fournie en paramètre")
        return False
        
        # Envoyer le challenge à chaque étudiant
        # for student in students:
        #     print(f"\n📤 Envoi du challenge à {student['username']} ({student['email']})...")
        #     
        #     success = send_question_from_api(
        #         to=student['email'],
        #         user_id=student['id']
        #     )
        #     
        #     if success:
        #         print(f"✅ Challenge envoyé avec succès à {student['username']}")
        #     else:
        #         print(f"❌ Échec de l'envoi du challenge à {student['username']}")
        #     
        #     # Petit délai entre chaque envoi pour éviter de surcharger le serveur mail
        #     time.sleep(2)
        
        # return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi des challenges: {e}")
        return False

def send_feedback_to_student(reply, evaluation, student):
    """Envoie le feedback à l'étudiant"""
    try:
        if not reply or not evaluation:
            print("❌ Réponse ou évaluation manquante")
            return False
            
        # Extraire les données nécessaires
        question_id = reply.get('question_id')
        if not question_id:
            print("❌ Question ID non trouvé")
            return False
            
        conversations = load_conversations()
        if question_id not in conversations:
            print(f"❌ Conversation non trouvée pour la question {question_id}")
            return False
            
        challenge_data = conversations[question_id]
        question = challenge_data.get('question', 'Question non trouvée')
        student_email = reply['from']
        student_name = student.get('username', 'Étudiant')
        response_text = reply['body']
        
        print(f"📧 Envoi du feedback en réponse à {student_email}")
        print(f"👤 Étudiant: {student_name}")
        print(f"📊 Note obtenue: {evaluation['raw_api_response']['data']['note']}")
        print(f"📊 Score final: {evaluation['raw_api_response']['data']['score']}")
        
        # Envoyer le feedback en réponse à l'email original
        feedback_sent = send_feedback_email(
            to_email=student_email,
            evaluation=evaluation,
            question=question,
            response=response_text,
            student_name=student_name,
            original_email=reply
        )
        
        if feedback_sent:
            print("✅ Feedback envoyé avec succès!")
            print(f"📬 L'étudiant {student_name} va recevoir son évaluation détaillée")
            
            # Sauvegarder l'envoi du feedback
            conversations[question_id]['feedback_sent'] = True
            conversations[question_id]['feedback_sent_to'] = student_email
            save_conversations(conversations)
            print(f"✅ Envoi du feedback enregistré pour {question_id}")
            
            return True
        else:
            print("❌ Échec de l'envoi du feedback")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du feedback: {e}")
        return False

def evaluate_reply(reply, student):
    """Évalue une réponse individuelle et met en file d'attente le feedback"""
    try:
        # Récupérer les données du challenge
        question_id = reply.get('question_id')
        if not question_id:
            print(f"❌ Question ID non trouvé pour l'étudiant {student['id']}")
            return None
            
        conversations = load_conversations()
        if question_id not in conversations:
            print(f"❌ Conversation non trouvée pour la question {question_id}")
            return None
            
        challenge_data = conversations[question_id]
        question = challenge_data.get('question', 'Question non trouvée')
        matiere = challenge_data.get('matiere', 'Matière inconnue')
        response_text = reply['body']
        
        # Évaluer la réponse
        evaluation = evaluate_and_display(question, response_text, matiere, user_id=student['id'])
        
        if evaluation:
            # Sauvegarder l'évaluation
            conversations[question_id]['evaluation'] = evaluation
            save_conversations(conversations)
            
            # Vérifier si la réponse est marquée comme "merdique"
            raw_response = evaluation.get('raw_api_response', {})
            data = raw_response.get('data', {})
            is_merdique = data.get('merdique', False)
            
            print(f"\n🔍 Vérification du statut 'merdique':")
            print(f"   - Raw API Response: {raw_response}")
            print(f"   - Data: {data}")
            print(f"   - Is merdique: {is_merdique}")
            print(f"   - Merdique value type: {type(data.get('merdique'))}")
            
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
                    'question_id': question_id
                }
                # Envoyer immédiatement le feedback spécial
                send_feedback_to_student(inappropriate_response, evaluation, student)
            else:
                # Envoyer immédiatement le feedback normal
                send_feedback_to_student(reply, evaluation, student)
        
        return evaluation
        
    except Exception as e:
        print(f"❌ Erreur lors de l'évaluation de la réponse: {e}")
        return None

def process_student_response(student, timeout_minutes):
    """Traite la réponse d'un étudiant de manière complètement indépendante"""
    try:
        print(f"\n⏳ Attente de la réponse de {student['username']}...")
        
        # Attendre la réponse avec un timeout individuel
        reply = wait_for_reply(student['email'], timeout_minutes)
        if reply:
            print(f"✅ Réponse reçue de {student['username']}")
            display_reply(reply)
            save_reply_to_conversations(reply)
            
            # Évaluer immédiatement la réponse
            print(f"🧠 Évaluation immédiate de la réponse de {student['username']}...")
            evaluation = evaluate_reply(reply, student)
            if evaluation:
                print(f"✅ Évaluation terminée pour {student['username']}")
                # Le feedback est déjà envoyé dans evaluate_reply
            else:
                print(f"❌ Échec de l'évaluation pour {student['username']}")
        else:
            print(f"⏰ Pas de réponse de {student['username']} dans le délai imparti")
            
    except Exception as e:
        print(f"❌ Erreur lors du traitement de la réponse de {student['username']}: {e}")

def wait_and_process_replies(timeout_minutes=30):
    """Attend et traite les réponses des étudiants de manière asynchrone et indépendante"""
    print("\n" + "="*60)
    print("⏳ ATTENTE ET TRAITEMENT DES RÉPONSES")
    print("="*60)
    
    try:
        # students = get_all_students()
        # print(f"👥 Attente des réponses de {len(students)} étudiants...")
        print("⚠️ Fonction désactivée - nécessite une liste d'étudiants")
        return False
        
        # Créer un thread pour chaque étudiant avec son propre timeout
        # with concurrent.futures.ThreadPoolExecutor(max_workers=len(students)) as executor:
        #     # Lancer le traitement de chaque étudiant dans un thread séparé
        #     futures = {
        #         executor.submit(process_student_response, student, timeout_minutes): student
        #         for student in students
        #     }
        #     
        #     # Ne pas attendre que tous les threads soient terminés
        #     # Chaque étudiant sera traité indépendamment
        #     for future in concurrent.futures.as_completed(futures):
        #         student = futures[future]
        #         try:
        #             future.result()
        #         except Exception as e:
        #             print(f"❌ Erreur dans le thread de {student['username']}: {e}")
        #             continue  # Continuer avec les autres étudiants même en cas d'erreur
        
        # print("\n✅ Tous les étudiants ont été traités")
        # return True
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement des réponses: {e}")
        return False

def main():
    """Fonction principale"""
    print("\n🚀 DÉMARRAGE DU PROCESSUS D'ENVOI ET D'ÉVALUATION")
    
    # Étape 1: Envoyer les challenges
    if not send_challenge_to_all_students():
        print("❌ Arrêt du processus: échec de l'envoi des challenges")
        return
    
    # Étape 2: Attendre et traiter les réponses de manière asynchrone
    if not wait_and_process_replies():
        print("❌ Arrêt du processus: échec du traitement des réponses")
        return
    
    print("\n✨ PROCESSUS TERMINÉ")
    print(f"📊 Résumé:")
    # print(f"   - Challenges envoyés: {len(get_all_students())}")
    # print(f"   - Réponses évaluées et feedbacks envoyés: {len(get_all_students())}")
    print("   - Statistiques désactivées (base de données temporairement indisponible)")

if __name__ == "__main__":
    main() 