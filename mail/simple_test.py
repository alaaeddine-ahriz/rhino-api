#!/usr/bin/env python3
"""
Test simple du système de mail sans API
Démontre l'intégration base de données et la structure du workflow
"""

import logging
from database_utils import get_student_by_id, get_all_students, print_database_info
from utils import load_conversations, save_conversations

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_database_integration():
    """Test de l'intégration avec la base de données"""
    print("\n" + "="*60)
    print("🗄️  TEST: INTÉGRATION BASE DE DONNÉES")
    print("="*60)
    
    # Afficher les statistiques
    print_database_info()
    
    # Récupérer tous les étudiants
    students = get_all_students()
    print(f"\n👥 Étudiants disponibles: {len(students)}")
    
    for student in students:
        print(f"   - {student['username']} (ID: {student['id']})")
        print(f"     📧 Email: {student['email']}")
        print(f"     📚 Abonnements: {', '.join(student['subscriptions'])}")
    
    return students

def test_student_retrieval():
    """Test de récupération d'un étudiant spécifique"""
    print("\n" + "="*60)
    print("👤 TEST: RÉCUPÉRATION ÉTUDIANT")
    print("="*60)
    
    # Tester avec l'ID 2
    student = get_student_by_id(2)
    
    if student:
        print(f"✅ Étudiant trouvé:")
        print(f"   - Nom: {student['username']}")
        print(f"   - Email: {student['email']}")
        print(f"   - Rôle: {student['role']}")
        print(f"   - Abonnements: {', '.join(student['subscriptions'])}")
        
        return student
    else:
        print("❌ Aucun étudiant trouvé avec l'ID 2")
        return None

def test_workflow_simulation():
    """Simulation du workflow sans API"""
    print("\n" + "="*60)
    print("🚀 TEST: SIMULATION WORKFLOW")
    print("="*60)
    
    # Récupérer un étudiant
    student = get_student_by_id(2)
    if not student:
        print("❌ Impossible de continuer sans étudiant")
        return
    
    print(f"1. ✅ Étudiant sélectionné: {student['username']} ({student['email']})")
    
    # Simuler l'envoi d'une question
    print("2. 📤 [SIMULATION] Envoi de question...")
    print(f"   Destinataire: {student['email']}")
    print(f"   Matière: {student['subscriptions'][0] if student['subscriptions'] else 'SYD'}")
    
    # Simuler une réponse
    print("3. 📥 [SIMULATION] Réception de réponse...")
    simulated_response = "TCP est un protocole fiable avec contrôle de flux, contrairement à UDP qui est plus rapide mais sans garantie."
    print(f"   Réponse simulée: {simulated_response[:50]}...")
    
    # Simuler l'évaluation
    print("4. 🤖 [SIMULATION] Évaluation automatique...")
    simulated_evaluation = {
        "score": 85,
        "note": 17,
        "feedback": "Bonne compréhension des concepts fondamentaux",
        "points_forts": ["Distinction claire TCP/UDP", "Concepts de fiabilité"],
        "points_ameliorer": ["Détailler le contrôle de flux"],
        "matiere": student['subscriptions'][0] if student['subscriptions'] else 'SYD'
    }
    print(f"   Note: {simulated_evaluation['note']}/20")
    print(f"   Score: {simulated_evaluation['score']}%")
    
    # Simuler l'envoi du résultat
    print("5. 📧 [SIMULATION] Envoi du résultat...")
    print(f"   Destinataire: {student['email']}")
    print(f"   Sujet: 🎓 Évaluation de votre réponse - {simulated_evaluation['note']}/20")
    
    print("\n🎉 Workflow simulé avec succès!")
    return True

def test_conversations_management():
    """Test de gestion des conversations"""
    print("\n" + "="*60)
    print("💬 TEST: GESTION DES CONVERSATIONS")
    print("="*60)
    
    # Charger les conversations existantes
    conversations = load_conversations()
    print(f"📂 Conversations existantes: {len(conversations)}")
    
    for q_id, conv in conversations.items():
        print(f"   - {q_id}:")
        print(f"     👤 Étudiant: {conv.get('student', 'N/A')}")
        print(f"     ❓ Question: {conv.get('question', 'N/A')[:50]}...")
        print(f"     📝 Réponse: {'✅' if conv.get('response') else '❌'}")
        print(f"     🤖 Évaluée: {'✅' if conv.get('evaluated') else '❌'}")
        print(f"     📧 Envoyée: {'✅' if conv.get('evaluation_sent') else '❌'}")
    
    return conversations

def test_email_format():
    """Test du formatage des emails"""
    print("\n" + "="*60)
    print("📧 TEST: FORMATAGE EMAIL")
    print("="*60)
    
    # Import local pour éviter les erreurs si les modules ne sont pas disponibles
    try:
        from send_evaluation import format_evaluation_email
        
        # Créer une évaluation de test
        test_evaluation = {
            "score": 85,
            "note": 17,
            "feedback": "Excellente compréhension des concepts de base.",
            "points_forts": ["Clarté de l'expression", "Utilisation d'exemples pertinents"],
            "points_ameliorer": ["Approfondir l'analyse", "Ajouter des références"],
            "justification_note": "La réponse démontre une bonne maîtrise du sujet.",
            "suggestions": ["Lire le chapitre 5", "Pratiquer avec des exercices supplémentaires"],
            "matiere": "SYD"
        }
        
        # Formater l'email
        email_content = format_evaluation_email(test_evaluation, "Test Student")
        
        print("✅ Email formaté avec succès:")
        print("📧 Aperçu du contenu:")
        lines = email_content.split('\n')
        for i, line in enumerate(lines[:10]):  # Afficher les 10 premières lignes
            print(f"   {line}")
        
        if len(lines) > 10:
            print("   ...")
            print(f"   [Total: {len(lines)} lignes]")
        
        return True
        
    except ImportError as e:
        print(f"⚠️ Impossible de tester le formatage: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 TESTS DU SYSTÈME DE MAIL AUTOMATISÉ")
    print("="*60)
    print("ℹ️  Ces tests fonctionnent sans API active")
    print("="*60)
    
    # Tests
    results = {}
    
    # 1. Test base de données
    try:
        students = test_database_integration()
        results["database"] = len(students) > 0
    except Exception as e:
        print(f"❌ Erreur test database: {e}")
        results["database"] = False
    
    # 2. Test récupération étudiant
    try:
        student = test_student_retrieval()
        results["student_retrieval"] = student is not None
    except Exception as e:
        print(f"❌ Erreur test student: {e}")
        results["student_retrieval"] = False
    
    # 3. Test workflow simulé
    try:
        workflow_ok = test_workflow_simulation()
        results["workflow_simulation"] = workflow_ok
    except Exception as e:
        print(f"❌ Erreur test workflow: {e}")
        results["workflow_simulation"] = False
    
    # 4. Test conversations
    try:
        conversations = test_conversations_management()
        results["conversations"] = True
    except Exception as e:
        print(f"❌ Erreur test conversations: {e}")
        results["conversations"] = False
    
    # 5. Test formatage email
    try:
        email_ok = test_email_format()
        results["email_format"] = email_ok
    except Exception as e:
        print(f"❌ Erreur test email: {e}")
        results["email_format"] = False
    
    # Résumé des tests
    print("\n" + "🏁" * 30)
    print("RÉSUMÉ DES TESTS")
    print("🏁" * 30)
    
    total_tests = len(results)
    successful_tests = sum(1 for success in results.values() if success)
    
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n📊 Résultat: {successful_tests}/{total_tests} tests réussis")
    
    if successful_tests == total_tests:
        print("🎉 Tous les tests sont passés! Le système est prêt.")
        print("\n📚 Prochaines étapes:")
        print("   1. Démarrer l'API: python -m uvicorn app.main:app --reload")
        print("   2. Configurer les emails dans .env")
        print("   3. Tester avec: python test_complete_workflow.py simple --user-id 2")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez la configuration.")
    
    return successful_tests == total_tests

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 