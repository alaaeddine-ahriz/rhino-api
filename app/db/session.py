from sqlmodel import create_engine, Session

DATABASE_URL = "sqlite:///./test.db"  # Modifier pour PostgreSQL en prod
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session 