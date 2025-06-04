import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from app.db.models import User
from app.db.session import get_session
from sqlmodel import select

# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
async def register_user(
    username: str = Body(...),
    email: str = Body(...),
    role: str = Body(...),
    subscriptions: Optional[List[str]] = Body(default=[]),
    session=Depends(get_session)
):
    logger.info(f"Tentative d'enregistrement pour l'utilisateur '{username}' avec l'email '{email}'")

    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        logger.warning(f"Échec enregistrement: email '{email}' déjà utilisé")
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    user = User(username=username, email=email, role=role, subscriptions=','.join(subscriptions))
    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info(f"Utilisateur enregistré avec succès: ID={user.id}, username='{username}'")
    return {
        "success": True,
        "message": "Utilisateur enregistré",
        "data": {"user_id": user.id}
    }

@router.put("/subscriptions")
async def update_or_get_subscriptions(
    user_id: int = Body(...),
    subscriptions: Optional[List[str]] = Body(default=None),
    session=Depends(get_session)
):
    logger.info(f"Requête de mise à jour/récupération d'abonnements pour user_id={user_id}")

    user = session.get(User, user_id)
    if not user:
        logger.error(f"Utilisateur introuvable: ID={user_id}")
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if subscriptions is not None:
        user.subscriptions = ','.join(subscriptions)
        session.add(user)
        session.commit()
        session.refresh(user)
        logger.info(f"Abonnements mis à jour pour user_id={user_id}: {subscriptions}")
        return {
            "success": True,
            "message": "Abonnements mis à jour",
            "data": {"subscriptions": subscriptions}
        }

    current = user.subscriptions.split(',') if user.subscriptions else []
    logger.info(f"Abonnements récupérés pour user_id={user_id}: {current}")
    return {
        "success": True,
        "message": "Abonnements récupérés",
        "data": {"subscriptions": current}
    }