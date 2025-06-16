"""
Utilitaires pour interagir avec la base de données
"""
import logging
from typing import Optional, Dict, Any, List
from sqlmodel import Session, select
from app.db.session import engine
from app.db.models import User

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_student_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère les informations d'un étudiant par son ID
    """
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "subscriptions": user.subscriptions.split(",") if user.subscriptions else []
            }
        return None

def get_all_students() -> List[Dict[str, Any]]:
    """
    Récupère tous les étudiants de la base de données
    """
    with Session(engine) as session:
        students = session.exec(select(User).where(User.role == 'student')).all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "subscriptions": user.subscriptions.split(",") if user.subscriptions else []
            }
            for user in students
        ]

def get_students_by_subscription(matiere: str) -> List[Dict[str, Any]]:
    """
    Récupère tous les étudiants abonnés à une matière spécifique
    """
    with Session(engine) as session:
        students = session.exec(
            select(User).where(
                (User.role == 'student') & (
                    (User.subscriptions.like(f"%{matiere},%")) |
                    (User.subscriptions.like(f"%,{matiere},%")) |
                    (User.subscriptions.like(f"%,{matiere}")) |
                    (User.subscriptions == matiere)
                )
            )
        ).all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "subscriptions": user.subscriptions.split(",") if user.subscriptions else []
            }
            for user in students
        ]

def get_database_stats() -> Dict[str, Any]:
    """
    Récupère des statistiques sur la base de données
    """
    with Session(engine) as session:
        # Compter les utilisateurs par rôle
        role_counts = {row[0]: row[1] for row in session.exec(
            select(User.role, User.id).group_by(User.role)
        ).all()}
        # Compter le total d'utilisateurs
        total_users = session.exec(select(User)).count()
        # Compter les matières et challenges si les modèles existent
        # (Assume you have Matiere and Challenge models imported if needed)
        return {
            "total_users": total_users,
            "users_by_role": role_counts,
            # Add more stats as needed
        }

def verify_user_exists(user_id: int) -> bool:
    """
    Vérifie si un utilisateur existe dans la base de données
    
    Args:
        user_id: ID de l'utilisateur
    
    Returns:
        bool: True si l'utilisateur existe
    """
    student = get_student_by_id(user_id)
    return student is not None

def print_database_info():
    """Affiche des informations sur la base de données"""
    stats = get_database_stats()
    
    print("\n" + "="*50)
    print("📊 INFORMATIONS BASE DE DONNÉES")
    print("="*50)
    print(f"👥 Total utilisateurs: {stats.get('total_users', 0)}")
    
    users_by_role = stats.get('users_by_role', {})
    for role, count in users_by_role.items():
        print(f"   - {role}: {count}")
    
    print("="*50)

if __name__ == "__main__":
    # Test des fonctions
    print_database_info()
    
    # Afficher quelques étudiants
    students = get_all_students()
    print(f"\n📋 Étudiants trouvés: {len(students)}")
    for student in students[:3]:  # Afficher les 3 premiers
        print(f"   - {student['username']} ({student['email']}) - ID: {student['id']}")
        print(f"     Abonnements: {', '.join(student['subscriptions'])}") 