from app.db.models import Challenge
from app.db.session import get_session
from sqlmodel import select
from fastapi import Depends

def generer_challenge_quotidien():
    """Génère le challenge du jour."""
    return {"success": True, "data": {"challenge_id": "chall_1", "question": "Décrivez TCP/IP"}}

def lister_challenges(matiere=None):
    """Liste les challenges."""
    return {"success": True, "data": [
        {"challenge_id": "chall_1", "matiere": "TCP"}
    ]}

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