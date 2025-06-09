from sqlmodel import SQLModel, Session, text
from app.db.session import engine
import app.db.models  # Assure l'import des modèles

def init_db():
    """Initialize database tables and handle migrations."""
    SQLModel.metadata.create_all(engine)
    migrate_database()

def migrate_database():
    """Handle database migrations for missing columns."""
    with Session(engine) as session:
        try:
            # Check if 'ref' column exists in challenge table
            result = session.exec(text("PRAGMA table_info(challenge)")).fetchall()
            columns = [column[1] for column in result]
            
            if 'ref' not in columns:
                print("Adding missing 'ref' column to challenge table...")
                
                # Add the ref column
                session.exec(text("ALTER TABLE challenge ADD COLUMN ref TEXT"))
                
                # Update existing challenges with generated refs
                existing_challenges = session.exec(text("SELECT id, matiere FROM challenge")).fetchall()
                for challenge_id, matiere in existing_challenges:
                    ref = f"{matiere}-{challenge_id:03d}"
                    session.exec(text("UPDATE challenge SET ref = :ref WHERE id = :id"), 
                               {"ref": ref, "id": challenge_id})
                
                session.commit()
                print("Successfully added 'ref' column and updated existing challenges.")
                
        except Exception as e:
            print(f"Migration error: {e}")
            session.rollback()

def reset_database():
    """Drop all tables and recreate them (useful for development)."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    print("Database reset completed.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        init_db()
    print("Base de données initialisée.") 