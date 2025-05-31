from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional
from app.db.models import User
from app.db.session import get_session
from sqlmodel import select

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register")
async def register_user(
    username: str = Body(...),
    email: str = Body(...),
    role: str = Body(...),
    subscriptions: Optional[List[str]] = Body(default=[]),
    session=Depends(get_session)
):
    # Vérifier unicité email ou username
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    user = User(username=username, email=email, role=role, subscriptions=','.join(subscriptions))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"success": True, "message": "Utilisateur enregistré", "data": {"user_id": user.id}}

@router.put("/subscriptions")
async def update_or_get_subscriptions(
    user_id: int = Body(...),
    subscriptions: Optional[List[str]] = Body(default=None),
    session=Depends(get_session)
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    if subscriptions is not None:
        user.subscriptions = ','.join(subscriptions)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"success": True, "message": "Abonnements mis à jour", "data": {"subscriptions": subscriptions}}
    # Si pas de subscriptions fourni, retourne la liste actuelle
    current = user.subscriptions.split(',') if user.subscriptions else []
    return {"success": True, "message": "Abonnements récupérés", "data": {"subscriptions": current}} 