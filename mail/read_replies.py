# Fichier amélioré : read_replies.py
import re
import pyzmail
import imapclient
import logging
from config import EMAIL, PASSWORD, IMAP_HOST
from utils import load_conversations, save_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def extract_id_from_subject(subject):
    """Extrait l'ID de question depuis le sujet de l'email"""
    match = re.search(r"IDQ-\d{14}-[a-f0-9]{6}", subject)
    return match.group(0) if match else None

def clean_response(response_text):
    """Nettoie la réponse en supprimant les métadonnées de l'email original"""
    lines = response_text.split('\n')
    clean_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Arrêter si on trouve une ligne de citation email
        if (re.match(r'^(Le|On|-----|\r|>)', line_stripped) or
            '@gmail.com' in line or
            'a écrit :' in line or
            line_stripped.startswith('From:') or
            line_stripped.startswith('To:') or
            line_stripped.startswith('Date:')):
            break
            
        # Ignorer les lignes vides au début
        if not clean_lines and not line_stripped:
            continue
            
        clean_lines.append(line)
    
    # Joindre et nettoyer les espaces
    cleaned = '\n'.join(clean_lines).strip()
    
    # Supprimer les retours chariot Windows
    cleaned = cleaned.replace('\r', '')
    
    # Limiter à une longueur raisonnable (éviter les réponses trop longues)
    if len(cleaned) > 1000:
        cleaned = cleaned[:1000] + "..."
    
    return cleaned

def decode_payload(message):
    """Décode le contenu du message email"""
    if message.text_part:
        try:
            charset = message.text_part.charset or 'utf-8'
            return message.text_part.get_payload().decode(charset)
        except (UnicodeDecodeError, AttributeError):
            try:
                return message.text_part.get_payload().decode("utf-8", errors="ignore")
            except:
                return message.text_part.get_payload().decode("iso-8859-1", errors="ignore")
    return "(Pas de contenu texte)"

def read_replies():
    """Lit les réponses des étudiants depuis la boîte mail"""
    logger.info("📥 Connexion à la boîte mail...")
    
    try:
        # Connexion IMAP
        client = imapclient.IMAPClient(IMAP_HOST, ssl=True)
        client.login(EMAIL, PASSWORD)
        client.select_folder("INBOX")
        
        # Recherche des messages de réponse (non lus uniquement)
        messages = client.search(['SUBJECT', 'Re: Question du jour', 'UNSEEN'])
        logger.info(f"📨 {len(messages)} nouveau(x) message(s) trouvé(s)")
        
        if not messages:
            logger.info("Aucun nouveau message à traiter")
            client.logout()
            return
        
        conversations = load_conversations()
        processed_count = 0
        
        for uid in messages:
            try:
                # Récupération du message
                raw_message = client.fetch([uid], ['BODY[]'])[uid][b'BODY[]']
                message = pyzmail.PyzMessage.factory(raw_message)
                
                # Extraction des informations
                from_email = message.get_addresses('from')[0][1]
                subject = message.get_subject()
                question_id = extract_id_from_subject(subject)
                
                if not question_id:
                    logger.warning(f"ID de question non trouvé dans le sujet: {subject}")
                    continue
                
                # Décodage et nettoyage de la réponse
                raw_body = decode_payload(message)
                response_text = clean_response(raw_body)
                
                if not response_text:
                    logger.warning(f"Réponse vide pour l'ID {question_id}")
                    continue
                
                logger.info(f"\n🧑‍🎓 De : {from_email}")
                logger.info(f"📌 ID Question : {question_id}")
                logger.info(f"📝 Réponse : {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
                
                # Mise à jour de la conversation
                if question_id in conversations:
                    conversations[question_id]["response"] = response_text
                    logger.info(f"✅ Réponse mise à jour pour l'ID {question_id}")
                else:
                    # Créer une nouvelle entrée si l'ID n'existe pas
                    conversations[question_id] = {
                        "student": from_email,
                        "question": "(question inconnue - ID non trouvé)",
                        "response": response_text,
                        "evaluated": False
                    }
                    logger.warning(f"⚠️ Nouvelle conversation créée pour l'ID inconnu {question_id}")
                
                # Marquer le message comme lu
                client.add_flags([uid], ['\\Seen'])
                processed_count += 1
                
            except Exception as e:
                logger.error(f"❌ Erreur lors du traitement du message {uid}: {e}")
                continue
        
        # Sauvegarde des conversations
        save_conversations(conversations)
        logger.info(f"💾 {processed_count} réponse(s) traitée(s) et sauvegardée(s)")
        
        # Déconnexion
        client.logout()
        logger.info("🔌 Déconnexion de la boîte mail")
        
    except imapclient.exceptions.LoginError:
        logger.error("❌ Erreur de connexion: Vérifiez vos identifiants email")
    except Exception as e:
        logger.error(f"❌ Erreur générale lors de la lecture des emails: {e}")

def get_unread_count():
    """Retourne le nombre de messages non lus"""
    try:
        client = imapclient.IMAPClient(IMAP_HOST, ssl=True)
        client.login(EMAIL, PASSWORD)
        client.select_folder("INBOX")
        
        messages = client.search(['SUBJECT', 'Re: Question du jour', 'UNSEEN'])
        count = len(messages)
        
        client.logout()
        return count
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du comptage des messages non lus: {e}")
        return 0

if __name__ == "__main__":
    read_replies() 