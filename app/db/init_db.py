from sqlmodel import SQLModel
from app.db.session import engine
import app.db.models  # Assure l'import des modèles

def init_db():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
    print("Base de données initialisée.") 