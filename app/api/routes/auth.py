"""Authentication routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Body, FastAPI
from datetime import timedelta
from typing import List, Optional

from app.core.security import create_access_token
from app.models.auth import TokenAuthRequest, TokenResponse, UserInDB, TokenInDB
from app.models.base import ApiResponse
from app.api.deps import get_user_from_token, get_admin_user, VALID_TOKENS_DB
from app.core.config import settings
from app.db.models import User
from app.db.session import get_session
from sqlmodel import select

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/token", response_model=TokenResponse)
async def authenticate_with_token(request: TokenAuthRequest):
    """
    Authenticate using a pre-generated token and get a JWT access token.
    
    Args:
        request: Contains the pre-generated authentication token
        
    Returns:
        JWT access token and user information
    """
    # Validate the pre-generated token
    logger.info("Tentative d'authentification avec un token")
    
    user = get_user_from_token(request.token)
    if not user:
        logger.warning("Échec d'authentification : token invalide ou expiré")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create a JWT access token
    access_token_expires = timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username, 
            "user_id": user.id,
            "role": user.role
        }, 
        expires_delta=access_token_expires
    )

    logger.info(f"Utilisateur authentifié : {user.username} (ID: {user.id})")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "user_info": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role
        }
    }

@router.get("/tokens", response_model=ApiResponse)
async def list_valid_tokens(current_user: UserInDB = Depends(get_admin_user)):
    """
    List all valid authentication tokens (admin only).
    
    Returns:
        List of all valid tokens with user information
    """
    logger.info(f"Admin {current_user.username} demande la liste des tokens valides")
    
    tokens_info = []
    for token, token_data in VALID_TOKENS_DB.items():
        tokens_info.append({
            "token": token,
            "user_id": token_data.user_id,
            "username": token_data.username,
            "role": token_data.role,
            "full_name": token_data.full_name,
            "email": token_data.email,
            "is_active": token_data.is_active
        })
    
    logger.info(f"{len(tokens_info)} tokens trouvés")
    return {
        "success": True,
        "message": f"{len(tokens_info)} tokens trouvés",
        "data": {"tokens": tokens_info}
    }

# Change le router ici pour éviter d’écraser celui de /auth
users_router = APIRouter(prefix="/users", tags=["Users"])

@users_router.post("/register")
async def register_user(
    username: str = Body(...),
    email: str = Body(...),
    role: str = Body(...),
    subscriptions: Optional[List[str]] = Body(default=[]),
    session=Depends(get_session)
):
    logger.info(f"Tentative d'enregistrement d'utilisateur : {username} ({email})")
    
    # Vérifier unicité email ou username
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        logger.warning(f"Échec de l'enregistrement : email déjà utilisé ({email})")
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    user = User(username=username, email=email, role=role, subscriptions=','.join(subscriptions))
    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info(f"Utilisateur enregistré avec succès : {user.username} (ID: {user.id})")
    
    return {"success": True, "message": "Utilisateur enregistré", "data": {"user_id": user.id}}

@users_router.put("/subscriptions")
async def update_or_get_subscriptions(
    user_id: int = Body(...),
    subscriptions: Optional[List[str]] = Body(default=None),
    session=Depends(get_session)
):
    logger.info(f"Requête de mise à jour/récupération des abonnements pour user_id={user_id}")
    
    user = session.get(User, user_id)
    if not user:
        logger.warning(f"Utilisateur non trouvé : ID {user_id}")
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if subscriptions is not None:
        user.subscriptions = ','.join(subscriptions)
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"Abonnements mis à jour pour l'utilisateur {user.username} (ID: {user.id})")
        return {"success": True, "message": "Abonnements mis à jour", "data": {"subscriptions": subscriptions}}

    current = user.subscriptions.split(',') if user.subscriptions else []
    logger.info(f"Abonnements récupérés pour l'utilisateur {user.username} (ID: {user.id})")
    return {"success": True, "message": "Abonnements récupérés", "data": {"subscriptions": current}}

app = FastAPI()
app.include_router(router)
app.include_router(users_router)