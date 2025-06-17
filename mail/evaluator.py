#!/usr/bin/env python3
"""
Simple response evaluation functionality
"""

import logging
import requests
import os
from typing import Dict, Optional
import re

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

def evaluate_response_simple(question: str, response: str, matiere: str, user_id: int = 1) -> Dict:
    """
    Évaluation d'une réponse via l'API d'évaluation
    
    Args:
        question: La question posée
        response: La réponse de l'étudiant
        matiere: La matière concernée
    
    Returns:
        Dict contenant la réponse brute de l'API
        
    Raises:
        Exception: Si l'API d'évaluation n'est pas disponible ou retourne une erreur
    """
    # Préparer les données pour l'API (format attendu par l'API)
    api_data = {
        'question': question,
        'reponse_etudiant': response,  # Changé de 'response' à 'reponse_etudiant'
        'matiere': matiere
    }
    
    # Appel à l'API d'évaluation avec user_id requis
    logger.info(f"Appel API d'évaluation pour la matière: {matiere} (user_id: {user_id})")
    api_response = requests.post(
        f'{API_BASE_URL}/evaluation/response?user_id={user_id}',  # Utilise le user_id de l'étudiant
        json=api_data,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    if api_response.status_code == 200:
        api_result = api_response.json()
        logger.info(f"✅ Évaluation réussie - API Response reçue")
        
        # Retourner la réponse brute de l'API pour l'instant
        return {
            'raw_api_response': api_result,
            'api_status': 'success',
            'status_code': api_response.status_code
        }
    else:
        logger.error(f"❌ Erreur API: {api_response.status_code} - {api_response.text}")
        raise Exception(f"Erreur API d'évaluation: {api_response.status_code}")

def clean_student_response(response: str) -> str:
    """
    Nettoie la réponse de l'étudiant en enlevant les parties non pertinentes
    
    Args:
        response: Réponse brute de l'étudiant
        
    Returns:
        str: Réponse nettoyée
    """
    if not response:
        return ""
        
    # Convertir en string si ce n'est pas déjà le cas
    response = str(response)
    
    # Enlever les parties de l'email original
    lines = response.split('\n')
    cleaned_lines = []
    skip_line = False
    
    for line in lines:
        # Ignorer les lignes de citation d'email
        if any(pattern in line.lower() for pattern in [
            'wrote:', 'écrit :', 'de :', 'from:', 'envoyé :', 'sent:',
            'objet :', 'subject:', 'date :', 'date:', 'à :', 'to:',
            'cc :', 'cc:', 'bcc :', 'bcc:', 'répondre à :', 'reply-to:'
        ]):
            skip_line = True
            continue
            
        # Ignorer les lignes de séparation d'email
        if line.strip().startswith('---') or line.strip().startswith('==='):
            skip_line = True
            continue
            
        # Ignorer les lignes de formatage d'email
        if line.strip().startswith('>'):
            skip_line = True
            continue
            
        # Réinitialiser skip_line si on trouve une ligne vide
        if not line.strip():
            skip_line = False
            
        # Ajouter la ligne si on ne doit pas la sauter
        if not skip_line:
            cleaned_lines.append(line)
    
    # Rejoindre les lignes et nettoyer
    cleaned = '\n'.join(cleaned_lines)
    
    # Enlever les espaces multiples
    cleaned = ' '.join(cleaned.split())
    
    # Enlever les retours à la ligne multiples
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    
    # Enlever les espaces au début et à la fin
    cleaned = cleaned.strip()
    
    return cleaned

def display_evaluation(evaluation: Dict, question: str, response: str):
    """Affiche l'évaluation de manière formatée"""
    import json
    
    # Nettoyer la réponse pour l'affichage
    clean_response = clean_student_response(response)
    
    print("\n" + "🤖" * 30)
    print("RÉPONSE BRUTE DE L'API D'ÉVALUATION")
    print("🤖" * 30)
    
    print(f"📝 Question: {question[:100]}...")
    print(f"📄 Réponse nettoyée: {clean_response[:100]}...")
    print(f"📊 Status Code: {evaluation.get('status_code', 'N/A')}")
    print(f"🔗 API Status: {evaluation.get('api_status', 'N/A')}")
    
    print("\n🤖 Réponse complète de l'API:")
    print(json.dumps(evaluation.get('raw_api_response', {}), indent=2, ensure_ascii=False))
    
    print("\n" + "🤖" * 30)

def evaluate_and_display(question: str, response: str, matiere: str, user_id: int = 1) -> Dict:
    """Évalue et affiche une réponse"""
    evaluation = evaluate_response_simple(question, response, matiere, user_id)
    display_evaluation(evaluation, question, response)
    return evaluation

def send_feedback_email(to_email: str, evaluation: Dict, question: str, response: str, student_name: str = None, original_email: Dict = None, is_merdique: bool = False) -> bool:
    """
    Envoie un email de feedback avec l'évaluation à l'étudiant en réponse à son email
    
    Args:
        to_email: Adresse email de l'étudiant
        evaluation: Dictionnaire contenant l'évaluation (ou réponse brute de l'API)
        question: Question originale
        response: Réponse de l'étudiant
        student_name: Nom de l'étudiant (optionnel)
        original_email: Dict contenant les infos de l'email original pour créer une réponse
        is_merdique: Indique si c'est une réponse inappropriée
    
    Returns:
        bool: True si envoyé avec succès
    """
    try:
        import yagmail
        from config import EMAIL, PASSWORD
        import json
        
        # Préparer le contenu du feedback
        student_greeting = f"Bonjour {student_name}" if student_name else "Bonjour"
        
        # Extraire les données de l'API
        api_data = evaluation.get('raw_api_response', {}).get('data', {})
        score = api_data.get('score', 'N/A')
        note = api_data.get('note', 'N/A')
        feedback = api_data.get('feedback', 'Aucun feedback disponible')
        
        if is_merdique:
            # Format simplifié pour les réponses inappropriées
            body = f"""{student_greeting},

RÉSULTAT
Note : {note}/20

FEEDBACK GÉNÉRAL
{feedback}"""
        else:
            # Format normal pour les autres réponses
            points_forts = api_data.get('points_forts', [])
            points_ameliorer = api_data.get('points_ameliorer', [])
            suggestions = api_data.get('suggestions', [])
            reponse_modele = api_data.get('reponse_modele', '')

            body = f"""{student_greeting},

Voici l'évaluation de votre réponse :

RÉSULTAT
Note : {note}/20

FEEDBACK GÉNÉRAL
{feedback}

POINTS FORTS
{chr(10).join([f"• {point}" for point in points_forts]) if points_forts else "• Aucun point fort identifié"}

POINTS À AMÉLIORER
{chr(10).join([f"• {point}" for point in points_ameliorer]) if points_ameliorer else "• Aucun point d'amélioration spécifique"}

SUGGESTIONS
{chr(10).join([f"• {suggestion}" for suggestion in suggestions]) if suggestions else "• Aucune suggestion spécifique"}

{f"RÉPONSE MODÈLE{chr(10)}{reponse_modele}" if reponse_modele else ""}

Cordialement,
Le Rhino"""

        # Envoi de l'email
        logger.info(f"Envoi du feedback à {to_email}")
        yag = yagmail.SMTP(EMAIL, PASSWORD)
        
        # Préparer les en-têtes pour créer une réponse dans le même thread
        headers = {}
        subject = None
        
        if original_email:
            # Conserver le sujet original
            original_subject = original_email.get('subject', '')
            if original_subject:
                # Si le sujet ne commence pas déjà par "Re: "
                if not original_subject.lower().startswith('re:'):
                    subject = f"Re: {original_subject}"
                else:
                    subject = original_subject
                logger.info(f"Utilisation du sujet original: {subject}")
            
            # Récupérer le message_id de l'email original
            original_message_id = original_email.get('message_id')
            if original_message_id:
                # Ajouter les headers de threading
                headers['In-Reply-To'] = original_message_id
                headers['References'] = original_message_id
                logger.info(f"Envoi en réponse au message ID: {original_message_id}")
            
            # Récupérer les références existantes si présentes
            existing_references = original_email.get('references', '')
            if existing_references:
                # Ajouter les références existantes
                headers['References'] = f"{existing_references} {original_message_id}"
                logger.info(f"Utilisation des références existantes: {existing_references}")
        
        # Si pas de sujet original, utiliser un sujet par défaut
        if not subject:
            subject = "Re: 🧠 Question du jour"
            logger.info("Utilisation du sujet par défaut")
        
        # Envoyer l'email avec les headers de threading
        if headers:
            logger.info("Envoi avec headers de threading")
            yag.send(to=to_email, subject=subject, contents=body, headers=headers)
        else:
            logger.info("Envoi sans headers de threading (fallback)")
            yag.send(to=to_email, subject=subject, contents=body)
        
        logger.info(f"✅ Feedback envoyé avec succès à {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi feedback: {e}")
        return False

# Les fonctions de formatage de l'ancien système d'évaluation ont été supprimées
# car nous utilisons maintenant la réponse brute de l'API d'évaluation

def send_apology_email(to_email: str, question: str, response: str, student_name: str = None, original_email: Dict = None, error_details: str = "") -> bool:
    """
    Envoie un email d'excuses lorsque l'évaluation automatique n'est pas disponible
    
    Args:
        to_email: Adresse email de l'étudiant
        question: Question originale
        response: Réponse de l'étudiant
        student_name: Nom de l'étudiant (optionnel)
        original_email: Dict contenant les infos de l'email original pour créer une réponse
        error_details: Détails de l'erreur (optionnel)
    
    Returns:
        bool: True si envoyé avec succès
    """
    try:
        import yagmail
        from config import EMAIL, PASSWORD
        
        # Préparer le contenu de l'email d'excuses
        student_greeting = f"Bonjour {student_name}" if student_name else "Bonjour"
        
        # Préparer le sujet en réponse à l'email original
        if original_email and original_email.get('subject'):
            original_subject = original_email['subject']
            # Supprimer les "Re: " existants pour éviter "Re: Re: ..."
            clean_subject = original_subject
            while clean_subject.startswith('Re: ') or clean_subject.startswith('RE: '):
                clean_subject = clean_subject[4:]
            subject = f"Re: {clean_subject} - ⚠️ Problème technique temporaire"
        else:
            subject = "⚠️ Problème technique temporaire - Évaluation différée"
        
        # Corps du message d'excuses en français
        body = f"""{student_greeting},

Nous vous remercions pour votre réponse à la question suivante :

📝 **QUESTION**
{question}

📄 **VOTRE RÉPONSE**
{response[:200]}{'...' if len(response) > 200 else ''}

⚠️ **PROBLÈME TECHNIQUE TEMPORAIRE**

Nous rencontrons actuellement un problème technique avec notre système d'évaluation automatique. 

🔧 **SOLUTION EN COURS**
• Notre équipe technique travaille activement à résoudre ce problème
• Votre réponse a bien été reçue et enregistrée
• L'évaluation sera effectuée dès que le système sera de nouveau opérationnel

📧 **PROCHAINES ÉTAPES**
Vous recevrez votre évaluation détaillée par email dès que notre système sera rétabli, généralement dans les 24 heures.

🙏 **SINCÈRES EXCUSES**
Nous nous excusons sincèrement pour ce désagrément temporaire et vous remercions de votre patience.

Si vous avez des questions urgentes, n'hésitez pas à nous contacter directement.

Cordialement,
L'équipe pédagogique 🎓

---
Détails techniques : Système d'évaluation temporairement indisponible
"""
        
        # Envoi de l'email avec en-têtes de réponse si disponibles
        logger.info(f"Envoi d'email d'excuses à {to_email}")
        yag = yagmail.SMTP(EMAIL, PASSWORD)
        
        # Préparer les en-têtes pour créer une réponse dans le même thread
        headers = {}
        if original_email:
            original_message_id = original_email.get('message_id')
            if original_message_id:
                headers['In-Reply-To'] = original_message_id
                headers['References'] = original_message_id
                logger.info(f"Envoi en réponse au message ID: {original_message_id}")
        
        if headers:
            yag.send(to=to_email, subject=subject, contents=body, headers=headers)
        else:
            yag.send(to=to_email, subject=subject, contents=body)
        
        logger.info(f"✅ Email d'excuses envoyé avec succès à {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi email d'excuses: {e}")
        return False

def evaluate_display_and_send_feedback(question: str, response: str, matiere: str, 
                                      student_email: str, student_name: str = None, original_email: Dict = None, user_id: int = 1) -> tuple:
    """
    Évalue une réponse, l'affiche et envoie le feedback par email
    
    Returns:
        tuple: (evaluation_dict, feedback_sent_success)
    """
    try:
        # Évaluer et afficher
        evaluation = evaluate_and_display(question, response, matiere, user_id)
        
        # S'assurer que original_email contient la matière
        if original_email is None:
            original_email = {}
        if 'matiere' not in original_email:
            original_email['matiere'] = matiere
        
        # Envoyer le feedback
        feedback_sent = send_feedback_email(student_email, evaluation, question, response, student_name, original_email)
        
        return evaluation, feedback_sent
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'évaluation: {e}")
        
        # Envoyer un email d'excuses en français
        apology_sent = send_apology_email(student_email, question, response, student_name, original_email, str(e))
        
        return None, apology_sent 