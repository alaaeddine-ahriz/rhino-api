"""User management routes (simplified)."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from sqlmodel import select

from app.models.base import ApiResponse
from app.db.models import User
from app.db.session import get_session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
async def register_user(
    username: str = Body(...),
    email: str = Body(...),
    role: str = Body(...),
    subscriptions: Optional[List[str]] = Body(default=[]),
    session=Depends(get_session)
):
    """Register a new user."""
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

@router.put("/subscriptions")
async def update_or_get_subscriptions(
    user_id: int = Body(...),
    subscriptions: Optional[List[str]] = Body(default=None),
    session=Depends(get_session)
):
    """Update or get user subscriptions."""
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

@router.put("/{user_id}")
async def update_user_info(
    user_id: int,
    username: Optional[str] = Body(default=None),
    email: Optional[str] = Body(default=None),
    role: Optional[str] = Body(default=None),
    session=Depends(get_session)
):
    """Update user information."""
    logger.info(f"Requête de mise à jour des informations pour user_id={user_id}")
    
    user = session.get(User, user_id)
    if not user:
        logger.warning(f"Utilisateur non trouvé : ID {user_id}")
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Check if email is being updated and ensure uniqueness
    if email is not None and email != user.email:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            logger.warning(f"Échec de la mise à jour : email déjà utilisé ({email})")
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        user.email = email
    
    # Update other fields if provided
    if username is not None:
        user.username = username
    
    if role is not None:
        user.role = role
    
    # Only commit if there were changes
    if any([username is not None, email is not None, role is not None]):
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"Informations mises à jour pour l'utilisateur {user.username} (ID: {user.id})")
        
        return {
            "success": True, 
            "message": "Informations utilisateur mises à jour", 
            "data": {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }
    else:
        logger.info(f"Aucune modification pour l'utilisateur {user.username} (ID: {user.id})")
        return {"success": True, "message": "Aucune modification apportée"}