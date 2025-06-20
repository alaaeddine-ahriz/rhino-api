#!/usr/bin/env python3
"""
Test étape par étape pour envoyer des mails à tous les étudiants avec threading
"""

import logging
import requests
import time
import concurrent.futures
from queue import Queue
import threading
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

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

# Queue partagée pour les réponses email
email_queue = Queue()
# Dictionnaire pour suivre les réponses par étudiant
student_replies = {}
# Lock pour synchroniser l'accès au dictionnaire
replies_lock = threading.Lock()

def get_all_matieres():
    """Récupère toutes les matières disponibles via l'API"""
    try:
        # Utiliser un admin pour pouvoir récupérer les matières (user_id=5 d'après README)
        response = requests.get(f"{API_BASE_URL}/matieres?user_id=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                matieres = data.get('data', {}).get('matieres', [])
                logger.info(f"✅ {len(matieres)} matières disponibles: {matieres}")
                return matieres
            else:
                logger.error(f"❌ Erreur API: {data.get('message', 'Unknown error')}")
                return []
        else:
            logger.error(f"❌ Erreur HTTP: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des matières: {e}")
        return []

def create_user():
    """Crée un nouvel utilisateur étudiant via l'API"""
    print("\n" + "👤" * 30)
    print("CRÉATION D'UN NOUVEL UTILISATEUR")
    print("👤" * 30)
    
    try:
        # Demander le username (prénom)
        while True:
            username = input("📝 Entrez le prénom/username de l'étudiant: ").strip()
            if username:
                break
            print("⚠️ Le nom d'utilisateur ne peut pas être vide!")
        
        # Demander l'adresse email
        while True:
            email = input("📧 Entrez l'adresse email de l'étudiant: ").strip()
            if email and "@" in email:
                break
            print("⚠️ Veuillez entrer une adresse email valide!")
        
        # Récupérer les matières disponibles
        print("\n📚 Récupération des matières disponibles...")
        matieres = get_all_matieres()
        
        subscriptions = []
        if matieres:
            print(f"\n📋 Matières disponibles: {', '.join(matieres)}")
            
            # Demander s'il veut abonner l'utilisateur à des matières
            while True:
                subscribe = input("\n🔔 Voulez-vous abonner cet étudiant à une ou plusieurs matières? (o/n): ").strip().lower()
                if subscribe in ['o', 'oui', 'y', 'yes']:
                    print("\n📝 Sélectionnez les matières (séparez par des virgules, ou tapez 'all' pour toutes):")
                    selection = input(f"Matières ({', '.join(matieres)}): ").strip()
                    
                    if selection.lower() == 'all':
                        subscriptions = matieres
                        print(f"✅ Étudiant abonné à toutes les matières: {', '.join(subscriptions)}")
                    else:
                        # Traiter la sélection
                        selected = [m.strip().upper() for m in selection.split(',')]
                        subscriptions = [m for m in selected if m in matieres]
                        
                        if subscriptions:
                            print(f"✅ Étudiant abonné aux matières: {', '.join(subscriptions)}")
                        else:
                            print("⚠️ Aucune matière valide sélectionnée, utilisateur créé sans abonnement")
                    break
                elif subscribe in ['n', 'non', 'no']:
                    print("📝 Utilisateur créé sans abonnement aux matières")
                    break
                else:
                    print("⚠️ Répondez par 'o' (oui) ou 'n' (non)")
        else:
            print("⚠️ Aucune matière disponible, utilisateur créé sans abonnement")
        
        # Créer l'utilisateur via l'API
        user_data = {
            "username": username,
            "email": email,
            "role": "student",
            "subscriptions": subscriptions
        }
        
        print(f"\n🚀 Création de l'utilisateur...")
        response = requests.post(f"{API_BASE_URL}/users/register", json=user_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                user_id = data.get('data', {}).get('user_id')
                print(f"✅ Utilisateur créé avec succès!")
                print(f"   - ID: {user_id}")
                print(f"   - Username: {username}")
                print(f"   - Email: {email}")
                print(f"   - Rôle: student")
                print(f"   - Abonnements: {', '.join(subscriptions) if subscriptions else 'Aucun'}")
                return True
            else:
                print(f"❌ Erreur lors de la création: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'utilisateur: {e}")
        return False

def get_all_students():
    """Récupère tous les étudiants via l'API"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                # Filter only students
                users = data.get('data', {}).get('users', [])
                students = [user for user in users if user.get('role') == 'student']
                logger.info(f"✅ {len(students)} étudiants récupérés via l'API")
                return students
            else:
                logger.error(f"❌ Erreur API: {data.get('message', 'Unknown error')}")
                return []
        else:
            logger.error(f"❌ Erreur HTTP: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des étudiants: {e}")
        return []

def read_emails_without_marking():
    """Lit les emails sans les marquer comme lus - version modifiée de read_new_replies"""
    import imaplib
    import email
    from config import EMAIL, PASSWORD, IMAP_HOST
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')
        
        # Chercher les emails non lus SANS les marquer comme lus
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            logger.error("Erreur lors de la recherche d'emails")
            return []
        
        new_replies = []
        email_ids = messages[0].split()
        
        logger.info(f"🔍 {len(email_ids)} emails non lus trouvés")
        
        for email_id in email_ids:
            try:
                # Récupérer l'email SANS le marquer comme lu
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    continue
                
                # Parser l'email
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Extraire les informations
                from_email = email.utils.parseaddr(msg['From'])[1]
                subject = msg['Subject'] or ""
                date = msg['Date']
                message_id = msg['Message-ID'] or ""
                
                # Extraire les headers de threading pour les réponses
                in_reply_to = msg.get('In-Reply-To', '')
                references = msg.get('References', '')
                
                # Extraire le contenu
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                # Vérifier si c'est une réponse à une question
                question_id = extract_question_id(subject, body)
                
                reply_data = {
                    'from': from_email,
                    'subject': subject,
                    'body': body.strip(),
                    'date': date,
                    'message_id': message_id,
                    'in_reply_to': in_reply_to,
                    'references': references,
                    'question_id': question_id,
                    'email_id': email_id.decode()
                }
                
                new_replies.append(reply_data)
                logger.info(f"📧 Réponse trouvée de {from_email}")
                
            except Exception as e:
                logger.error(f"Erreur traitement email {email_id}: {e}")
                continue
        
        mail.close()
        mail.logout()
        return new_replies
        
    except Exception as e:
        logger.error(f"Erreur lecture emails: {e}")
        return []

def extract_question_id(subject: str, body: str):
    """Extrait l'ID de la question depuis le sujet ou le corps de l'email"""
    import re
    
    # Chercher dans le sujet
    subject_match = re.search(r'IDQ-\d{14}-[a-f0-9]{6}', subject)
    if subject_match:
        return subject_match.group()
    
    # Chercher dans le corps
    body_match = re.search(r'IDQ-\d{14}-[a-f0-9]{6}', body)
    if body_match:
        return body_match.group()
    
    return None

def mark_email_as_read(email_id):
    """Marque un email spécifique comme lu"""
    import imaplib
    from config import EMAIL, PASSWORD, IMAP_HOST
    
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')
        
        # Marquer l'email comme lu
        mail.store(email_id, '+FLAGS', '\\Seen')
        
        mail.close()
        mail.logout()
        return True
    except Exception as e:
        logger.error(f"Erreur lors du marquage de l'email {email_id}: {e}")
        return False

def email_monitor_thread(timeout_minutes):
    """Thread qui surveille les emails et les met dans la queue"""
    print(f"📧 Thread de surveillance des emails démarré (timeout: {timeout_minutes} min)")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    check_interval = 10  # Vérifier toutes les 10 secondes
    
    while time.time() - start_time < timeout_seconds:
        try:
            # Lire les nouveaux emails sans les marquer comme lus
            replies = read_emails_without_marking()
            
            for reply in replies:
                # Vérifier si cet email a déjà été traité
                email_id = reply['email_id']
                with replies_lock:
                    if email_id not in student_replies:
                        # Marquer cet email comme lu pour éviter qu'il soit lu par d'autres
                        if mark_email_as_read(email_id):
                            student_replies[email_id] = reply
                            email_queue.put(reply)
                            print(f"📧 Email de {reply['from']} ajouté à la queue")
                        else:
                            print(f"⚠️ Impossible de marquer l'email {email_id} comme lu")
            
            remaining_time = timeout_seconds - (time.time() - start_time)
            if remaining_time > 0:
                time.sleep(check_interval)
                
        except Exception as e:
            print(f"❌ Erreur dans le thread de surveillance: {e}")
            time.sleep(check_interval)
    
    print("📧 Thread de surveillance des emails terminé")

def wait_for_reply_from_queue(student_email, timeout_minutes):
    """Attend une réponse d'un étudiant spécifique depuis la queue"""
    print(f"⏳ Attente d'une réponse de {student_email} depuis la queue...")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    check_interval = 2  # Vérifier toutes les 2 secondes
    
    while time.time() - start_time < timeout_seconds:
        try:
            # Vérifier si une réponse pour cet étudiant est dans la queue
            with replies_lock:
                for email_id, reply in student_replies.items():
                    if reply['from'].lower() == student_email.lower():
                        print(f"✅ Réponse trouvée pour {student_email} dans la queue!")
                        return reply
            
            remaining_time = timeout_seconds - (time.time() - start_time)
            if remaining_time > 0:
                time.sleep(check_interval)
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification de la queue: {e}")
            time.sleep(check_interval)
    
    print(f"⏰ Timeout atteint - Aucune réponse de {student_email}")
    return None

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
        
        # Étape 4: Attendre la réponse depuis la queue
        from email_reader import display_reply, save_reply_to_conversations
        
        print(f"⏳ Attente de la réponse de {student['username']} depuis la queue...")
        reply = wait_for_reply_from_queue(student['email'], timeout_minutes)
        
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
                    
                    # Créer une évaluation spéciale pour le cas merdique
                    merdique_evaluation = {
                        'raw_api_response': {
                            'success': True,
                            'message': 'Réponse inappropriée détectée',
                            'data': {
                                'score': 0,
                                'note': 0,
                                'feedback': """Votre réponse ne respecte pas les règles de base de la communication académique.

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
                        response=merdique_evaluation['raw_api_response']['data']['feedback'],
                        student_name=student['username'],
                        original_email=reply,  # Important pour le threading
                        is_merdique=True  # Nouveau paramètre pour indiquer que c'est une réponse merdique
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
        
        # Démarrer le thread de surveillance des emails
        email_monitor = threading.Thread(
            target=email_monitor_thread, 
            args=(timeout_minutes,),
            daemon=True
        )
        email_monitor.start()
        print("📧 Thread de surveillance des emails démarré")
        
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
        
        # Attendre que le thread de surveillance se termine
        email_monitor.join(timeout=10)
        
        # Résumé
        print("\n" + "📋" * 30)
        print("RÉSUMÉ FINAL")
        print("📋" * 30)
        print(f"✅ Étudiants traités avec succès: {success_count}/{len(students)}")
        print(f"📧 Emails traités: {len(student_replies)}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        print(f"   Détails: {traceback.format_exc()}")
        return False

def select_and_process_student(timeout_minutes=5):
    """Permet de sélectionner et traiter un étudiant spécifique"""
    print("\n" + "🎯" * 30)
    print("SÉLECTION D'UN ÉTUDIANT SPÉCIFIQUE")
    print("🎯" * 30)
    
    try:
        # Récupérer tous les étudiants
        students = get_all_students()
        if not students:
            print("❌ Aucun étudiant trouvé dans la base de données")
            return False
            
        print(f"\n👥 {len(students)} étudiants disponibles:")
        print("-" * 60)
        
        # Afficher la liste des étudiants
        for i, student in enumerate(students, 1):
            subscriptions_str = ', '.join(student['subscriptions']) if student['subscriptions'] else 'Aucun'
            print(f"{i:2d}. {student['username']} ({student['email']}) - Abonnements: {subscriptions_str}")
        
        # Demander la sélection
        while True:
            try:
                choice = input(f"\n👉 Sélectionnez un étudiant (1-{len(students)}) ou 'q' pour annuler: ").strip()
                
                if choice.lower() == 'q':
                    print("🚫 Opération annulée")
                    return False
                    
                student_index = int(choice) - 1
                if 0 <= student_index < len(students):
                    selected_student = students[student_index]
                    break
                else:
                    print(f"⚠️ Veuillez entrer un numéro entre 1 et {len(students)}")
            except ValueError:
                print("⚠️ Veuillez entrer un numéro valide ou 'q' pour annuler")
        
        print(f"\n✅ Étudiant sélectionné: {selected_student['username']} ({selected_student['email']})")
        
        # Confirmer l'envoi
        confirm = input(f"\n🚀 Envoyer le challenge à {selected_student['username']}? (o/n): ").strip().lower()
        if confirm not in ['o', 'oui', 'y', 'yes']:
            print("🚫 Envoi annulé")
            return False
        
        # Démarrer le thread de surveillance des emails pour cet étudiant
        email_monitor = threading.Thread(
            target=email_monitor_thread, 
            args=(timeout_minutes,),
            daemon=True
        )
        email_monitor.start()
        print("📧 Thread de surveillance des emails démarré")
        
        # Traiter l'étudiant sélectionné
        success = process_student(selected_student, timeout_minutes)
        
        # Attendre que le thread de surveillance se termine
        email_monitor.join(timeout=10)
        
        if success:
            print(f"\n✅ Traitement de {selected_student['username']} terminé avec succès!")
        else:
            print(f"\n❌ Échec du traitement de {selected_student['username']}")
            
        return success
        
    except Exception as e:
        print(f"❌ Erreur lors de la sélection de l'étudiant: {e}")
        import traceback
        print(f"   Détails: {traceback.format_exc()}")
        return False

def show_post_creation_menu(timeout_minutes=5):
    """Menu affiché après la création d'un utilisateur"""
    print("\n" + "🎉" * 30)
    print("UTILISATEUR CRÉÉ AVEC SUCCÈS!")
    print("🎉" * 30)
    
    while True:
        print("\n📋 QUE VOULEZ-VOUS FAIRE MAINTENANT?")
        print("1️⃣  Envoyer un challenge à l'utilisateur que je viens de créer")
        print("2️⃣  Envoyer des challenges à tous les étudiants")
        print("3️⃣  Envoyer un challenge à un étudiant spécifique")
        print("4️⃣  Retourner au menu principal")
        
        try:
            choice = input("\n👉 Votre choix (1-4): ").strip()
            
            if choice == "1":
                # Récupérer tous les étudiants et prendre le dernier créé
                students = get_all_students()
                if students:
                    # Le dernier étudiant dans la liste (le plus récemment créé)
                    latest_student = max(students, key=lambda x: x.get('id', 0))
                    print(f"\n🎯 Envoi du challenge à {latest_student['username']} ({latest_student['email']})")
                    
                    # Démarrer le thread de surveillance des emails
                    email_monitor = threading.Thread(
                        target=email_monitor_thread, 
                        args=(timeout_minutes,),
                        daemon=True
                    )
                    email_monitor.start()
                    
                    # Traiter l'étudiant
                    success = process_student(latest_student, timeout_minutes)
                    email_monitor.join(timeout=10)
                    
                    if success:
                        print(f"✅ Challenge envoyé avec succès à {latest_student['username']}!")
                    else:
                        print(f"❌ Échec de l'envoi à {latest_student['username']}")
                else:
                    print("❌ Aucun étudiant trouvé")
                break
                
            elif choice == "2":
                send_to_all_students(timeout_minutes)
                break
                
            elif choice == "3":
                select_and_process_student(timeout_minutes)
                break
                
            elif choice == "4":
                break
                
            else:
                print("⚠️ Choix invalide, veuillez sélectionner 1, 2, 3 ou 4")
                
        except KeyboardInterrupt:
            print("\n👋 Retour au menu principal")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("🦏 DEMO LE RHINO - SYSTÈME MAIL")
    print("="*60)
    
    # Menu principal
    while True:
        print("\n📋 OPTIONS DISPONIBLES:")
        print("1️⃣  Créer un nouvel utilisateur étudiant")
        print("2️⃣  Envoyer des challenges à tous les étudiants")
        print("3️⃣  Envoyer un challenge à un étudiant spécifique")
        print("4️⃣  Quitter")
        
        try:
            choice = input("\n👉 Votre choix (1-4): ").strip()
            
            if choice == "1":
                if create_user():
                    # Demander le timeout pour les opérations suivantes
                    try:
                        timeout_input = input("\n⏱️  Délai d'attente pour les réponses en minutes (défaut: 5): ").strip()
                        timeout_minutes = int(timeout_input) if timeout_input else 5
                    except ValueError:
                        print("⚠️ Valeur invalide, utilisation du délai par défaut (5 minutes)")
                        timeout_minutes = 5
                    
                    # Afficher le menu post-création
                    show_post_creation_menu(timeout_minutes)
                    
            elif choice == "2":
                # Demander le timeout
                try:
                    timeout_input = input("⏱️  Délai d'attente en minutes (défaut: 5): ").strip()
                    timeout_minutes = int(timeout_input) if timeout_input else 5
                except ValueError:
                    print("⚠️ Valeur invalide, utilisation du délai par défaut (5 minutes)")
                    timeout_minutes = 5
                
                # Lancer l'envoi à tous les étudiants
                send_to_all_students(timeout_minutes)
                
            elif choice == "3":
                # Demander le timeout
                try:
                    timeout_input = input("⏱️  Délai d'attente en minutes (défaut: 5): ").strip()
                    timeout_minutes = int(timeout_input) if timeout_input else 5
                except ValueError:
                    print("⚠️ Valeur invalide, utilisation du délai par défaut (5 minutes)")
                    timeout_minutes = 5
                
                # Sélectionner et traiter un étudiant spécifique
                select_and_process_student(timeout_minutes)
                
            elif choice == "4":
                print("👋 Au revoir!")
                break
            else:
                print("⚠️ Choix invalide, veuillez sélectionner 1, 2, 3 ou 4")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interruption détectée, au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main() 