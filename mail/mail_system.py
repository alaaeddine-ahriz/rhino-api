#!/usr/bin/env python3
"""
Système de gestion des emails automatisé
Orchestrateur principal pour l'envoi de questions et l'évaluation des réponses
"""

import time
import logging
import argparse
from typing import List, Dict, Any
from send_questions import (
    send_daily_challenge_to_user, 
    send_subject_challenge, 
    test_api_connection
)
from read_replies import read_replies, get_unread_count
from evaluate_responses import evaluate_pending_responses, print_evaluation_report
from utils import load_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def send_question_to_student(email: str, user_id: int = None, matiere: str = None) -> bool:
    """
    Envoie une question à un étudiant
    
    Args:
        email: Email de l'étudiant
        user_id: ID de l'utilisateur (pour challenge personnalisé)
        matiere: Matière spécifique (optionnel)
    
    Returns:
        bool: True si envoyé avec succès
    """
    logger.info(f"📤 Envoi d'une question à {email}")
    
    if user_id:
        success = send_daily_challenge_to_user(email, user_id)
    elif matiere:
        success = send_subject_challenge(email, matiere)
    else:
        logger.error("❌ user_id ou matiere doit être spécifié")
        return False
    
    if success:
        logger.info(f"✅ Question envoyée avec succès à {email}")
    else:
        logger.error(f"❌ Échec de l'envoi à {email}")
    
    return success

def send_questions_to_multiple_students(students: List[Dict[str, Any]]) -> Dict[str, bool]:
    """
    Envoie des questions à plusieurs étudiants
    
    Args:
        students: Liste de dictionnaires avec 'email', 'user_id' (optionnel), 'matiere' (optionnel)
    
    Returns:
        Dict avec l'email comme clé et le résultat (bool) comme valeur
    """
    results = {}
    
    logger.info(f"📤 Envoi de questions à {len(students)} étudiant(s)")
    
    for student in students:
        email = student.get('email')
        user_id = student.get('user_id')
        matiere = student.get('matiere')
        
        if not email:
            logger.warning("⚠️ Email manquant pour un étudiant")
            continue
        
        result = send_question_to_student(email, user_id, matiere)
        results[email] = result
        
        # Pause entre les envois pour éviter le spam
        time.sleep(1)
    
    # Résumé des envois
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful
    
    logger.info(f"📊 Résumé des envois: {successful} succès, {failed} échecs")
    
    return results

def process_replies() -> int:
    """
    Traite les réponses reçues
    
    Returns:
        Nombre de nouvelles réponses traitées
    """
    logger.info("📥 Vérification des nouvelles réponses...")
    
    # Vérifier le nombre de messages non lus
    unread_count = get_unread_count()
    logger.info(f"📨 {unread_count} message(s) non lu(s) trouvé(s)")
    
    if unread_count == 0:
        logger.info("ℹ️ Aucune nouvelle réponse à traiter")
        return 0
    
    # Lire les réponses
    read_replies()
    
    return unread_count

def evaluate_all_responses() -> int:
    """
    Évalue toutes les réponses en attente
    
    Returns:
        Nombre de réponses évaluées
    """
    logger.info("🤖 Évaluation des réponses en attente...")
    
    count = evaluate_pending_responses()
    
    if count > 0:
        logger.info(f"✅ {count} réponse(s) évaluée(s)")
    else:
        logger.info("ℹ️ Aucune réponse en attente d'évaluation")
    
    return count

def run_full_workflow(students: List[Dict[str, Any]] = None) -> None:
    """
    Execute le workflow complet: envoi -> réception -> évaluation
    
    Args:
        students: Liste optionnelle d'étudiants pour envoi groupé
    """
    logger.info("🚀 Démarrage du workflow complet")
    
    # 1. Vérifier la connexion API
    if not test_api_connection():
        logger.error("❌ Impossible de se connecter à l'API. Arrêt du workflow.")
        return
    
    # 2. Envoyer des questions (si spécifié)
    if students:
        logger.info("📤 Phase 1: Envoi des questions")
        send_questions_to_multiple_students(students)
    else:
        logger.info("ℹ️ Aucun envoi de question programmé")
    
    # 3. Traiter les réponses
    logger.info("📥 Phase 2: Traitement des réponses")
    new_replies = process_replies()
    
    # 4. Évaluer les réponses
    logger.info("🤖 Phase 3: Évaluation des réponses")
    evaluated = evaluate_all_responses()
    
    # 5. Afficher le rapport
    logger.info("📊 Phase 4: Génération du rapport")
    print_evaluation_report()
    
    logger.info(f"✅ Workflow terminé: {new_replies} nouvelles réponses, {evaluated} évaluations")

def monitor_mode(interval: int = 300) -> None:
    """
    Mode surveillance: vérifie périodiquement les nouvelles réponses
    
    Args:
        interval: Intervalle en secondes entre les vérifications (défaut: 5 minutes)
    """
    logger.info(f"👁️ Mode surveillance activé (intervalle: {interval}s)")
    
    try:
        while True:
            logger.info("🔄 Vérification périodique...")
            
            # Traiter les réponses
            new_replies = process_replies()
            
            # Évaluer les réponses
            if new_replies > 0:
                evaluated = evaluate_all_responses()
                logger.info(f"📊 Traitement: {new_replies} réponses, {evaluated} évaluations")
            
            # Attendre avant la prochaine vérification
            logger.info(f"⏰ Prochaine vérification dans {interval} secondes")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("🛑 Mode surveillance arrêté par l'utilisateur")

def main():
    """Fonction principale avec interface en ligne de commande"""
    parser = argparse.ArgumentParser(description="Système de gestion des emails automatisé")
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Commande send
    send_parser = subparsers.add_parser('send', help='Envoyer une question')
    send_parser.add_argument('--email', required=True, help='Email de l\'étudiant')
    send_parser.add_argument('--user-id', type=int, help='ID de l\'utilisateur')
    send_parser.add_argument('--matiere', help='Matière spécifique')
    
    # Commande read
    read_parser = subparsers.add_parser('read', help='Lire les réponses')
    
    # Commande evaluate
    eval_parser = subparsers.add_parser('evaluate', help='Évaluer les réponses')
    
    # Commande report
    report_parser = subparsers.add_parser('report', help='Afficher le rapport')
    
    # Commande workflow
    workflow_parser = subparsers.add_parser('workflow', help='Exécuter le workflow complet')
    
    # Commande monitor
    monitor_parser = subparsers.add_parser('monitor', help='Mode surveillance')
    monitor_parser.add_argument('--interval', type=int, default=300, help='Intervalle en secondes (défaut: 300)')
    
    args = parser.parse_args()
    
    if args.command == 'send':
        send_question_to_student(args.email, args.user_id, args.matiere)
    
    elif args.command == 'read':
        process_replies()
    
    elif args.command == 'evaluate':
        evaluate_all_responses()
    
    elif args.command == 'report':
        print_evaluation_report()
    
    elif args.command == 'workflow':
        run_full_workflow()
    
    elif args.command == 'monitor':
        monitor_mode(args.interval)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 