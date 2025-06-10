#!/usr/bin/env python3
"""
Simple email reply reader functionality
"""

import imaplib
import email
import logging
import time
from typing import List, Dict, Optional
from config import EMAIL, PASSWORD, IMAP_HOST
from utils import load_conversations, save_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def connect_to_imap():
    """Établit une connexion IMAP à Gmail"""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')
        return mail
    except Exception as e:
        logger.error(f"Erreur connexion IMAP: {e}")
        return None

def read_new_replies() -> List[Dict]:
    """
    Lit les nouvelles réponses dans la boîte mail
    
    Returns:
        Liste des nouvelles réponses trouvées
    """
    mail = connect_to_imap()
    if not mail:
        return []
    
    try:
        # Chercher les emails non lus
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            logger.error("Erreur lors de la recherche d'emails")
            return []
        
        new_replies = []
        email_ids = messages[0].split()
        
        logger.info(f"🔍 {len(email_ids)} emails non lus trouvés")
        
        for email_id in email_ids:
            try:
                # Récupérer l'email
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

def extract_question_id(subject: str, body: str) -> Optional[str]:
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

def wait_for_reply(from_email: str, timeout_minutes: int = 5) -> Optional[Dict]:
    """
    Attend une réponse d'un email spécifique pendant un certain temps
    
    Args:
        from_email: Adresse email de l'expéditeur attendu
        timeout_minutes: Temps d'attente en minutes
    
    Returns:
        Dict contenant la réponse ou None si timeout
    """
    print(f"⏳ Attente d'une réponse de {from_email} (timeout: {timeout_minutes} min)...")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    check_interval = 10  # Vérifier toutes les 10 secondes
    
    while time.time() - start_time < timeout_seconds:
        remaining_time = timeout_seconds - (time.time() - start_time)
        print(f"🔄 Vérification des emails... (temps restant: {remaining_time/60:.1f} min)")
        
        replies = read_new_replies()
        
        for reply in replies:
            if reply['from'].lower() == from_email.lower():
                print(f"✅ Réponse reçue de {from_email}!")
                return reply
        
        if replies:
            print(f"📧 {len(replies)} réponses trouvées, mais pas de {from_email}")
        
        time.sleep(check_interval)
    
    print(f"⏰ Timeout atteint - Aucune réponse de {from_email}")
    return None

def display_reply(reply: Dict):
    """Affiche une réponse de manière formatée"""
    print("\n" + "📧" * 30)
    print("RÉPONSE REÇUE")
    print("📧" * 30)
    print(f"👤 De: {reply['from']}")
    print(f"📝 Sujet: {reply['subject']}")
    print(f"📅 Date: {reply['date']}")
    print(f"🔖 ID Question: {reply.get('question_id', 'Non identifié')}")
    print(f"📧 Message ID: {reply.get('message_id', 'Non disponible')}")
    print("\n📄 Contenu de la réponse:")
    print("-" * 50)
    print(reply['body'])
    print("-" * 50)

def save_reply_to_conversations(reply: Dict):
    """Sauvegarde la réponse dans le fichier conversations"""
    question_id = reply.get('question_id')
    if not question_id:
        logger.warning("Impossible de sauvegarder - ID question non trouvé")
        return False
    
    conversations = load_conversations()
    
    if question_id in conversations:
        conversations[question_id]['response'] = reply['body']
        conversations[question_id]['response_date'] = reply['date']
        conversations[question_id]['response_from'] = reply['from']
        save_conversations(conversations)
        logger.info(f"✅ Réponse sauvegardée pour {question_id}")
        return True
    else:
        logger.warning(f"Question ID {question_id} non trouvée dans les conversations")
        return False 