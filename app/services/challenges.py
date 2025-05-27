from app.db.models import Challenge
from app.db.session import get_session
from sqlmodel import select
from fastapi import Depends

def generer_challenge_quotidien():
    """Génère le challenge du jour."""
    return {"success": True, "data": {"challenge_id": "chall_1", "question": "Décrivez TCP/IP"}}

def lister_challenges(matiere=None, session=None):
    """Liste les challenges depuis la base de données, avec option de filtrage par matière."""
    if session is None:
        from app.db.session import engine
        from sqlmodel import Session
        with Session(engine) as session:
            return lister_challenges(matiere=matiere, session=session)
    query = select(Challenge)
    if matiere:
        query = query.where(Challenge.matiere == matiere)
    results = session.exec(query).all()
    challenges = [challenge.dict() for challenge in results]
    return {"success": True, "data": {"challenges": challenges}}

def creer_challenge(challenge_data, session=None):
    """Crée un challenge et l'ajoute à la base de données."""
    if session is None:
        # Pour usage direct (ex: script), ouvrir une session
        from app.db.session import engine
        from sqlmodel import Session
        with Session(engine) as session:
            return creer_challenge(challenge_data, session=session)
    # Créer l'objet Challenge
    challenge = Challenge(**challenge_data)
    session.add(challenge)
    session.commit()
    session.refresh(challenge)
    return {"success": True, "data": {"challenge_id": challenge.id, "challenge": challenge_data}}

def soumettre_reponse(challenge_id: str, reponse: str):
    """Soumet une réponse à un challenge."""
    return {"success": True, "data": {"challenge_id": challenge_id, "reponse": reponse}} 

if __name__ == "__main__":
    challenge_data = {
        "question": "Qu'est-ce que Kafka ?",
        "matiere": "SYD",
        "date": "2025-05-27"
    }
    creer_challenge(challenge_data)
    lister_challenges(matiere="SYD")