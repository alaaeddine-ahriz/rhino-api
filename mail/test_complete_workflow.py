#!/usr/bin/env python3
"""
Script de test complet pour le système de mail automatisé
Workflow: envoi -> réponse -> évaluation -> envoi résultat
"""

import time
import logging
import argparse
from typing import List, Dict, Any, Optional
from database_utils import get_student_by_id, get_all_students, print_database_info
from send_questions import send_question_from_api, test_api_connection
from read_replies import read_replies, get_unread_count
from evaluate_responses import evaluate_pending_responses, print_evaluation_report
from send_evaluation import send_evaluations_for_pending_responses, print_evaluation_send_report
from utils import load_conversations, save_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class EmailWorkflowTester:
    """Classe pour tester le workflow complet du système d'email"""
    
    def __init__(self):
        self.conversations_at_start = {}
        self.test_session_id = int(time.time())
        
    def setup_test_environment(self):
        """Prépare l'environnement de test"""
        logger.info("🔧 Configuration de l'environnement de test...")
        
        # Sauvegarder l'état initial des conversations
        self.conversations_at_start = load_conversations().copy()
        
        # Vérifier la connexion API
        if not test_api_connection():
            logger.error("❌ Impossible de se connecter à l'API")
            return False
        
        logger.info("✅ Environnement de test configuré")
        return True
    
    def send_question_to_student_by_id(self, user_id: int) -> bool:
        """
        Envoie une question à un étudiant en récupérant son email depuis la base
        
        Args:
            user_id: ID de l'étudiant
        
        Returns:
            bool: True si succès
        """
        logger.info(f"📤 Envoi d'une question à l'étudiant ID {user_id}")
        
        # Récupérer les informations de l'étudiant
        student = get_student_by_id(user_id)
        if not student:
            logger.error(f"❌ Étudiant avec ID {user_id} non trouvé dans la base")
            return False
        
        email = student.get("email")
        if not email:
            logger.error(f"❌ Email manquant pour l'étudiant {student.get('username')}")
            return False
        
        logger.info(f"👤 Étudiant trouvé: {student['username']} ({email})")
        logger.info(f"📚 Abonnements: {', '.join(student['subscriptions'])}")
        
        # Envoyer la question
        success = send_question_from_api(
            to=email,
            user_id=user_id
        )
        
        if success:
            logger.info(f"✅ Question envoyée avec succès à {student['username']}")
        else:
            logger.error(f"❌ Échec de l'envoi à {student['username']}")
        
        return success
    
    def wait_for_responses(self, timeout_minutes: int = 5) -> int:
        """
        Attend les réponses des étudiants (en mode test, on peut simuler)
        
        Args:
            timeout_minutes: Délai d'attente maximum en minutes
        
        Returns:
            int: Nombre de nouvelles réponses reçues
        """
        logger.info(f"⏳ Attente de réponses (max {timeout_minutes} min)...")
        
        start_time = time.time()
        total_new_responses = 0
        
        while time.time() - start_time < timeout_minutes * 60:
            # Vérifier les nouvelles réponses
            unread_count = get_unread_count()
            
            if unread_count > 0:
                logger.info(f"📨 {unread_count} nouveau(x) message(s) détecté(s)")
                new_responses = self.process_new_responses()
                total_new_responses += new_responses
                
                if new_responses > 0:
                    logger.info(f"📥 {new_responses} réponse(s) traitée(s)")
                    break
            
            # Attendre 30 secondes avant de vérifier à nouveau
            time.sleep(30)
        
        if total_new_responses == 0:
            logger.info("ℹ️ Aucune nouvelle réponse reçue dans le délai imparti")
        
        return total_new_responses
    
    def process_new_responses(self) -> int:
        """
        Traite les nouvelles réponses reçues
        
        Returns:
            int: Nombre de réponses traitées
        """
        logger.info("📥 Traitement des nouvelles réponses...")
        
        try:
            # Lire les réponses
            read_replies()
            
            # Compter les nouvelles réponses
            conversations = load_conversations()
            new_responses = 0
            
            for conv in conversations.values():
                if conv.get("response") and not conv.get("evaluated"):
                    new_responses += 1
            
            logger.info(f"📊 {new_responses} nouvelle(s) réponse(s) non évaluée(s)")
            return new_responses
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement des réponses: {e}")
            return 0
    
    def evaluate_all_responses(self) -> int:
        """
        Évalue toutes les réponses en attente
        
        Returns:
            int: Nombre de réponses évaluées
        """
        logger.info("🤖 Évaluation des réponses en attente...")
        
        try:
            evaluated_count = evaluate_pending_responses()
            
            if evaluated_count > 0:
                logger.info(f"✅ {evaluated_count} réponse(s) évaluée(s)")
            else:
                logger.info("ℹ️ Aucune réponse en attente d'évaluation")
            
            return evaluated_count
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'évaluation: {e}")
            return 0
    
    def send_evaluation_results(self) -> int:
        """
        Envoie les résultats d'évaluation aux étudiants
        
        Returns:
            int: Nombre d'évaluations envoyées
        """
        logger.info("📧 Envoi des résultats d'évaluation...")
        
        try:
            sent_count = send_evaluations_for_pending_responses()
            
            if sent_count > 0:
                logger.info(f"✅ {sent_count} évaluation(s) envoyée(s)")
            else:
                logger.info("ℹ️ Aucune évaluation en attente d'envoi")
            
            return sent_count
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi des évaluations: {e}")
            return 0
    
    def run_complete_workflow(self, user_id: int, wait_for_response: bool = True) -> Dict[str, Any]:
        """
        Execute le workflow complet pour un étudiant
        
        Args:
            user_id: ID de l'étudiant
            wait_for_response: Si True, attend les réponses
        
        Returns:
            Dict avec les résultats du workflow
        """
        logger.info(f"🚀 Démarrage du workflow complet pour l'étudiant ID {user_id}")
        
        results = {
            "user_id": user_id,
            "question_sent": False,
            "responses_received": 0,
            "responses_evaluated": 0,
            "evaluations_sent": 0,
            "success": False
        }
        
        # 1. Envoyer la question
        logger.info("📤 Phase 1: Envoi de la question")
        results["question_sent"] = self.send_question_to_student_by_id(user_id)
        
        if not results["question_sent"]:
            logger.error("❌ Échec de l'envoi de la question. Arrêt du workflow.")
            return results
        
        # 2. Attendre et traiter les réponses (si demandé)
        if wait_for_response:
            logger.info("📥 Phase 2: Attente et traitement des réponses")
            results["responses_received"] = self.wait_for_responses(timeout_minutes=10)
        else:
            logger.info("📥 Phase 2: Traitement des réponses existantes")
            results["responses_received"] = self.process_new_responses()
        
        # 3. Évaluer les réponses
        logger.info("🤖 Phase 3: Évaluation des réponses")
        results["responses_evaluated"] = self.evaluate_all_responses()
        
        # 4. Envoyer les évaluations
        logger.info("📧 Phase 4: Envoi des évaluations")
        results["evaluations_sent"] = self.send_evaluation_results()
        
        # 5. Déterminer le succès
        results["success"] = (
            results["question_sent"] and 
            (results["responses_received"] > 0 or not wait_for_response) and
            results["responses_evaluated"] > 0 and
            results["evaluations_sent"] > 0
        )
        
        logger.info(f"✅ Workflow terminé - Succès: {results['success']}")
        return results
    
    def run_batch_workflow(self, user_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Execute le workflow pour plusieurs étudiants
        
        Args:
            user_ids: Liste des IDs d'étudiants
        
        Returns:
            Liste des résultats pour chaque étudiant
        """
        logger.info(f"🚀 Démarrage du workflow batch pour {len(user_ids)} étudiant(s)")
        
        results = []
        
        for user_id in user_ids:
            logger.info(f"\n{'='*60}")
            logger.info(f"📋 Traitement de l'étudiant ID {user_id}")
            logger.info(f"{'='*60}")
            
            result = self.run_complete_workflow(user_id, wait_for_response=False)
            results.append(result)
            
            # Pause entre les étudiants
            time.sleep(2)
        
        # Résumé des résultats
        self.print_batch_summary(results)
        
        return results
    
    def print_batch_summary(self, results: List[Dict[str, Any]]):
        """Affiche un résumé des résultats batch"""
        logger.info("\n" + "="*60)
        logger.info("📊 RÉSUMÉ DU WORKFLOW BATCH")
        logger.info("="*60)
        
        total_students = len(results)
        questions_sent = sum(1 for r in results if r["question_sent"])
        responses_received = sum(r["responses_received"] for r in results)
        responses_evaluated = sum(r["responses_evaluated"] for r in results)
        evaluations_sent = sum(r["evaluations_sent"] for r in results)
        successful_workflows = sum(1 for r in results if r["success"])
        
        logger.info(f"👥 Total étudiants: {total_students}")
        logger.info(f"📤 Questions envoyées: {questions_sent}/{total_students}")
        logger.info(f"📥 Réponses reçues: {responses_received}")
        logger.info(f"🤖 Réponses évaluées: {responses_evaluated}")
        logger.info(f"📧 Évaluations envoyées: {evaluations_sent}")
        logger.info(f"✅ Workflows réussis: {successful_workflows}/{total_students}")
        
        success_rate = round(successful_workflows / total_students * 100, 2) if total_students > 0 else 0
        logger.info(f"📊 Taux de succès: {success_rate}%")
        
        logger.info("="*60)
    
    def generate_final_report(self):
        """Génère un rapport final complet"""
        logger.info("\n" + "🔍" * 30)
        logger.info("RAPPORT FINAL COMPLET")
        logger.info("🔍" * 30)
        
        # Informations base de données
        print_database_info()
        
        # Rapport d'évaluation
        print_evaluation_report()
        
        # Rapport d'envoi des évaluations
        print_evaluation_send_report()

def main():
    """Fonction principale avec interface CLI"""
    parser = argparse.ArgumentParser(description="Test du workflow complet du système de mail")
    
    subparsers = parser.add_subparsers(dest='command', help='Commandes disponibles')
    
    # Test simple
    simple_parser = subparsers.add_parser('simple', help='Test simple avec un étudiant')
    simple_parser.add_argument('--user-id', type=int, required=True, help='ID de l\'étudiant')
    simple_parser.add_argument('--no-wait', action='store_true', help='Ne pas attendre de réponse')
    
    # Test batch
    batch_parser = subparsers.add_parser('batch', help='Test batch avec plusieurs étudiants')
    batch_parser.add_argument('--user-ids', nargs='+', type=int, help='IDs des étudiants')
    batch_parser.add_argument('--all-students', action='store_true', help='Tester tous les étudiants')
    
    # Monitoring
    monitor_parser = subparsers.add_parser('monitor', help='Mode surveillance')
    monitor_parser.add_argument('--interval', type=int, default=60, help='Intervalle en secondes')
    
    # Rapport
    report_parser = subparsers.add_parser('report', help='Générer un rapport')
    
    args = parser.parse_args()
    
    # Créer le testeur
    tester = EmailWorkflowTester()
    
    # Configuration de l'environnement
    if not tester.setup_test_environment():
        logger.error("❌ Impossible de configurer l'environnement de test")
        return
    
    if args.command == 'simple':
        # Test simple
        wait_response = not args.no_wait
        result = tester.run_complete_workflow(args.user_id, wait_for_response=wait_response)
        
        if result["success"]:
            logger.info("🎉 Test réussi!")
        else:
            logger.error("💥 Test échoué")
    
    elif args.command == 'batch':
        # Test batch
        if args.all_students:
            students = get_all_students()
            user_ids = [s["id"] for s in students]
            logger.info(f"📋 Test avec tous les étudiants: {len(user_ids)} trouvés")
        elif args.user_ids:
            user_ids = args.user_ids
        else:
            logger.error("❌ Spécifiez --user-ids ou --all-students")
            return
        
        results = tester.run_batch_workflow(user_ids)
        
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        logger.info(f"🎯 Résultat final: {successful}/{total} workflows réussis")
    
    elif args.command == 'monitor':
        # Mode surveillance
        logger.info(f"👁️ Mode surveillance activé (intervalle: {args.interval}s)")
        
        try:
            while True:
                logger.info("🔄 Vérification périodique...")
                
                # Traiter les réponses
                responses = tester.process_new_responses()
                if responses > 0:
                    # Évaluer et envoyer
                    evaluated = tester.evaluate_all_responses()
                    sent = tester.send_evaluation_results()
                    logger.info(f"📊 Traité: {responses} réponses, {evaluated} évaluations, {sent} envois")
                
                time.sleep(args.interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Surveillance arrêtée")
    
    elif args.command == 'report':
        # Générer un rapport
        tester.generate_final_report()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 