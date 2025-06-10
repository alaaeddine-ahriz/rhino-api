#!/usr/bin/env python3
"""
Exemple d'utilisation du système de mail automatisé
"""

import logging
from mail_system import (
    send_question_to_student,
    send_questions_to_multiple_students,
    process_replies,
    evaluate_all_responses,
    run_full_workflow,
    monitor_mode
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_send_single_question():
    """Exemple : Envoyer une question à un étudiant"""
    print("\n=== EXEMPLE 1: Envoi d'une question ===")
    
    # Envoyer un challenge personnalisé pour un utilisateur
    success = send_question_to_student(
        email="mathis.beaufour71@gmail.com",
        user_id=1
    )
    
    if success:
        print("✅ Question envoyée avec succès!")
    else:
        print("❌ Échec de l'envoi")

def example_send_multiple_questions():
    """Exemple : Envoyer des questions à plusieurs étudiants"""
    print("\n=== EXEMPLE 2: Envoi groupé ===")
    
    students = [
        {
            "email": "student1@example.com",
            "user_id": 1
        },
        {
            "email": "student2@example.com",
            "matiere": "informatique"
        },
        {
            "email": "student3@example.com",
            "user_id": 3
        }
    ]
    
    results = send_questions_to_multiple_students(students)
    
    print("📊 Résultats:")
    for email, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {email}")

def example_process_workflow():
    """Exemple : Workflow complet"""
    print("\n=== EXEMPLE 3: Workflow complet ===")
    
    # Définir les étudiants pour l'envoi (optionnel)
    students = [
        {"email": "mathis.beaufour71@gmail.com", "user_id": 1}
    ]
    
    # Exécuter le workflow complet
    run_full_workflow(students)

def example_monitoring():
    """Exemple : Mode surveillance"""
    print("\n=== EXEMPLE 4: Mode surveillance ===")
    print("⚠️  Mode surveillance activé - Appuyez sur Ctrl+C pour arrêter")
    
    try:
        # Surveillance toutes les 60 secondes (pour test)
        monitor_mode(interval=60)
    except KeyboardInterrupt:
        print("\n🛑 Surveillance arrêtée")

def example_manual_processing():
    """Exemple : Traitement manuel étape par étape"""
    print("\n=== EXEMPLE 5: Traitement manuel ===")
    
    # 1. Traiter les réponses
    print("📥 Traitement des réponses...")
    new_replies = process_replies()
    print(f"📨 {new_replies} nouvelles réponses traitées")
    
    # 2. Évaluer les réponses
    print("🤖 Évaluation des réponses...")
    evaluated = evaluate_all_responses()
    print(f"✅ {evaluated} réponses évaluées")

def main():
    """Menu principal d'exemples"""
    print("🚀 EXEMPLES D'UTILISATION DU SYSTÈME DE MAIL")
    print("=" * 50)
    
    examples = {
        "1": ("Envoyer une question", example_send_single_question),
        "2": ("Envoi groupé", example_send_multiple_questions),
        "3": ("Workflow complet", example_process_workflow),
        "4": ("Mode surveillance", example_monitoring),
        "5": ("Traitement manuel", example_manual_processing)
    }
    
    print("Choisissez un exemple:")
    for key, (description, _) in examples.items():
        print(f"  {key}. {description}")
    
    choice = input("\nVotre choix (1-5): ").strip()
    
    if choice in examples:
        _, example_func = examples[choice]
        try:
            example_func()
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution: {e}")
    else:
        print("❌ Choix invalide")

if __name__ == "__main__":
    main() 