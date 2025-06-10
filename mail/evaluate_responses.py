"""
Module d'évaluation des réponses des étudiants
"""
import requests
import logging
from typing import Optional, Dict, Any
from utils import load_conversations, save_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration de l'API
API_BASE_URL = "http://127.0.0.1:8000/api"

class EvaluationError(Exception):
    """Exception levée en cas d'erreur lors de l'évaluation"""
    pass

def evaluate_response_with_ai(question: str, response: str, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Évalue une réponse d'étudiant en utilisant l'IA
    
    Args:
        question: La question posée
        response: La réponse de l'étudiant
        context: Contexte additionnel (matière, référence, etc.)
    
    Returns:
        Dict contenant l'évaluation
    
    Raises:
        EvaluationError: En cas d'erreur lors de l'évaluation
    """
    try:
        url = f"{API_BASE_URL}/evaluations/evaluate"
        payload = {
            "question": question,
            "response": response,
            "context": context or ""
        }
        
        logger.info(f"Envoi de l'évaluation à l'API...")
        response_api = requests.post(url, json=payload, timeout=30)
        response_api.raise_for_status()
        
        data = response_api.json()
        
        if not data.get("success"):
            raise EvaluationError(f"API Error: {data.get('message', 'Erreur inconnue')}")
        
        evaluation = data.get("data", {})
        return {
            "score": evaluation.get("score", 0),
            "feedback": evaluation.get("feedback", ""),
            "points_positifs": evaluation.get("points_positifs", []),
            "points_amelioration": evaluation.get("points_amelioration", []),
            "note_sur_20": evaluation.get("note_sur_20", 0)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur de connexion à l'API d'évaluation: {e}")
        raise EvaluationError(f"Impossible de se connecter à l'API: {e}")
    except Exception as e:
        logger.error(f"Erreur lors de l'évaluation: {e}")
        raise EvaluationError(f"Erreur inattendue: {e}")

def evaluate_pending_responses() -> int:
    """
    Évalue toutes les réponses en attente
    
    Returns:
        Nombre de réponses évaluées
    """
    conversations = load_conversations()
    evaluated_count = 0
    
    for question_id, conv in conversations.items():
        # Vérifier si la réponse existe et n'est pas déjà évaluée
        if conv.get("response") and not conv.get("evaluated"):
            try:
                logger.info(f"Évaluation de la réponse pour l'ID {question_id}")
                
                # Préparer le contexte
                context = f"Matière: {conv.get('matiere', 'N/A')}, Référence: {conv.get('challenge_ref', 'N/A')}"
                
                # Évaluer la réponse
                evaluation = evaluate_response_with_ai(
                    question=conv["question"],
                    response=conv["response"],
                    context=context
                )
                
                # Mettre à jour la conversation
                conversations[question_id]["evaluation"] = evaluation
                conversations[question_id]["evaluated"] = True
                
                logger.info(f"✅ Réponse évaluée pour {conv['student']}")
                logger.info(f"   - Note: {evaluation['note_sur_20']}/20")
                logger.info(f"   - Score: {evaluation['score']}%")
                
                evaluated_count += 1
                
            except EvaluationError as e:
                logger.error(f"❌ Erreur d'évaluation pour l'ID {question_id}: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Erreur inattendue pour l'ID {question_id}: {e}")
                continue
    
    # Sauvegarder les modifications
    if evaluated_count > 0:
        save_conversations(conversations)
        logger.info(f"💾 {evaluated_count} évaluation(s) sauvegardée(s)")
    
    return evaluated_count

def get_evaluation_report() -> Dict[str, Any]:
    """
    Génère un rapport d'évaluation
    
    Returns:
        Dict contenant les statistiques d'évaluation
    """
    conversations = load_conversations()
    
    total_responses = 0
    evaluated_responses = 0
    pending_responses = 0
    total_score = 0
    scores = []
    
    for conv in conversations.values():
        if conv.get("response"):
            total_responses += 1
            
            if conv.get("evaluated"):
                evaluated_responses += 1
                evaluation = conv.get("evaluation", {})
                score = evaluation.get("note_sur_20", 0)
                scores.append(score)
                total_score += score
            else:
                pending_responses += 1
    
    average_score = total_score / evaluated_responses if evaluated_responses > 0 else 0
    
    return {
        "total_responses": total_responses,
        "evaluated_responses": evaluated_responses,
        "pending_responses": pending_responses,
        "average_score": round(average_score, 2),
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "all_scores": scores
    }

def print_evaluation_report():
    """Affiche un rapport d'évaluation formaté"""
    report = get_evaluation_report()
    
    print("\n" + "="*50)
    print("📊 RAPPORT D'ÉVALUATION")
    print("="*50)
    print(f"📨 Total des réponses: {report['total_responses']}")
    print(f"✅ Réponses évaluées: {report['evaluated_responses']}")
    print(f"⏳ Réponses en attente: {report['pending_responses']}")
    
    if report['evaluated_responses'] > 0:
        print(f"📈 Note moyenne: {report['average_score']}/20")
        print(f"🏆 Meilleure note: {report['max_score']}/20")
        print(f"📉 Note la plus basse: {report['min_score']}/20")
    
    print("="*50)

def test_evaluation_api() -> bool:
    """Teste la connexion à l'API d'évaluation"""
    try:
        response = requests.get(f"{API_BASE_URL}/evaluations/", timeout=5)
        return response.status_code in [200, 404]  # 404 peut être normal si l'endpoint n'existe pas encore
    except:
        return False

if __name__ == "__main__":
    # Test de connexion API
    if test_evaluation_api():
        logger.info("✅ Connexion API d'évaluation OK")
    else:
        logger.warning("⚠️ API d'évaluation non disponible")
    
    # Évaluer les réponses en attente
    count = evaluate_pending_responses()
    
    if count > 0:
        logger.info(f"🎉 {count} réponse(s) évaluée(s) avec succès!")
        print_evaluation_report()
    else:
        logger.info("ℹ️ Aucune réponse en attente d'évaluation")
        print_evaluation_report() 