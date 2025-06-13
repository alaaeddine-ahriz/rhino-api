from sqlmodel import create_engine, Session
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database path from settings
db_path = settings.DB_PATH
logger.info(f"Initializing database at: {db_path}")

# Create database URL
DATABASE_URL = f"sqlite:///{db_path}"
logger.info(f"Database URL: {DATABASE_URL}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    poolclass=None,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
        "isolation_level": "IMMEDIATE"
    }
)

def get_session():
    with Session(engine) as session:
        yield session 