from sqlmodel import create_engine, Session, text
from app.core.config import settings
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database path from settings
db_path = settings.DB_PATH
logger.info(f"Initializing database at: {db_path}")
logger.info(f"Database absolute path: {os.path.abspath(db_path)}")
logger.info(f"Database exists: {os.path.exists(db_path)}")
logger.info(f"Database directory exists: {os.path.exists(os.path.dirname(db_path))}")

# Ensure database directory exists
db_dir = os.path.dirname(db_path)
if not os.path.exists(db_dir):
    os.makedirs(db_dir)
    logger.info(f"Created database directory: {db_dir}")

# Create database URL
DATABASE_URL = f"sqlite:///{db_path}"
logger.info(f"Database URL: {DATABASE_URL}")

# Create engine with optimized settings for concurrent access
engine = create_engine(
    DATABASE_URL,
    echo=True,
    poolclass=None,
    connect_args={
        "check_same_thread": False,  # Allow multiple threads to access the database
        "timeout": 60,  # Increase timeout for busy database
        "isolation_level": "IMMEDIATE",  # Use immediate transaction isolation
    }
)

# Configure SQLite pragmas after engine creation
def configure_sqlite():
    with engine.connect() as conn:
        logger.info("Configuring SQLite pragmas...")
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        conn.execute(text("PRAGMA busy_timeout=60000"))
        conn.execute(text("PRAGMA cache_size=-2000"))
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("PRAGMA temp_store=MEMORY"))
        conn.execute(text("PRAGMA locking_mode=NORMAL"))  # Ensure proper locking
        conn.commit()
        logger.info("SQLite pragmas configured successfully")

# Configure SQLite settings
configure_sqlite()

def get_session():
    with Session(engine) as session:
        yield session 