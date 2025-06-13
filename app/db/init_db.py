from sqlmodel import SQLModel, Session, text
from app.db.session import engine
import app.db.models  # Assure l'import des modèles
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database tables."""
    logger.info("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created successfully")

def migrate_database():
    """Handle database migrations for missing columns."""
    with Session(engine) as session:
        try:
            # Check if 'ref' column exists in challenge table
            result = session.exec(text("PRAGMA table_info(challenge)")).fetchall()
            columns = [column[1] for column in result]
            
            if 'ref' not in columns:
                logger.info("Adding missing 'ref' column to challenge table...")
                
                # Add the ref column
                session.exec(text("ALTER TABLE challenge ADD COLUMN ref TEXT"))
                
                # Update existing challenges with generated refs
                existing_challenges = session.exec(text("SELECT id, matiere FROM challenge")).fetchall()
                for challenge_id, matiere in existing_challenges:
                    ref = f"{matiere}-{challenge_id:03d}"
                    session.exec(text("UPDATE challenge SET ref = :ref WHERE id = :id"), 
                               {"ref": ref, "id": challenge_id})
                
                session.commit()
                logger.info("Successfully added 'ref' column and updated existing challenges.")
                
        except Exception as e:
            logger.error(f"Migration error: {e}")
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