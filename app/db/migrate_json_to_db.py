#!/usr/bin/env python3
"""
Script de migration pour transférer les données de conversations.json vers la base de données.
"""

import json
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, Any
from sqlmodel import SQLModel, create_engine, Session, select

# Ajouter le répertoire parent au chemin pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.models import StudentResponse, Evaluation, User, Challenge
from app.db.session import engine

def backup_current_db():
    """Sauvegarde la base de données actuelle."""
    if os.path.exists("prod.db"):
        backup_name = f"prod_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy("prod.db", backup_name)
        print(f"✅ Base de données sauvegardée : {backup_name}")
        return backup_name
    return None

def load_json_conversations():
    """Charge les conversations depuis le fichier JSON."""
    json_path = "mail/conversations.json"
    if not os.path.exists(json_path):
        print(f"❌ Fichier {json_path} non trouvé")
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur lors du chargement du JSON : {e}")
        return {}

def find_or_create_user(session: Session, email: str, user_id: int = None) -> int:
    """Trouve ou crée un utilisateur basé sur l'email et l'ID."""
    if user_id:
        # Essayer de trouver par ID d'abord
        user = session.get(User, user_id)
        if user:
            return user.id
    
    # Chercher par email
    stmt = select(User).where(User.email == email)
    user = session.exec(stmt).first()
    if user:
        return user.id
    
    # Créer un nouvel utilisateur
    new_user = User(
        username=email.split('@')[0],
        email=email,
        role="student"
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user.id

def find_challenge_by_api_id(session: Session, api_challenge_id: int) -> int:
    """Trouve un challenge par son api_challenge_id (mapping depuis l'ancien système)."""
    if not api_challenge_id:
        return None
    
    # Pour le moment, on utilise l'ID directement
    # Dans un vrai système, il faudrait un mapping plus sophistiqué
    challenge = session.get(Challenge, api_challenge_id)
    if challenge:
        return challenge.id
    return None

def migrate_conversations_to_db():
    """Migre les conversations du JSON vers la base de données."""
    print("🚀 Début de la migration des conversations...")
    
    # Charger les données JSON
    conversations = load_json_conversations()
    if not conversations:
        print("❌ Aucune conversation trouvée dans le JSON")
        return
    
    print(f"📊 {len(conversations)} conversations trouvées dans le JSON")
    
    # Créer les tables si elles n'existent pas
    SQLModel.metadata.create_all(engine)
    print("✅ Tables créées ou vérifiées")
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    with Session(engine) as session:
        for question_id, data in conversations.items():
            try:
                # Vérifier si cette réponse existe déjà
                stmt = select(StudentResponse).where(StudentResponse.question_id == question_id)
                existing = session.exec(stmt).first()
                if existing:
                    print(f"⏭️  Question {question_id} déjà migrée, passage")
                    skipped_count += 1
                    continue
                
                # Obtenir l'email de l'étudiant
                student_email = data.get('student', '')
                if not student_email:
                    print(f"❌ Pas d'email étudiant pour {question_id}")
                    error_count += 1
                    continue
                
                # Trouver ou créer l'utilisateur
                user_id = find_or_create_user(session, student_email, data.get('user_id'))
                
                # Trouver le challenge
                challenge_id = find_challenge_by_api_id(session, data.get('api_challenge_id'))
                
                # Créer la réponse de l'étudiant
                student_response = StudentResponse(
                    question_id=question_id,
                    user_id=user_id,
                    challenge_id=challenge_id,
                    response=data.get('response'),
                    response_date=data.get('response_date'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(student_response)
                session.commit()
                session.refresh(student_response)
                
                # Migrer l'évaluation si elle existe
                if data.get('evaluated') and 'evaluation' in data:
                    eval_data = data['evaluation']
                    
                    # Gérer les deux formats d'évaluation
                    if 'raw_api_response' in eval_data:
                        # Nouveau format avec raw_api_response
                        api_data = eval_data['raw_api_response'].get('data', {})
                        score = api_data.get('score', eval_data.get('score'))
                        feedback = api_data.get('feedback', eval_data.get('feedback'))
                        points_forts = json.dumps(api_data.get('points_forts', []))
                        points_ameliorer = json.dumps(api_data.get('points_ameliorer', []))
                        evaluated_at = api_data.get('evaluated_at')
                        raw_response = json.dumps(eval_data['raw_api_response'])
                    else:
                        # Ancien format simple
                        score = eval_data.get('score')
                        feedback = json.dumps(eval_data.get('feedback', []))
                        points_forts = None
                        points_ameliorer = None
                        evaluated_at = None
                        raw_response = json.dumps(eval_data)
                    
                    evaluation = Evaluation(
                        student_response_id=student_response.id,
                        score=score,
                        grade=eval_data.get('grade'),
                        feedback=feedback,
                        points_forts=points_forts,
                        points_ameliorer=points_ameliorer,
                        feedback_sent=data.get('feedback_sent', False),
                        feedback_sent_at=datetime.now() if data.get('feedback_sent') else None,
                        evaluated_at=evaluated_at,
                        raw_api_response=raw_response,
                        created_at=datetime.now()
                    )
                    
                    session.add(evaluation)
                    session.commit()
                
                migrated_count += 1
                if migrated_count % 10 == 0:
                    print(f"📈 {migrated_count} conversations migrées...")
                    
            except Exception as e:
                print(f"❌ Erreur lors de la migration de {question_id}: {e}")
                error_count += 1
                session.rollback()
    
    print(f"\n✅ Migration terminée:")
    print(f"   - {migrated_count} conversations migrées")
    print(f"   - {skipped_count} conversations déjà existantes")
    print(f"   - {error_count} erreurs")

def backup_json_file():
    """Crée une sauvegarde du fichier JSON."""
    json_file = "mail/conversations.json"
    if os.path.exists(json_file):
        backup_file = f"mail/conversations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import shutil
        shutil.copy2(json_file, backup_file)
        print(f"📋 Sauvegarde créée: {backup_file}")
        return backup_file
    return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrer les conversations JSON vers la base de données")
    parser.add_argument("--backup", action="store_true", help="Créer une sauvegarde du JSON avant migration")
    parser.add_argument("--force", action="store_true", help="Forcer la migration même si des données existent")
    
    args = parser.parse_args()
    
    if args.backup:
        backup_json_file()
    
    migrate_conversations_to_db() 