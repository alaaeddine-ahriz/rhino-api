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