import json
import os
import sys
import uuid
from datetime import datetime
from config import CONV_FILE

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

def generate_question_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    uid = uuid.uuid4().hex[:6]
    return f"IDQ-{timestamp}-{uid}"

def load_conversations():
    """Charge les conversations depuis la base de données ou le JSON en fallback."""
    if DB_AVAILABLE:
        try:
            # Utiliser la base de données en priorité
            service = StudentResponseService()
            # Pour la compatibilité, on ne retourne pas toutes les conversations
            # Cette fonction est maintenant dépréciée au profit des méthodes du service
            return {}
        except Exception as e:
            print(f"Erreur base de données, fallback vers JSON: {e}")
    
    # Fallback vers JSON
    if os.path.exists(CONV_FILE):
        with open(CONV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_conversations(conversations):
    """Sauvegarde les conversations en base de données et en JSON pour backup."""
    # Toujours sauvegarder en JSON pour backup
    with open(CONV_FILE, "w", encoding="utf-8") as f:
        json.dump(conversations, f, indent=2, ensure_ascii=False)
    
    # Si la base de données est disponible, migrer automatiquement
    if DB_AVAILABLE:
        try:
            service = StudentResponseService()
            for question_id, data in conversations.items():
                # Sauvegarder la question si elle n'existe pas
                if not service.question_exists(question_id):
                    service.save_question(
                        question_id=question_id,
                        student_email=data.get('student', ''),
                        question=data.get('question', ''),
                        matiere=data.get('matiere'),
                        challenge_ref=data.get('challenge_ref'),
                        api_challenge_id=data.get('api_challenge_id'),
                        user_id=data.get('user_id')
                    )
                
                # Sauvegarder la réponse si elle existe
                if data.get('response'):
                    service.save_response(
                        question_id=question_id,
                        response=data.get('response'),
                        response_date=data.get('response_date'),
                        response_from=data.get('response_from')
                    )
                
                # Sauvegarder l'évaluation si elle existe
                if data.get('evaluation'):
                    service.save_evaluation(
                        question_id=question_id,
                        evaluation_data=data.get('evaluation')
                    )
                
                # Marquer le feedback comme envoyé si nécessaire
                if data.get('feedback_sent'):
                    service.mark_feedback_sent(
                        question_id=question_id,
                        feedback_sent_to=data.get('feedback_sent_to', '')
                    )
        except Exception as e:
            print(f"Erreur lors de la sauvegarde en base de données: {e}")

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