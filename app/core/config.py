"""Configuration settings for the API."""
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file
env_path = ROOT_DIR / ".env"
if not env_path.exists():
    raise FileNotFoundError(f".env file not found at {env_path}")

load_dotenv(env_path)
logger.info(f"Loaded .env file from: {env_path}")

# Debug: Print raw environment variable
raw_db_path = os.environ.get("DB_PATH", "")
logger.info(f"Raw DB_PATH from environment: '{raw_db_path}'")

class Settings(BaseSettings):
    """Application settings."""
    
    # API metadata
    API_TITLE: str = "Le Rhino API"
    API_DESCRIPTION: str = "API pour gérer des documents de cours et générer des questions via RAG"
    API_VERSION: str = "1.0.0"
    
    # JWT Authentication
    TOKEN_SECRET_KEY: str = os.getenv("TOKEN_SECRET_KEY", "secret_key_change_in_production")
    TOKEN_ALGORITHM: str = os.getenv("TOKEN_ALGORITHM", "HS256")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
    
    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rag-sir-v2")
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Tick scheduling
    # Global reference date used to compute tick numbers for all matières
    # Format ISO YYYY-MM-DD
    TICK_REFERENCE_DATE: str = os.getenv("TICK_REFERENCE_DATE", "2024-01-01")
    
    # Folders
    COURS_DIR: str = os.getenv("COURS_DIR", "cours")
    DB_PATH: str = os.environ["DB_PATH"]  # Strip any whitespace or special characters
    
    # Port
    PORT: str = os.getenv("PORT", "8000")

    class Config:
        """Pydantic config class."""
        case_sensitive = True
        env_file = str(env_path)

# Create settings object
settings = Settings()
logger.info(f"Database path configured: '{settings.DB_PATH}'") 