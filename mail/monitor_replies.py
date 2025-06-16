#!/usr/bin/env python3
"""
Script de monitoring automatique des réponses email
Lit continuellement les nouvelles réponses et envoie les feedbacks automatiquement
"""

import time
import logging
from typing import Dict, List
from email_reader import read_new_replies, display_reply, save_reply_to_conversations
from evaluator import evaluate_display_and_send_feedback
from utils import load_conversations, save_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def process_reply(reply: Dict) -> bool:
    """
    Traite une réponse : évaluation et envoi de feedback automatique
    
    Args:
        reply: Dictionnaire contenant les informations de la réponse
        
    Returns:
        bool: True si traité avec succès
    """
    try:
        question_id = reply.get('question_id')
        if not question_id:
            logger.warning("Réponse ignorée - pas d'ID de question trouvé")
            return False
        
        # Charger la conversation pour récupérer les infos de la question
        conversations = load_conversations()
        
        if question_id not in conversations:
            logger.warning(f"Question ID {question_id} non trouvée dans les conversations")
            return False
        
        conversation = conversations[question_id]
        
        # Vérifier si déjà évaluée
        if conversation.get('evaluated'):
            logger.info(f"Question {question_id} déjà évaluée, ignoring")
            return False
        
        # Extraire les données nécessaires
        question = conversation.get('question', '')
        matiere = conversation.get('matiere', 'Général')
        student_email = reply['from']
        response_text = reply['body']
        
        # Extraire les headers de threading
        original_message_id = conversation.get('sent_message_id')
        student_message_id = reply.get('message_id')
        in_reply_to = reply.get('in_reply_to')
        references = reply.get('references')
        
        logger.info(f"🔄 Traitement de la réponse {question_id} de {student_email}")
        logger.info(f"Message-ID original: {original_message_id}")
        logger.info(f"Message-ID étudiant: {student_message_id}")
        logger.info(f"In-Reply-To: {in_reply_to}")
        logger.info(f"References: {references}")
        
        # Évaluer la réponse
        evaluation = evaluate_and_display(question, response_text, matiere, conversation.get('user_id', 1))
        
        if evaluation:
            # Envoyer le feedback avec threading
            from send_questions import send_evaluation_response
            feedback_sent = send_evaluation_response(
                to=student_email,
                question_id=question_id,
                evaluation=evaluation,
                original_message_id=original_message_id,
                student_message_id=student_message_id
            )
            
            if feedback_sent:
                # Mettre à jour la conversation
                conversations[question_id].update({
                    'response': response_text,
                    'response_date': reply['date'],
                    'response_from': reply['from'],
                    'evaluated': True,
                    'evaluation': evaluation,
                    'feedback_sent': True,
                    'feedback_sent_to': student_email,
                    'student_message_id': student_message_id,
                    'student_in_reply_to': in_reply_to,
                    'student_references': references
                })
                
                save_conversations(conversations)
                logger.info(f"✅ Feedback envoyé avec succès pour {question_id}")
                return True
            else:
                logger.error(f"❌ Échec de l'envoi du feedback pour {question_id}")
                return False
        else:
            logger.error(f"❌ Échec de l'évaluation pour {question_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du traitement de la réponse: {e}")
        import traceback
        logger.error(f"Détails: {traceback.format_exc()}")
        return False

def monitor_emails(check_interval: int = 30, max_iterations: int = None):
    """
    Monitore continuellement les emails et traite automatiquement les réponses
    
    Args:
        check_interval: Intervalle entre les vérifications en secondes
        max_iterations: Nombre maximum d'itérations (None pour infini)
    """
    logger.info("🚀 Démarrage du monitoring automatique des emails")
    logger.info(f"   - Intervalle de vérification: {check_interval}s")
    logger.info(f"   - Itérations max: {max_iterations or 'Infini'}")
    
    iteration = 0
    processed_emails = set()  # Pour éviter de traiter le même email plusieurs fois
    
    try:
        while True:
            iteration += 1
            logger.info(f"🔄 Vérification #{iteration} des nouveaux emails...")
            
            try:
                # Lire les nouvelles réponses
                replies = read_new_replies()
                
                if replies:
                    logger.info(f"📧 {len(replies)} nouvelles réponses trouvées")
                    
                    for reply in replies:
                        email_id = reply.get('email_id')
                        
                        # Éviter de traiter le même email plusieurs fois
                        if email_id in processed_emails:
                            continue
                            
                        logger.info(f"📧 Nouvelle réponse de {reply['from']}")
                        
                        # Sauvegarder d'abord la réponse
                        save_reply_to_conversations(reply)
                        
                        # Traiter la réponse (évaluation + feedback)
                        success = process_reply(reply)
                        
                        if success:
                            processed_emails.add(email_id)
                            logger.info(f"✅ Réponse {email_id} traitée avec succès")
                        else:
                            logger.warning(f"⚠️ Échec du traitement de la réponse {email_id}")
                            
                else:
                    logger.info("📭 Aucune nouvelle réponse trouvée")
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors de la vérification des emails: {e}")
            
            # Vérifier la condition d'arrêt
            if max_iterations and iteration >= max_iterations:
                logger.info(f"🛑 Arrêt après {iteration} itérations")
                break
            
            # Attendre avant la prochaine vérification
            logger.info(f"⏳ Attente de {check_interval}s avant la prochaine vérification...")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt du monitoring par l'utilisateur (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Erreur fatale du monitoring: {e}")
        import traceback
        logger.error(f"Détails: {traceback.format_exc()}")
    
    logger.info("📋 Fin du monitoring automatique")

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitoring automatique des réponses email")
    parser.add_argument("--interval", "-i", type=int, default=30, 
                       help="Intervalle entre vérifications en secondes (défaut: 30)")
    parser.add_argument("--max-iterations", "-n", type=int, default=None,
                       help="Nombre maximum d'itérations (défaut: infini)")
    parser.add_argument("--test", "-t", action="store_true",
                       help="Mode test: une seule vérification puis arrêt")
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Mode test: une seule vérification")
        monitor_emails(check_interval=1, max_iterations=1)
    else:
        monitor_emails(check_interval=args.interval, max_iterations=args.max_iterations)

if __name__ == "__main__":
    main() 