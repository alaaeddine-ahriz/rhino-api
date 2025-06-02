from app.db.models import Challenge, ChallengeServed, Matiere
from app.db.session import get_session
from sqlmodel import select
from fastapi import Depends
from datetime import datetime

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

def get_next_challenge_for_matiere(matiere: str, session, granularite: str = None):
    """Sert le challenge du tick courant pour la matière et la granularité, sans resservir avant d'avoir tout épuisé."""
    # 1. Récupérer la granularité de la matière si non fournie
    if granularite is None:
        matiere_obj = session.exec(select(Matiere).where(Matiere.name == matiere)).first()
        granularite = matiere_obj.granularite if matiere_obj else "semaine"
    # 2. Récupérer tous les challenges de la matière
    challenges = session.exec(
        select(Challenge).where(Challenge.matiere == matiere).order_by(Challenge.date, Challenge.id)
    ).all()
    if not challenges:
        return None
    # 3. Récupérer les refs déjà servis pour cette matière et granularité
    served_refs = set(
        row.challenge_ref for row in session.exec(
            select(ChallengeServed).where(
                ChallengeServed.matiere == matiere,
                # ChallengeServed.granularite == granularite
            )
        ).all()
    )
    # 4. Trouver le premier challenge non servi
    for challenge in challenges:
        if challenge.ref not in served_refs:
            tick = compute_tick(granularite, challenges[0].date)
            cs = ChallengeServed(matiere=matiere, challenge_ref=challenge.ref, tick=tick)
            session.add(cs)
            session.commit()
            return challenge
    # 5. Si tous ont été servis, reset la file et recommencer
    session.exec(
        select(ChallengeServed).where(
            ChallengeServed.matiere == matiere,
            # ChallengeServed.granularite == granularite
        )
    ).delete()
    session.commit()
    return get_next_challenge_for_matiere(matiere, session, granularite)

def compute_tick(granularite, ref_date_str):
    ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d")
    now = datetime.now()
    if granularite == "jour":
        return (now.date() - ref_date.date()).days
    elif granularite == "semaine":
        return ((now.date() - ref_date.date()).days) // 7
    elif granularite == "mois":
        return (now.year - ref_date.year) * 12 + (now.month - ref_date.month)
    elif granularite.endswith("jours"):
        n = int(granularite.replace("jours", ""))
        return ((now.date() - ref_date.date()).days) // n
    else:
        raise ValueError("Granularité non supportée")

if __name__ == "__main__":
    challenge_data = {
        "question": "Qu'est-ce que Kafka ?",
        "matiere": "SYD",
        "date": "2025-05-27"
    }
    creer_challenge(challenge_data)
    lister_challenges(matiere="SYD")