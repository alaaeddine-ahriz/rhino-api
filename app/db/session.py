from sqlmodel import create_engine, Session

DATABASE_URL = "sqlite:///./prod.db"  # Modifier pour PostgreSQL en prod

# Configure SQLite engine with no pooling to avoid connection reuse issues
engine = create_engine(
    DATABASE_URL, 
    echo=True,
    poolclass=None,  # Disable connection pooling
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
        # Use immediate isolation level
        "isolation_level": "IMMEDIATE"
    }
)
 
def get_session():
    with Session(engine) as session:
        yield session 