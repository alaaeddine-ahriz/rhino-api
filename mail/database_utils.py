"""
Utilitaires pour interagir avec la base de données
"""
import sqlite3
import logging
from typing import Optional, Dict, Any, List

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Chemin vers la base de données (ajuster selon votre configuration)
DATABASE_PATH = "../prod.db"  # Ou "../sample_data.db" selon votre environnement

def get_database_connection():
    """
    Établit une connexion à la base de données
    
    Returns:
        sqlite3.Connection: Connexion à la base de données
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erreur de connexion à la base de données: {e}")
        return None

def get_student_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Récupère les informations d'un étudiant par son ID
    
    Args:
        user_id: ID de l'utilisateur
    
    Returns:
        Dict contenant les informations de l'étudiant ou None si non trouvé
    """
    conn = get_database_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, role, subscriptions 
            FROM user 
            WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "role": row["role"],
                "subscriptions": row["subscriptions"].split(",") if row["subscriptions"] else []
            }
        
        return None
        
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de la récupération de l'utilisateur {user_id}: {e}")
        return None
    finally:
        conn.close()

def get_all_students() -> List[Dict[str, Any]]:
    """
    Récupère tous les étudiants de la base de données
    
    Returns:
        Liste des étudiants
    """
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, role, subscriptions 
            FROM user 
            WHERE role = 'student'
        """)
        
        students = []
        for row in cursor.fetchall():
            students.append({
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "role": row["role"],
                "subscriptions": row["subscriptions"].split(",") if row["subscriptions"] else []
            })
        
        return students
        
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de la récupération des étudiants: {e}")
        return []
    finally:
        conn.close()

def get_students_by_subscription(matiere: str) -> List[Dict[str, Any]]:
    """
    Récupère tous les étudiants abonnés à une matière spécifique
    
    Args:
        matiere: Nom de la matière
    
    Returns:
        Liste des étudiants abonnés à cette matière
    """
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, role, subscriptions 
            FROM user 
            WHERE role = 'student' 
            AND (subscriptions LIKE ? OR subscriptions LIKE ? OR subscriptions LIKE ? OR subscriptions = ?)
        """, (f"%{matiere},%", f"%,{matiere},%", f"%,{matiere}", matiere))
        
        students = []
        for row in cursor.fetchall():
            students.append({
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "role": row["role"],
                "subscriptions": row["subscriptions"].split(",") if row["subscriptions"] else []
            })
        
        return students
        
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de la récupération des étudiants pour {matiere}: {e}")
        return []
    finally:
        conn.close()

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

def get_database_stats() -> Dict[str, Any]:
    """
    Récupère des statistiques sur la base de données
    
    Returns:
        Dict contenant les statistiques
    """
    conn = get_database_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        
        # Compter les utilisateurs par rôle
        cursor.execute("SELECT role, COUNT(*) as count FROM user GROUP BY role")
        role_counts = {row["role"]: row["count"] for row in cursor.fetchall()}
        
        # Compter le total d'utilisateurs
        cursor.execute("SELECT COUNT(*) as total FROM user")
        total_users = cursor.fetchone()["total"]
        
        # Compter les matières
        cursor.execute("SELECT COUNT(*) as total FROM matiere")
        total_matieres = cursor.fetchone()["total"]
        
        # Compter les challenges
        cursor.execute("SELECT COUNT(*) as total FROM challenge")
        total_challenges = cursor.fetchone()["total"]
        
        return {
            "total_users": total_users,
            "users_by_role": role_counts,
            "total_matieres": total_matieres,
            "total_challenges": total_challenges
        }
        
    except sqlite3.Error as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        return {}
    finally:
        conn.close()

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
    
    print(f"📚 Total matières: {stats.get('total_matieres', 0)}")
    print(f"🧠 Total challenges: {stats.get('total_challenges', 0)}")
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