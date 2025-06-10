#!/usr/bin/env python3
"""
Simple response evaluation functionality
"""

import logging
import requests
from typing import Dict, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def evaluate_response_simple(question: str, response: str, matiere: str) -> Dict:
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
    logger.info(f"Appel API d'évaluation pour la matière: {matiere}")
    api_response = requests.post(
        'http://localhost:8000/api/evaluation/response?user_id=1',  # Ajout du user_id requis
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

# Les fonctions d'évaluation locales ont été supprimées car l'évaluation
# se fait maintenant via l'API /api/evaluation/response

def display_evaluation(evaluation: Dict, question: str, response: str):
    """Affiche l'évaluation de manière formatée"""
    import json
    
    print("\n" + "🤖" * 30)
    print("RÉPONSE BRUTE DE L'API D'ÉVALUATION")
    print("🤖" * 30)
    
    print(f"📝 Question: {question[:100]}...")
    print(f"📄 Réponse: {response[:100]}...")
    print(f"📊 Status Code: {evaluation.get('status_code', 'N/A')}")
    print(f"🔗 API Status: {evaluation.get('api_status', 'N/A')}")
    
    print("\n🤖 Réponse complète de l'API:")
    print(json.dumps(evaluation.get('raw_api_response', {}), indent=2, ensure_ascii=False))
    
    print("\n" + "🤖" * 30)

def evaluate_and_display(question: str, response: str, matiere: str) -> Dict:
    """Évalue et affiche une réponse"""
    evaluation = evaluate_response_simple(question, response, matiere)
    display_evaluation(evaluation, question, response)
    return evaluation

def send_feedback_email(to_email: str, evaluation: Dict, question: str, response: str, student_name: str = None, original_email: Dict = None) -> bool:
    """
    Envoie un email de feedback avec l'évaluation à l'étudiant en réponse à son email
    
    Args:
        to_email: Adresse email de l'étudiant
        evaluation: Dictionnaire contenant l'évaluation (ou réponse brute de l'API)
        question: Question originale
        response: Réponse de l'étudiant
        student_name: Nom de l'étudiant (optionnel)
        original_email: Dict contenant les infos de l'email original pour créer une réponse
    
    Returns:
        bool: True si envoyé avec succès
    """
    try:
        import yagmail
        from config import EMAIL, PASSWORD
        import json
        
        # Préparer le contenu du feedback
        student_greeting = f"Bonjour {student_name}" if student_name else "Bonjour"
        
        # Préparer le sujet en réponse à l'email original
        if original_email and original_email.get('subject'):
            original_subject = original_email['subject']
            # Supprimer les "Re: " existants pour éviter "Re: Re: ..."
            clean_subject = original_subject
            while clean_subject.startswith('Re: ') or clean_subject.startswith('RE: '):
                clean_subject = clean_subject[4:]
            subject = f"Re: {clean_subject} - 🤖 Réponse de l'API d'évaluation"
        else:
            subject = "🤖 Réponse de l'API d'évaluation"
        
        # Corps du message avec la réponse brute de l'API
        body = f"""{student_greeting},

Voici la réponse brute de l'API d'évaluation pour votre question :

📝 **QUESTION POSÉE**
{question}

📄 **VOTRE RÉPONSE**
{response[:200]}{'...' if len(response) > 200 else ''}

🤖 **RÉPONSE BRUTE DE L'API**
```json
{json.dumps(evaluation, indent=2, ensure_ascii=False)}
```

📊 **INFORMATIONS TECHNIQUES**
• Status Code: {evaluation.get('status_code', 'N/A')}
• API Status: {evaluation.get('api_status', 'N/A')}

Cordialement,
Le système d'évaluation automatique 🤖

---
Note: Cette réponse contient les données brutes de l'API pour debug/développement.
"""
        
        # Envoi de l'email avec en-têtes de réponse si disponibles
        logger.info(f"Envoi du feedback à {to_email}")
        yag = yagmail.SMTP(EMAIL, PASSWORD)
        
        # Préparer les en-têtes pour créer une réponse dans le même thread
        headers = {}
        if original_email:
            # Extraire le Message-ID de l'email original
            original_message_id = original_email.get('message_id')
            if original_message_id:
                headers['In-Reply-To'] = original_message_id
                headers['References'] = original_message_id
                logger.info(f"Envoi en réponse au message ID: {original_message_id}")
        
        if headers:
            # Envoyer avec en-têtes personnalisés pour créer une réponse
            yag.send(to=to_email, subject=subject, contents=body, headers=headers)
        else:
            # Envoi normal si pas d'informations pour la réponse
            yag.send(to=to_email, subject=subject, contents=body)
        
        logger.info(f"✅ Feedback envoyé avec succès à {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur envoi feedback: {e}")
        return False

def format_evaluation_details(evaluation: Dict) -> str:
    """Formate les détails de l'évaluation pour l'email"""
    details = evaluation['details']
    return f"""• Longueur de réponse : {details['length_score']}/20 points ({details['response_length']} caractères)
• Nombre de mots : {details['word_score']}/15 points ({details['word_count']} mots)
• Mots-clés techniques : {details['keyword_score']}/25 points
• Structure et présentation : {details['structure_score']}/20 points
• Effort et réflexion : {details['effort_score']}/20 points"""

def format_feedback_list(feedback_list: list) -> str:
    """Formate la liste de feedback pour l'email"""
    return '\n'.join([f"• {feedback}" for feedback in feedback_list])

def format_recommendations(score: int) -> str:
    """Génère des recommandations basées sur le score"""
    if score < 60:
        return """• Développez davantage votre réponse pour montrer votre compréhension
• Utilisez des termes techniques appropriés à la matière
• Structurez votre réponse en paragraphes clairs
• Ajoutez des exemples concrets pour illustrer vos propos"""
    elif score < 80:
        return """• Bonne base ! Ajoutez plus d'exemples concrets
• Approfondissez certains aspects de votre explication
• Utilisez plus de vocabulaire technique spécialisé"""
    else:
        return """• Excellente réponse ! Continuez sur cette lancée
• Votre maîtrise du sujet est évidente
• La structure et le contenu sont très satisfaisants"""

def format_encouragement(grade: str) -> str:
    """Génère un message d'encouragement basé sur la note"""
    encouragements = {
        'A+': "🌟 Travail exceptionnel ! Vous maîtrisez parfaitement le sujet.",
        'A': "🎉 Très bon travail ! Vous démontrez une solide compréhension.",
        'B': "👍 Bon travail ! Continuez vos efforts, vous êtes sur la bonne voie.",
        'C': "💪 Travail correct. Avec un peu plus d'effort, vous pouvez encore progresser.",
        'D': "📚 Il y a des améliorations à apporter. N'hésitez pas à approfondir vos révisions.",
        'F': "🔄 Cette réponse nécessite plus de travail. Reprenez les concepts de base et n'hésitez pas à demander de l'aide."
    }
    return encouragements.get(grade, "Continuez vos efforts !")

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
                                      student_email: str, student_name: str = None, original_email: Dict = None) -> tuple:
    """
    Évalue une réponse, l'affiche et envoie le feedback par email
    
    Returns:
        tuple: (evaluation_dict, feedback_sent_success)
    """
    try:
        # Évaluer et afficher
        evaluation = evaluate_and_display(question, response, matiere)
        
        # Envoyer le feedback
        feedback_sent = send_feedback_email(student_email, evaluation, question, response, student_name, original_email)
        
        return evaluation, feedback_sent
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'évaluation: {e}")
        
        # Envoyer un email d'excuses en français
        apology_sent = send_apology_email(student_email, question, response, student_name, original_email, str(e))
        
        return None, apology_sent 