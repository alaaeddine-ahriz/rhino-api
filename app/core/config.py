"""Configuration settings for the API."""
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement depuis .env
load_dotenv()

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
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rag-sir")
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Folders
    COURS_DIR: str = os.getenv("COURS_DIR", "cours")
    OUTPUTS_DIR: str = os.getenv("OUTPUTS_DIR", "outputs")
    
    class Config:
        """Pydantic config class."""
        case_sensitive = True
        env_file = ".env"

# Create settings object
settings = Settings() 