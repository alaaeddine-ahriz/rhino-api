#!/usr/bin/env python3
"""
Simple response evaluation functionality
"""

import logging
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
    Évaluation simple d'une réponse basée sur des critères de base
    
    Args:
        question: La question posée
        response: La réponse de l'étudiant
        matiere: La matière concernée
    
    Returns:
        Dict contenant l'évaluation
    """
    evaluation = {
        'score': 0,
        'max_score': 100,
        'feedback': [],
        'grade': 'F',
        'details': {}
    }
    
    # Critères de base
    response_length = len(response.strip())
    word_count = len(response.split())
    
    # Critère 1: Longueur de la réponse (20 points max)
    if response_length < 50:
        evaluation['feedback'].append("❌ Réponse trop courte (moins de 50 caractères)")
        length_score = 0
    elif response_length < 200:
        evaluation['feedback'].append("⚠️ Réponse courte mais acceptable")
        length_score = 10
    elif response_length < 500:
        evaluation['feedback'].append("✅ Longueur de réponse appropriée")
        length_score = 20
    else:
        evaluation['feedback'].append("✅ Réponse détaillée")
        length_score = 20
    
    # Critère 2: Nombre de mots (15 points max)
    if word_count < 10:
        evaluation['feedback'].append("❌ Réponse trop brève (moins de 10 mots)")
        word_score = 0
    elif word_count < 50:
        evaluation['feedback'].append("⚠️ Réponse succincte")
        word_score = 8
    else:
        evaluation['feedback'].append("✅ Réponse développée")
        word_score = 15
    
    # Critère 3: Présence de mots-clés selon la matière (25 points max)
    keyword_score = check_keywords_by_subject(response, matiere)
    
    # Critère 4: Structure et présentation (20 points max)
    structure_score = check_structure(response)
    
    # Critère 5: Effort apparent (20 points max)
    effort_score = check_effort(response)
    
    # Calcul du score total
    total_score = length_score + word_score + keyword_score + structure_score + effort_score
    evaluation['score'] = min(total_score, 100)
    
    # Attribution de la note
    if evaluation['score'] >= 90:
        evaluation['grade'] = 'A+'
    elif evaluation['score'] >= 80:
        evaluation['grade'] = 'A'
    elif evaluation['score'] >= 70:
        evaluation['grade'] = 'B'
    elif evaluation['score'] >= 60:
        evaluation['grade'] = 'C'
    elif evaluation['score'] >= 50:
        evaluation['grade'] = 'D'
    else:
        evaluation['grade'] = 'F'
    
    # Détails des scores
    evaluation['details'] = {
        'length_score': length_score,
        'word_score': word_score,
        'keyword_score': keyword_score,
        'structure_score': structure_score,
        'effort_score': effort_score,
        'response_length': response_length,
        'word_count': word_count
    }
    
    return evaluation

def check_keywords_by_subject(response: str, matiere: str) -> int:
    """Vérifie la présence de mots-clés spécifiques à la matière"""
    response_lower = response.lower()
    score = 0
    
    keywords = {
        'SYD': ['système', 'distribué', 'réseau', 'serveur', 'client', 'protocole', 'tcp', 'udp', 'http', 'consensus', 'raft', 'byzantine', 'cohérence', 'disponibilité', 'partition'],
        'TCP': ['tcp', 'protocole', 'transport', 'fiable', 'connexion', 'segment', 'port', 'socket', 'flow control', 'congestion', 'window', 'acknowledgment', 'handshake', 'syn', 'ack'],
        'MATH': ['équation', 'fonction', 'dérivée', 'intégrale', 'limite', 'calcul', 'mathématique', 'formule', 'variable', 'constante'],
        'PHYS': ['force', 'énergie', 'masse', 'vitesse', 'accélération', 'newton', 'joule', 'physique', 'gravité', 'électricité'],
        'INFO': ['algorithme', 'programmation', 'code', 'variable', 'fonction', 'boucle', 'condition', 'données', 'structure', 'informatique']
    }
    
    subject_keywords = keywords.get(matiere, [])
    
    found_keywords = []
    for keyword in subject_keywords:
        if keyword in response_lower:
            found_keywords.append(keyword)
            score += 2  # 2 points par mot-clé trouvé
    
    if found_keywords:
        feedback_msg = f"✅ Mots-clés pertinents trouvés: {', '.join(found_keywords)}"
    else:
        feedback_msg = f"❌ Aucun mot-clé spécifique à {matiere} trouvé"
    
    return min(score, 25)  # Maximum 25 points

def check_structure(response: str) -> int:
    """Vérifie la structure de la réponse"""
    score = 0
    feedback = []
    
    # Présence de phrases complètes
    sentences = response.split('.')
    if len(sentences) > 2:
        score += 8
        feedback.append("✅ Réponse structurée en phrases")
    
    # Présence de paragraphes
    paragraphs = response.split('\n\n')
    if len(paragraphs) > 1:
        score += 6
        feedback.append("✅ Réponse organisée en paragraphes")
    
    # Utilisation de majuscules
    if any(c.isupper() for c in response):
        score += 3
        feedback.append("✅ Utilisation correcte des majuscules")
    
    # Ponctuation appropriée
    if any(p in response for p in ['.', '!', '?', ',']):
        score += 3
        feedback.append("✅ Ponctuation présente")
    
    return min(score, 20)

def check_effort(response: str) -> int:
    """Évalue l'effort apparent dans la réponse"""
    score = 0
    
    # Variété du vocabulaire
    words = response.lower().split()
    unique_words = set(words)
    vocabulary_ratio = len(unique_words) / len(words) if words else 0
    
    if vocabulary_ratio > 0.7:
        score += 10  # Vocabulaire varié
    elif vocabulary_ratio > 0.5:
        score += 6   # Vocabulaire correct
    else:
        score += 2   # Vocabulaire répétitif
    
    # Présence d'exemples ou d'explications
    if any(indicator in response.lower() for indicator in ['exemple', 'par exemple', 'comme', 'c\'est-à-dire', 'notamment']):
        score += 5
    
    # Effort de réflexion apparent
    if any(indicator in response.lower() for indicator in ['parce que', 'car', 'donc', 'ainsi', 'cependant', 'néanmoins']):
        score += 5
    
    return min(score, 20)

def display_evaluation(evaluation: Dict, question: str, response: str):
    """Affiche l'évaluation de manière formatée"""
    print("\n" + "📊" * 30)
    print("ÉVALUATION DE LA RÉPONSE")
    print("📊" * 30)
    
    print(f"📝 Question: {question[:100]}...")
    print(f"🎯 Score: {evaluation['score']}/{evaluation['max_score']}")
    print(f"📊 Note: {evaluation['grade']}")
    
    print("\n📋 Feedback détaillé:")
    for feedback in evaluation['feedback']:
        print(f"   {feedback}")
    
    print(f"\n📈 Détail des scores:")
    details = evaluation['details']
    print(f"   • Longueur: {details['length_score']}/20 ({details['response_length']} caractères)")
    print(f"   • Nombre de mots: {details['word_score']}/15 ({details['word_count']} mots)")
    print(f"   • Mots-clés: {details['keyword_score']}/25")
    print(f"   • Structure: {details['structure_score']}/20")
    print(f"   • Effort: {details['effort_score']}/20")
    
    print("\n💡 Recommandations:")
    if evaluation['score'] < 60:
        print("   • Développer davantage la réponse")
        print("   • Utiliser des termes techniques appropriés")
        print("   • Structurer la réponse en paragraphes")
    elif evaluation['score'] < 80:
        print("   • Ajouter plus d'exemples concrets")
        print("   • Approfondir l'explication")
    else:
        print("   • Excellente réponse, continuez ainsi!")

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
        evaluation: Dictionnaire contenant l'évaluation
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
        
        # Préparer le contenu du feedback
        student_greeting = f"Bonjour {student_name}" if student_name else "Bonjour"
        
        # Préparer le sujet en réponse à l'email original
        if original_email and original_email.get('subject'):
            original_subject = original_email['subject']
            # Supprimer les "Re: " existants pour éviter "Re: Re: ..."
            clean_subject = original_subject
            while clean_subject.startswith('Re: ') or clean_subject.startswith('RE: '):
                clean_subject = clean_subject[4:]
            subject = f"Re: {clean_subject} - 📊 Note: {evaluation['grade']} ({evaluation['score']}/100)"
        else:
            subject = f"📊 Feedback - Note: {evaluation['grade']} ({evaluation['score']}/100)"
        
        # Corps du message de feedback
        body = f"""{student_greeting},

Voici l'évaluation de votre réponse :

🎯 **RÉSULTAT GLOBAL**
• Score : {evaluation['score']}/100
• Note : {evaluation['grade']}

📝 **QUESTION POSÉE**
{question}

📄 **VOTRE RÉPONSE**
{response[:200]}{'...' if len(response) > 200 else ''}

📊 **DÉTAIL DE L'ÉVALUATION**
{format_evaluation_details(evaluation)}

📋 **FEEDBACK DÉTAILLÉ**
{format_feedback_list(evaluation['feedback'])}

💡 **RECOMMANDATIONS**
{format_recommendations(evaluation['score'])}

{format_encouragement(evaluation['grade'])}

Cordialement,
Le système d'évaluation automatique 🤖
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

def evaluate_display_and_send_feedback(question: str, response: str, matiere: str, 
                                      student_email: str, student_name: str = None, original_email: Dict = None) -> tuple:
    """
    Évalue une réponse, l'affiche et envoie le feedback par email
    
    Returns:
        tuple: (evaluation_dict, feedback_sent_success)
    """
    # Évaluer et afficher
    evaluation = evaluate_and_display(question, response, matiere)
    
    # Envoyer le feedback
    feedback_sent = send_feedback_email(student_email, evaluation, question, response, student_name, original_email)
    
    return evaluation, feedback_sent 