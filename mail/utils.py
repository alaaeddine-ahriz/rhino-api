import json
import os
import sys
import uuid
from datetime import datetime
from config import CONV_FILE
from typing import Dict
import logging

# Ajouter le chemin pour les imports de l'application
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import conditionnel du service de base de données
try:
    from app.services.student_response_service import StudentResponseService
    # Temporarily force JSON usage to avoid DB errors
    DB_AVAILABLE = False  # Force to False to use JSON fallback
    print("🔧 Forçage de l'utilisation du JSON (base de données temporairement désactivée)")
except ImportError:
    DB_AVAILABLE = False
    print("Service de base de données non disponible, utilisation du JSON")

logger = logging.getLogger(__name__)

def generate_question_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return f"IDQ-{timestamp}-{uid}"

def save_conversations(conversations: Dict[str, Dict]) -> None:
    """Sauvegarde les conversations dans un fichier JSON avec horodatage."""
    try:
        # Créer le dossier archive s'il n'existe pas
        archive_dir = os.path.join(os.path.dirname(__file__), 'archive')
        os.makedirs(archive_dir, exist_ok=True)
        
        # Sauvegarder d'abord dans le fichier actuel
        current_file = os.path.join(archive_dir, 'current_conversations.json')
        with open(current_file, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
        
        # Créer une copie archivée avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_file = os.path.join(archive_dir, f'conversations_{timestamp}.json')
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Conversations sauvegardées dans {current_file} et archivées dans {archive_file}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la sauvegarde des conversations: {e}")
        raise

def load_conversations() -> Dict[str, Dict]:
    """Charge les conversations depuis le fichier JSON courant."""
    try:
        archive_dir = os.path.join(os.path.dirname(__file__), 'archive')
        current_file = os.path.join(archive_dir, 'current_conversations.json')
        
        # Si le fichier courant n'existe pas, retourner un dictionnaire vide
        if not os.path.exists(current_file):
            return {}
        
        with open(current_file, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        logger.info(f"✅ Conversations chargées depuis {current_file}")
        return conversations
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement des conversations: {e}")
        return {}

def save_question_to_db(question_id: str, student_email: str, question: str, 
                       matiere: str = None, challenge_ref: str = None, 
                       api_challenge_id: int = None, user_id: int = None,
                       sent_message_id: str = None) -> bool:
    """Nouvelle fonction pour sauvegarder directement en base de données."""
    if not DB_AVAILABLE:
        return False
    
    try:
        service = StudentResponseService()
        return service.save_question(
            question_id=question_id,
            student_email=student_email,
            question=question,
            matiere=matiere,
            challenge_ref=challenge_ref,
            api_challenge_id=api_challenge_id,
            user_id=user_id,
            sent_message_id=sent_message_id
        )
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la question: {e}")
        return False

def save_response_to_db(question_id: str, response: str, 
                       response_date: str = None, response_from: str = None) -> bool:
    """Nouvelle fonction pour sauvegarder directement une réponse en base de données."""
    if not DB_AVAILABLE:
        return False
    
    try:
        service = StudentResponseService()
        return service.save_response(
            question_id=question_id,
            response=response,
            response_date=response_date,
            response_from=response_from
        )
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de la réponse: {e}")
        return False

def save_evaluation_to_db(question_id: str, evaluation_data: dict) -> bool:
    """Nouvelle fonction pour sauvegarder directement une évaluation en base de données."""
    if not DB_AVAILABLE:
        return False
    
    try:
        service = StudentResponseService()
        return service.save_evaluation(
            question_id=question_id,
            evaluation_data=evaluation_data
        )
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de l'évaluation: {e}")
        return False

def get_conversation_from_db(question_id: str) -> dict:
    """Récupère une conversation depuis la base de données."""
    if not DB_AVAILABLE:
        return {}
    
    try:
        service = StudentResponseService()
        return service.get_student_response(question_id) or {}
    except Exception as e:
        print(f"Erreur lors de la récupération de la conversation: {e}")
        return {}

def get_unevaluated_responses_from_db() -> list:
    """Récupère les réponses non évaluées depuis la base de données."""
    if not DB_AVAILABLE:
        return []
    
    try:
        service = StudentResponseService()
        return service.get_unevaluated_responses()
    except Exception as e:
        print(f"Erreur lors de la récupération des réponses non évaluées: {e}")
        return [] 