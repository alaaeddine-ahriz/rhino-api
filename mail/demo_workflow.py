#!/usr/bin/env python3
"""
Script de démonstration du workflow complet du système de mail
Ce script montre comment utiliser toutes les fonctionnalités ensemble
"""

import logging
import time
from database_utils import get_student_by_id, get_all_students, print_database_info
from send_questions import send_question_from_api, test_api_connection
from read_replies import read_replies, get_unread_count
from evaluate_responses import evaluate_pending_responses, print_evaluation_report
from send_evaluation import send_evaluations_for_pending_responses, print_evaluation_send_report

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def demo_database_integration():
    """Démontre l'intégration avec la base de données"""
    print("\n" + "="*60)
    print("🗄️  DÉMONSTRATION: INTÉGRATION BASE DE DONNÉES")
    print("="*60)
    
    # Afficher les informations de la base
    print_database_info()
    
    # Récupérer tous les étudiants
    students = get_all_students()
    print(f"\n👥 Étudiants trouvés dans la base: {len(students)}")
    
    for i, student in enumerate(students[:3], 1):  # Afficher les 3 premiers
        print(f"   {i}. {student['username']} ({student['email']}) - ID: {student['id']}")
        print(f"      📚 Abonnements: {', '.join(student['subscriptions'])}")
    
    if len(students) > 3:
        print(f"   ... et {len(students) - 3} autre(s) étudiant(s)")
    
    return students

def demo_send_question_by_id(user_id: int):
    """Démontre l'envoi d'une question en utilisant l'ID étudiant"""
    print("\n" + "="*60)
    print(f"📤 DÉMONSTRATION: ENVOI DE QUESTION À L'ÉTUDIANT ID {user_id}")
    print("="*60)
    
    # Récupérer les informations de l'étudiant
    student = get_student_by_id(user_id)
    if not student:
        print(f"❌ Étudiant avec ID {user_id} non trouvé")
        return False
    
    print(f"👤 Étudiant sélectionné: {student['username']}")
    print(f"📧 Email: {student['email']}")
    print(f"📚 Abonnements: {', '.join(student['subscriptions'])}")
    
    # Vérifier la connexion API
    if not test_api_connection():
        print("❌ Impossible de se connecter à l'API")
        return False
    
    print("✅ Connexion API vérifiée")
    
    # Envoyer la question
    print(f"\n📤 Envoi de la question à {student['email']}...")
    success = send_question_from_api(
        to=student['email'],
        user_id=user_id
    )
    
    if success:
        print(f"✅ Question envoyée avec succès à {student['username']}")
        return True
    else:
        print(f"❌ Échec de l'envoi à {student['username']}")
        return False

def demo_process_responses():
    """Démontre le traitement des réponses"""
    print("\n" + "="*60)
    print("📥 DÉMONSTRATION: TRAITEMENT DES RÉPONSES")
    print("="*60)
    
    # Vérifier les messages non lus
    unread_count = get_unread_count()
    print(f"📨 Messages non lus trouvés: {unread_count}")
    
    if unread_count > 0:
        print("📥 Lecture des nouvelles réponses...")
        read_replies()
        print("✅ Réponses traitées")
    else:
        print("ℹ️ Aucune nouvelle réponse à traiter")
    
    return unread_count

def demo_evaluate_responses():
    """Démontre l'évaluation des réponses"""
    print("\n" + "="*60)
    print("🤖 DÉMONSTRATION: ÉVALUATION AUTOMATIQUE")
    print("="*60)
    
    # Évaluer les réponses en attente
    evaluated_count = evaluate_pending_responses()
    
    if evaluated_count > 0:
        print(f"✅ {evaluated_count} réponse(s) évaluée(s) avec succès")
        
        # Afficher le rapport d'évaluation
        print_evaluation_report()
    else:
        print("ℹ️ Aucune réponse en attente d'évaluation")
    
    return evaluated_count

def demo_send_evaluation_results():
    """Démontre l'envoi des résultats d'évaluation"""
    print("\n" + "="*60)
    print("📧 DÉMONSTRATION: ENVOI DES RÉSULTATS")
    print("="*60)
    
    # Envoyer les évaluations en attente
    sent_count = send_evaluations_for_pending_responses()
    
    if sent_count > 0:
        print(f"✅ {sent_count} évaluation(s) envoyée(s) aux étudiants")
        
        # Afficher le rapport d'envoi
        print_evaluation_send_report()
    else:
        print("ℹ️ Aucune évaluation en attente d'envoi")
    
    return sent_count

def demo_complete_workflow():
    """Démontre le workflow complet"""
    print("\n" + "🚀" * 30)
    print("DÉMONSTRATION COMPLÈTE DU WORKFLOW EMAIL")
    print("🚀" * 30)
    
    # 1. Intégration base de données
    students = demo_database_integration()
    
    if not students:
        print("❌ Aucun étudiant trouvé. Impossible de continuer la démonstration.")
        return
    
    # Sélectionner le premier étudiant pour la démonstration
    demo_student_id = students[0]['id']
    
    # 2. Envoi de question
    question_sent = demo_send_question_by_id(demo_student_id)
    
    if not question_sent:
        print("❌ Impossible d'envoyer la question. Fin de la démonstration.")
        return
    
    # 3. Simulation d'attente de réponse
    print("\n⏳ En production, le système attendrait les réponses des étudiants...")
    print("   Pour cette démonstration, nous vérifions les réponses existantes.")
    time.sleep(2)
    
    # 4. Traitement des réponses
    responses_processed = demo_process_responses()
    
    # 5. Évaluation des réponses
    responses_evaluated = demo_evaluate_responses()
    
    # 6. Envoi des résultats
    evaluations_sent = demo_send_evaluation_results()
    
    # 7. Résumé final
    print("\n" + "🏁" * 30)
    print("RÉSUMÉ DE LA DÉMONSTRATION")
    print("🏁" * 30)
    print(f"📤 Question envoyée: {'✅' if question_sent else '❌'}")
    print(f"📥 Réponses traitées: {responses_processed}")
    print(f"🤖 Réponses évaluées: {responses_evaluated}")
    print(f"📧 Évaluations envoyées: {evaluations_sent}")
    
    if question_sent and (responses_evaluated > 0 or evaluations_sent > 0):
        print("\n🎉 Démonstration réussie! Le workflow complet fonctionne.")
    else:
        print("\n💡 Démonstration partielle. Pour tester complètement:")
        print("   1. Répondez aux emails de questions envoyés")
        print("   2. Relancez le script pour voir l'évaluation automatique")
    
    print("\n📚 Pour plus d'options, utilisez:")
    print("   python test_complete_workflow.py --help")

def demo_interactive():
    """Mode interactif pour choisir les démonstrations"""
    print("🎯 DÉMONSTRATIONS DISPONIBLES")
    print("="*40)
    print("1. Intégration base de données")
    print("2. Envoi de question par ID")
    print("3. Traitement des réponses")
    print("4. Évaluation automatique")
    print("5. Envoi des résultats")
    print("6. Workflow complet")
    print("0. Quitter")
    
    while True:
        try:
            choice = input("\nChoisissez une démonstration (0-6): ").strip()
            
            if choice == '0':
                print("👋 Au revoir!")
                break
            elif choice == '1':
                demo_database_integration()
            elif choice == '2':
                students = get_all_students()
                if students:
                    user_id = students[0]['id']
                    demo_send_question_by_id(user_id)
                else:
                    print("❌ Aucun étudiant trouvé")
            elif choice == '3':
                demo_process_responses()
            elif choice == '4':
                demo_evaluate_responses()
            elif choice == '5':
                demo_send_evaluation_results()
            elif choice == '6':
                demo_complete_workflow()
            else:
                print("❌ Choix invalide")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

def main():
    """Fonction principale"""
    import sys
    
    print("🔍 DÉMONSTRATION DU SYSTÈME DE MAIL AUTOMATISÉ")
    print("="*50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        demo_interactive()
    else:
        demo_complete_workflow()

if __name__ == "__main__":
    main() 