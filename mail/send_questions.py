# Fichier modifié : send_question.py
import yagmail
import requests
import logging
from typing import Optional, Dict, Any
from config import EMAIL, PASSWORD
from utils import generate_question_id, load_conversations, save_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration de l'API
API_BASE_URL = "http://localhost:8000/api"  # Modifiez selon votre configuration

class APIError(Exception):
    """Exception levée en cas d'erreur avec l'API"""
    pass

def get_challenge_from_api(user_id: Optional[int] = None, matiere: Optional[str] = None) -> Dict[str, Any]:
    """
    Récupère un challenge depuis l'API.
    
    Args:
        user_id: ID de l'utilisateur pour récupérer son challenge du jour
        matiere: Matière pour récupérer le prochain challenge disponible
    
    Returns:
        Dict contenant les informations du challenge
    
    Raises:
        APIError: En cas d'erreur lors de la récupération
    """
    try:
        if user_id:
            # Récupération du challenge du jour pour un utilisateur
            url = f"{API_BASE_URL}/challenges/today"
            params = {"user_id": user_id}
            logger.info(f"Récupération du challenge du jour pour l'utilisateur {user_id}")
            
        elif matiere:
            # Récupération du prochain challenge pour une matière
            url = f"{API_BASE_URL}/challenges/next"
            params = {"matiere": matiere}
            logger.info(f"Récupération du prochain challenge pour la matière {matiere}")
            
        else:
            raise APIError("user_id ou matiere doit être spécifié")
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("success"):
            raise APIError(f"API Error: {data.get('message', 'Erreur inconnue')}")
        
        challenge_data = data.get("data", {})
        
        # Extraction des informations du challenge selon le format de réponse
        if user_id:
            challenge = challenge_data.get("challenge")
            if not challenge:
                raise APIError("Aucun challenge disponible pour cet utilisateur")
            return {
                "question": challenge.get("question"),
                "matiere": challenge.get("matiere"),
                "challenge_id": challenge.get("challenge_id"),
                "ref": challenge.get("ref"),
                "user_info": challenge_data.get("user_info", {})
            }
        else:
            challenge = challenge_data.get("challenge")
            if not challenge:
                raise APIError("Aucun challenge disponible pour cette matière")
            return {
                "question": challenge.get("question"),
                "matiere": challenge.get("matiere"),
                "challenge_id": challenge.get("id"),
                "ref": challenge.get("ref")
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion à l'API: {e}")
        raise APIError(f"Impossible de se connecter à l'API: {e}")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du challenge: {e}")
        raise APIError(f"Erreur inattendue: {e}")

def send_question_from_api(to: str, user_id: Optional[int] = None, matiere: Optional[str] = None) -> bool:
    """
    Envoie une question récupérée depuis l'API à un utilisateur.
    
    Args:
        to: Email de destination
        user_id: ID de l'utilisateur pour son challenge personnalisé
        matiere: Matière pour un challenge spécifique
    
    Returns:
        bool: True si envoyé avec succès, False sinon
    """
    try:
        # Récupération du challenge depuis l'API
        logger.info(f"Récupération d'un challenge depuis l'API pour {to}")
        challenge_data = get_challenge_from_api(user_id=user_id, matiere=matiere)
        
        question = challenge_data.get("question")
        matiere_name = challenge_data.get("matiere", "Général")
        api_challenge_id = challenge_data.get("challenge_id")
        challenge_ref = challenge_data.get("ref", "N/A")
        
        if not question:
            logger.error("Question vide récupérée depuis l'API")
            return False
        
        # Génération de l'ID local pour le suivi email
        local_question_id = generate_question_id()
        
        # Préparation de l'email
        subject = f"🧠 Question du jour - {matiere_name} - {local_question_id}"
        body = f"""Bonjour,

Voici ta question du jour en {matiere_name} : {question}

Matière : {matiere_name}
Référence : {challenge_ref}

Bonne chance !
Le Rhino

[ID de suivi : {local_question_id}]
[ID Challenge API : {api_challenge_id}]
"""
        
        # Envoi de l'email
        logger.info(f"Envoi de la question à {to}")
        yag = yagmail.SMTP(EMAIL, PASSWORD)
        
        # Envoi simple et fiable
        yag.send(to=to, subject=subject, contents=body)
        
        logger.info(f"✅ Question envoyée à {to}")
        logger.info(f"   - ID local: {local_question_id}")
        logger.info(f"   - ID API: {api_challenge_id}")
        logger.info(f"   - Matière: {matiere_name}")
        logger.info(f"   - Référence: {challenge_ref}")
        
        # Sauvegarde dans la base de données
        from utils import save_question_to_db
        db_saved = save_question_to_db(
            question_id=local_question_id,
            student_email=to,
            question=question,
            matiere=matiere_name,
            challenge_ref=challenge_ref,
            api_challenge_id=api_challenge_id,
            user_id=user_id
        )
        
        # Fallback vers JSON si la base de données échoue
        if not db_saved:
            logger.warning("Échec de la sauvegarde en base de données, utilisation du JSON")
            conversations = load_conversations()
            conversations[local_question_id] = {
                "student": to,
                "question": question,
                "matiere": matiere_name,
                "challenge_ref": challenge_ref,
                "api_challenge_id": api_challenge_id,
                "response": None,
                "evaluated": False,
                "user_id": user_id
            }
            save_conversations(conversations)
        else:
            logger.info("✅ Question sauvegardée en base de données")
        
        return True
        
    except APIError as e:
        logger.error(f"❌ Erreur API: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Échec de l'envoi: {e}")
        return False

def send_question(to: str, question: str):
    """
    Fonction legacy pour envoyer une question hardcodée.
    Conservée pour compatibilité.
    """
    logger.warning("Utilisation de la fonction legacy send_question. Utilisez send_question_from_api à la place.")
    
    question_id = generate_question_id()
    subject = f"🧠 Question du jour - {question_id}"
    body = f"""Bonjour,

Voici ta question du jour :

❓ {question}

[ID de la question : {question_id}]
"""
    try:
        yag = yagmail.SMTP(EMAIL, PASSWORD)
        yag.send(to=to, subject=subject, contents=body)
        logger.info(f"✅ Question legacy envoyée à {to} avec l'ID {question_id}")
    except Exception as e:
        logger.error(f"❌ Échec de l'envoi legacy : {e}")
        return

    conversations = load_conversations()
    conversations[question_id] = {
        "student": to,
        "question": question,
        "response": None,
        "evaluated": False
    }
    save_conversations(conversations)

# Fonctions utilitaires pour différents cas d'usage
def send_daily_challenge_to_user(email: str, user_id: int) -> bool:
    """Envoie le challenge du jour personnalisé à un utilisateur"""
    return send_question_from_api(email, user_id=user_id)

def send_subject_challenge(email: str, matiere: str) -> bool:
    """Envoie un challenge pour une matière spécifique"""
    return send_question_from_api(email, matiere=matiere)

def test_api_connection() -> bool:
    """Teste la connexion à l'API"""
    try:
        response = requests.get(f"{API_BASE_URL}/challenges/today", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    # Tests et exemples d'utilisation
    
    # Test de connexion API
    if test_api_connection():
        logger.info("✅ Connexion API OK")
    else:
        logger.error("❌ Connexion API échouée")
    
    # Exemples d'utilisation :
    
    # 1. Envoyer le challenge du jour pour un utilisateur spécifique
    # success = send_daily_challenge_to_user("mathis.beaufour71@gmail.com", user_id=1)
    
    # 2. Envoyer un challenge pour une matière spécifique
    # success = send_subject_challenge("mathis.beaufour71@gmail.com", "informatique")
    
    # 3. Utilisation générale
    success = send_question_from_api("mathis.beaufour71@gmail.com", user_id=1)
    
    if success:
        logger.info("🎉 Challenge envoyé avec succès!")
    else:
        logger.error("💥 Échec de l'envoi du challenge")

# send_daily_challenge_to_user("student@example.com", user_id=1) 