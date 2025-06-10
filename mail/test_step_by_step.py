#!/usr/bin/env python3
"""
Test étape par étape pour identifier où le système plante
"""

import logging
import requests
import time
from database_utils import get_student_by_id, get_all_students

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration de l'API
API_BASE_URL = "http://localhost:8000/api"

def test_step_1_database(user_id=8):
    """Étape 1: Test de connexion à la base de données"""
    print("\n" + "="*60)
    print("📊 ÉTAPE 1: CONNEXION BASE DE DONNÉES")
    print("="*60)
    
    try:
        # Test connexion générale
        students = get_all_students()
        print(f"✅ Connexion DB réussie - {len(students)} étudiants trouvés")
        
        # Test récupération étudiant spécifique
        student = get_student_by_id(user_id)
        if student:
            print(f"✅ Étudiant ID {user_id} trouvé:")
            print(f"   - Nom: {student['username']}")
            print(f"   - Email: {student['email']}")
            print(f"   - Abonnements: {', '.join(student['subscriptions'])}")
            return True, student
        else:
            print(f"❌ Étudiant ID {user_id} non trouvé")
            return False, None
            
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False, None

def test_step_2_api_connection():
    """Étape 2: Test de connexion à l'API"""
    print("\n" + "="*60)
    print("🌐 ÉTAPE 2: CONNEXION API")
    print("="*60)
    
    try:
        # Test de base - ping simple
        url = f"{API_BASE_URL}/challenges/health"
        print(f"🔍 Test connexion: {url}")
        
        response = requests.get(url, timeout=6)
        print(f"✅ Réponse API: Status {response.status_code}")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Erreur: API non accessible - Serveur non démarré?")
        print("💡 Solution: Démarrer l'API avec: python -m uvicorn app.main:app --reload")
        return False
    except requests.exceptions.Timeout:
        print("❌ Erreur: Timeout - API trop lente")
        return False
    except Exception as e:
        print(f"❌ Erreur API inattendue: {e}")
        return False

def test_step_3_api_challenge(user_id=8):
    """Étape 3: Test récupération challenge pour un utilisateur"""
    print("\n" + "="*60)
    print("🧠 ÉTAPE 3: RÉCUPÉRATION CHALLENGE")
    print("="*60)
    
    try:
        # Test challenge du jour pour utilisateur
        url = f"{API_BASE_URL}/challenges/today/simple"
        params = {"user_id": user_id}
        
        print(f"🔍 URL: {url}")
        print(f"🔍 Params: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Challenge récupéré avec succès:")
            print(f"   - Question: {data.get('question', 'N/A')[:100]}...")
            print(f"   - Matière: {data.get('matiere', 'N/A')}")
            print(f"   - Référence: {data.get('ref', 'N/A')}")
            return True, data
        else:
            print(f"❌ Erreur API: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Détail: {error_data}")
            except:
                print(f"   Réponse brute: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Erreur récupération challenge: {e}")
        return False, None

def test_step_4_email_config():
    """Étape 4: Test configuration email"""
    print("\n" + "="*60)
    print("📧 ÉTAPE 4: CONFIGURATION EMAIL")
    print("="*60)
    
    try:
        from config import EMAIL, PASSWORD
        
        if EMAIL and EMAIL != "lerhinoo@gmail.com":
            print(f"✅ Email configuré: {EMAIL}")
        else:
            print("⚠️ Email par défaut utilisé - Configurer .env")
            
        if PASSWORD and len(PASSWORD) > 10:
            print("✅ Mot de passe configuré")
        else:
            print("⚠️ Mot de passe par défaut - Configurer .env")
            
        # Test simple (sans vraiment envoyer)
        print("📧 Configuration email semble OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur configuration email: {e}")
        return False

def test_step_6_send_email_real(student, challenge_data):
    """Étape 6: Envoi réel de l'email"""
    print("\n" + "="*60)
    print("📤 ÉTAPE 6: ENVOI RÉEL EMAIL")
    print("="*60)
    
    try:
        if not student:
            print("❌ Pas d'étudiant fourni")
            return False
            
        if not challenge_data:
            print("❌ Pas de challenge fourni")
            return False
            
        print("📤 Envoi réel de l'email:")
        print(f"   - Destinataire: {student['email']}")
        print(f"   - Question: {challenge_data.get('question', 'N/A')[:60]}...")
        print(f"   - Matière: {challenge_data.get('matiere', 'N/A')}")
        
        # Import et envoi réel
        from send_questions import send_question_from_api
        
        print("🚀 Démarrage de l'envoi...")
        success = send_question_from_api(
            to=student['email'], 
            user_id=student['id']
        )
        
        if success:
            print("✅ Email envoyé avec succès!")
            print(f"📧 Challenge envoyé à {student['username']} ({student['email']})")
            return True
        else:
            print("❌ Échec de l'envoi de l'email")
            return False
        
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        import traceback
        print(f"   Détails: {traceback.format_exc()}")
        return False

def test_step_7_wait_for_reply(student, timeout_minutes=5):
    """Étape 7: Attendre la réponse de l'utilisateur"""
    print("\n" + "="*60)
    print("⏳ ÉTAPE 7: ATTENTE DE LA RÉPONSE")
    print("="*60)
    
    try:
        from email_reader import wait_for_reply, display_reply, save_reply_to_conversations
        
        print(f"⏰ Attente d'une réponse de {student['email']} pendant {timeout_minutes} minutes...")
        print("💡 L'utilisateur peut maintenant répondre à l'email reçu")
        print("🔄 Vérification automatique des nouveaux emails...")
        
        reply = wait_for_reply(student['email'], timeout_minutes)
        
        if reply:
            print("✅ Réponse reçue!")
            display_reply(reply)
            
            # Sauvegarder la réponse
            save_reply_to_conversations(reply)
            
            return True, reply
        else:
            print("⏰ Aucune réponse reçue dans le délai imparti")
            return False, None
            
    except Exception as e:
        print(f"❌ Erreur lors de l'attente de la réponse: {e}")
        import traceback
        print(f"   Détails: {traceback.format_exc()}")
        return False, None

def test_step_8_evaluate_response(reply, challenge_data):
    """Étape 8: Évaluer la réponse reçue"""
    print("\n" + "="*60)
    print("📊 ÉTAPE 8: ÉVALUATION DE LA RÉPONSE")
    print("="*60)
    
    try:
        from evaluator import evaluate_and_display
        from utils import load_conversations, save_conversations
        
        if not reply:
            print("❌ Aucune réponse à évaluer")
            return False, None
            
        # Extraire les données nécessaires
        question = challenge_data.get('data', {}).get('challenge', {}).get('question', 'Question non trouvée')
        matiere = challenge_data.get('data', {}).get('challenge', {}).get('matiere', 'Matière inconnue')
        response_text = reply['body']
        
        print(f"🧠 Évaluation de la réponse en {matiere}...")
        
        # Évaluer la réponse
        evaluation = evaluate_and_display(question, response_text, matiere)
        
        # Sauvegarder l'évaluation
        question_id = reply.get('question_id')
        if question_id:
            conversations = load_conversations()
            if question_id in conversations:
                conversations[question_id]['evaluation'] = evaluation
                conversations[question_id]['evaluated'] = True
                save_conversations(conversations)
                print(f"✅ Évaluation sauvegardée pour {question_id}")
        
        return True, evaluation
        
    except Exception as e:
        print(f"❌ Erreur lors de l'évaluation: {e}")
        import traceback
        print(f"   Détails: {traceback.format_exc()}")
        return False, None

def send_challenge_to_user_6():
    """Fonction spécifique pour envoyer un challenge à l'user ID 6"""
    print("\n" + "🎯" * 30)
    print("ENVOI CHALLENGE À L'USER ID 6 (MATHIS)")
    print("🎯" * 30)
    
    user_id = 8
    all_good = True
    
    # Étape 1: Base de données
    db_ok, student = test_step_1_database(user_id)
    if not db_ok:
        return False
    
    # Étape 2: API connexion
    api_ok = test_step_2_api_connection()
    if not api_ok:
        return False
    
    # Étape 3: Récupération challenge
    challenge_ok, challenge_data = test_step_3_api_challenge(user_id)
    if not challenge_ok:
        return False
    
    # Étape 4: Configuration email
    email_config_ok = test_step_4_email_config()
    
    # Étape 6: Envoi réel
    send_ok = test_step_6_send_email_real(student, challenge_data)
    
    # Nouvelles étapes: Attente et évaluation de la réponse
    reply_ok, reply = False, None
    eval_ok, evaluation = False, None
    
    if send_ok:
        # Demander à l'utilisateur s'il veut attendre une réponse
        print("\n" + "🤔" * 30)
        print("OPTION: ATTENDRE UNE RÉPONSE")
        print("🤔" * 30)
        
        user_choice = input("Voulez-vous attendre une réponse de l'étudiant? (o/n): ").lower().strip()
        
        if user_choice in ['o', 'oui', 'y', 'yes']:
            timeout_choice = input("Combien de minutes d'attente? (défaut: 5): ").strip()
            try:
                timeout_minutes = int(timeout_choice) if timeout_choice else 5
            except ValueError:
                timeout_minutes = 5
            
            # Étape 7: Attendre la réponse
            reply_ok, reply = test_step_7_wait_for_reply(student, timeout_minutes)
            
            if reply_ok and reply:
                # Étape 8: Évaluer la réponse
                eval_ok, evaluation = test_step_8_evaluate_response(reply, challenge_data)
    
    # Résumé
    print("\n" + "📋" * 30)
    print("RÉSUMÉ DU TEST")
    print("📋" * 30)
    print(f"✅ Base de données: {'OK' if db_ok else 'ÉCHEC'}")
    print(f"✅ Connexion API: {'OK' if api_ok else 'ÉCHEC'}")
    print(f"✅ Challenge API: {'OK' if challenge_ok else 'ÉCHEC'}")
    print(f"✅ Config email: {'OK' if email_config_ok else 'ÉCHEC'}")
    print(f"✅ Envoi email: {'OK' if send_ok else 'ÉCHEC'}")
    
    if reply_ok:
        print(f"✅ Réception réponse: {'OK' if reply_ok else 'ÉCHEC'}")
    if eval_ok:
        print(f"✅ Évaluation: {'OK' if eval_ok else 'ÉCHEC'}")
        if evaluation:
            print(f"📊 Score final: {evaluation['score']}/100 ({evaluation['grade']})")
    
    if db_ok and api_ok and challenge_ok and email_config_ok and send_ok:
        print("\n🎉 Toutes les étapes sont OK! Email envoyé avec succès!")
        if reply_ok and eval_ok:
            print("🌟 Bonus: Réponse reçue et évaluée!")
        return True
    else:
        print("\n❌ Certaines étapes ont échoué")
        return False

def real_send_to_user_6():
    """Envoi réel du challenge à l'user ID 6"""
    print("\n" + "🚀" * 30)
    print("ENVOI RÉEL DU CHALLENGE")
    print("🚀" * 30)
    
    try:
        from send_questions import send_question_from_api
        
        user_id = 8
        
        # Récupérer l'étudiant
        student = get_student_by_id(user_id)
        if not student:
            print(f"❌ Étudiant ID {user_id} non trouvé")
            return False
        
        print(f"📤 Envoi réel du challenge à {student['username']} ({student['email']})")
        
        # Envoi réel
        success = send_question_from_api(
            to=student['email'],
            user_id=user_id
        )
        
        if success:
            print("✅ Challenge envoyé avec succès!")
            return True
        else:
            print("❌ Échec de l'envoi")
            return False
            
    except Exception as e:
        print(f"❌ Erreur envoi réel: {e}")
        return False

def main():
    """Fonction principale"""
    import sys
    
    print("🔍 TEST ÉTAPE PAR ÉTAPE - SYSTÈME MAIL")
    print("="*60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "real":
            # Envoi réel
            real_send_to_user_6()
        elif sys.argv[1] == "test":
            # Test complet
            send_challenge_to_user_6()
        else:
            print("Usage: python test_step_by_step.py [test|real]")
    else:
        # Par défaut: test simulation
        send_challenge_to_user_6()

if __name__ == "__main__":
    main() 