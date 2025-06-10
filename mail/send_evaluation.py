"""
Module pour envoyer les résultats d'évaluation aux étudiants par email
"""
import yagmail
import logging
from typing import Dict, Any
from config import EMAIL, PASSWORD
from utils import load_conversations, save_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def format_evaluation_email(evaluation: Dict[str, Any], student_name: str = "étudiant") -> str:
    """
    Formate les résultats d'évaluation en email HTML
    
    Args:
        evaluation: Résultats de l'évaluation
        student_name: Nom de l'étudiant
    
    Returns:
        str: Contenu de l'email formaté
    """
    score = evaluation.get("score", 0)
    note_sur_20 = evaluation.get("note", 0)
    feedback = evaluation.get("feedback", "")
    points_forts = evaluation.get("points_forts", [])
    points_ameliorer = evaluation.get("points_ameliorer", [])
    justification = evaluation.get("justification_note", "")
    suggestions = evaluation.get("suggestions", [])
    
    # Déterminer l'emoji selon la note
    if note_sur_20 >= 16:
        score_emoji = "🎉"
        performance = "Excellent"
    elif note_sur_20 >= 14:
        score_emoji = "👏"
        performance = "Très bien"
    elif note_sur_20 >= 12:
        score_emoji = "👍"
        performance = "Bien"
    elif note_sur_20 >= 10:
        score_emoji = "📈"
        performance = "Assez bien"
    else:
        score_emoji = "💪"
        performance = "À améliorer"
    
    email_content = f"""
Bonjour {student_name},

🤖 **ÉVALUATION AUTOMATIQUE DE VOTRE RÉPONSE**

{score_emoji} **NOTE: {note_sur_20}/20 ({score}%) - {performance}**

📝 **FEEDBACK GÉNÉRAL:**
{feedback}

"""
    
    if points_forts:
        email_content += "✅ **POINTS FORTS:**\n"
        for point in points_forts:
            email_content += f"• {point}\n"
        email_content += "\n"
    
    if points_ameliorer:
        email_content += "🔧 **POINTS À AMÉLIORER:**\n"
        for point in points_ameliorer:
            email_content += f"• {point}\n"
        email_content += "\n"
    
    if justification:
        email_content += f"💭 **JUSTIFICATION DE LA NOTE:**\n{justification}\n\n"
    
    if suggestions:
        email_content += "💡 **SUGGESTIONS:**\n"
        for suggestion in suggestions:
            email_content += f"• {suggestion}\n"
        email_content += "\n"
    
    email_content += """
📚 Continuez vos efforts et n'hésitez pas à poser des questions !

Cordialement,
L'équipe pédagogique 🎓
"""
    
    return email_content

def send_evaluation_to_student(
    student_email: str, 
    evaluation: Dict[str, Any], 
    original_question: str,
    question_id: str,
    student_name: str = None
) -> bool:
    """
    Envoie les résultats d'évaluation à un étudiant
    
    Args:
        student_email: Email de l'étudiant
        evaluation: Résultats de l'évaluation
        original_question: Question originale
        question_id: ID de la question
        student_name: Nom de l'étudiant (optionnel)
    
    Returns:
        bool: True si envoyé avec succès
    """
    try:
        # Extraire le nom de l'étudiant depuis l'email si pas fourni
        if not student_name:
            student_name = student_email.split('@')[0].replace('.', ' ').title()
        
        # Formater le contenu de l'email
        email_body = format_evaluation_email(evaluation, student_name)
        
        # Créer le sujet
        note_sur_20 = evaluation.get("note", 0)
        matiere = evaluation.get("matiere", "")
        subject = f"🎓 Évaluation de votre réponse - {note_sur_20}/20"
        if matiere:
            subject += f" - {matiere}"
        subject += f" - {question_id}"
        
        # Envoyer l'email
        logger.info(f"Envoi de l'évaluation à {student_email}")
        yag = yagmail.SMTP(EMAIL, PASSWORD)
        yag.send(
            to=student_email,
            subject=subject,
            contents=email_body
        )
        
        logger.info(f"✅ Évaluation envoyée avec succès à {student_email}")
        logger.info(f"   - Note: {note_sur_20}/20")
        logger.info(f"   - Score: {evaluation.get('score', 0)}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'envoi de l'évaluation à {student_email}: {e}")
        return False

def send_evaluations_for_pending_responses() -> int:
    """
    Envoie les évaluations pour toutes les réponses évaluées mais pas encore envoyées
    
    Returns:
        int: Nombre d'évaluations envoyées
    """
    conversations = load_conversations()
    sent_count = 0
    
    for question_id, conv in conversations.items():
        # Vérifier si la réponse est évaluée mais l'évaluation pas encore envoyée
        if (conv.get("evaluated") and 
            conv.get("evaluation") and 
            not conv.get("evaluation_sent", False)):
            
            try:
                student_email = conv.get("student")
                evaluation = conv.get("evaluation")
                original_question = conv.get("question", "Question non disponible")
                
                if not student_email or not evaluation:
                    logger.warning(f"Données manquantes pour l'ID {question_id}")
                    continue
                
                # Envoyer l'évaluation
                success = send_evaluation_to_student(
                    student_email=student_email,
                    evaluation=evaluation,
                    original_question=original_question,
                    question_id=question_id
                )
                
                if success:
                    # Marquer comme envoyé
                    conversations[question_id]["evaluation_sent"] = True
                    sent_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors du traitement de l'ID {question_id}: {e}")
                continue
    
    # Sauvegarder les modifications
    if sent_count > 0:
        save_conversations(conversations)
        logger.info(f"💾 {sent_count} évaluation(s) marquée(s) comme envoyée(s)")
    
    return sent_count

def get_evaluation_send_report() -> Dict[str, Any]:
    """
    Génère un rapport sur l'envoi des évaluations
    
    Returns:
        Dict contenant les statistiques d'envoi
    """
    conversations = load_conversations()
    
    total_evaluated = 0
    evaluations_sent = 0
    evaluations_pending = 0
    
    for conv in conversations.values():
        if conv.get("evaluated") and conv.get("evaluation"):
            total_evaluated += 1
            
            if conv.get("evaluation_sent", False):
                evaluations_sent += 1
            else:
                evaluations_pending += 1
    
    return {
        "total_evaluated": total_evaluated,
        "evaluations_sent": evaluations_sent,
        "evaluations_pending": evaluations_pending,
        "send_rate": round(evaluations_sent / total_evaluated * 100, 2) if total_evaluated > 0 else 0
    }

def print_evaluation_send_report():
    """Affiche un rapport d'envoi des évaluations formaté"""
    report = get_evaluation_send_report()
    
    print("\n" + "="*50)
    print("📧 RAPPORT D'ENVOI DES ÉVALUATIONS")
    print("="*50)
    print(f"🤖 Total évaluations terminées: {report['total_evaluated']}")
    print(f"✅ Évaluations envoyées: {report['evaluations_sent']}")
    print(f"⏳ Évaluations en attente d'envoi: {report['evaluations_pending']}")
    print(f"📊 Taux d'envoi: {report['send_rate']}%")
    print("="*50)

if __name__ == "__main__":
    # Envoyer les évaluations en attente
    count = send_evaluations_for_pending_responses()
    
    if count > 0:
        logger.info(f"🎉 {count} évaluation(s) envoyée(s) avec succès!")
    else:
        logger.info("ℹ️ Aucune évaluation en attente d'envoi")
    
    # Afficher le rapport
    print_evaluation_send_report() 