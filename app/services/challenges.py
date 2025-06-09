from app.db.models import Challenge, ChallengeServed, Matiere
from app.db.session import get_session
from sqlmodel import select
from fastapi import Depends
from datetime import datetime
from typing import Optional, Dict

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
    
    try:
        # Select only the essential columns that should exist
        query = select(Challenge.id, Challenge.question, Challenge.matiere, Challenge.date)
        if matiere:
            query = query.where(Challenge.matiere == matiere)
        results = session.exec(query).all()
        
        # Convert to dictionaries manually
        challenges = []
        for result in results:
            challenge_dict = {
                "id": result[0],
                "question": result[1], 
                "matiere": result[2],
                "date": result[3],
                "ref": f"{result[2]}-{result[0]:03d}"  # Generate ref from matiere and id
            }
            challenges.append(challenge_dict)
        
        return {"success": True, "data": {"challenges": challenges}}
    except Exception as e:
        print(f"Error in lister_challenges: {str(e)}")
        return {"success": False, "data": {"challenges": []}, "error": str(e)}

def creer_challenge(challenge_data, session=None):
    """Crée un challenge et l'ajoute à la base de données."""
    if session is None:
        # Pour usage direct (ex: script), ouvrir une session
        from app.db.session import engine
        from sqlmodel import Session
        with Session(engine) as session:
            return creer_challenge(challenge_data, session=session)
    
    try:
        # Remove 'ref' from challenge_data if it exists since the column might not exist
        challenge_data_clean = {k: v for k, v in challenge_data.items() if k != 'ref'}
        
        # Créer l'objet Challenge without ref
        challenge = Challenge(**challenge_data_clean)
        session.add(challenge)
        session.commit()
        session.refresh(challenge)
        
        # Generate ref after creation
        generated_ref = f"{challenge.matiere}-{challenge.id:03d}"
        
        # Try to update with ref if column exists, otherwise just return without it
        try:
            challenge.ref = generated_ref
            session.add(challenge)
            session.commit()
            session.refresh(challenge)
        except Exception:
            # Column doesn't exist, continue without it
            pass
        
        # Prepare response data
        response_data = challenge_data_clean.copy()
        response_data["ref"] = generated_ref
        response_data["id"] = challenge.id
        
        return {"success": True, "data": {"challenge_id": challenge.id, "challenge": response_data}}
    except Exception as e:
        print(f"Error creating challenge: {str(e)}")
        return {"success": False, "error": str(e)}

def soumettre_reponse(challenge_id: str, reponse: str):
    """Soumet une réponse à un challenge."""
    return {"success": True, "data": {"challenge_id": challenge_id, "reponse": reponse}}

def get_challenge_for_current_tick(matiere: str, session, granularite: str = None):
    """
    Get the challenge that should be served for the current tick.
    All users should get the same challenge during the same tick period.
    """
    # 1. Get subject granularity if not provided
    if granularite is None:
        matiere_obj = session.exec(select(Matiere).where(Matiere.name == matiere)).first()
        granularite = matiere_obj.granularite if matiere_obj else "semaine"
    
    # 2. Get all challenges for the subject, ordered by date and ID
    challenges = session.exec(
        select(Challenge.id, Challenge.question, Challenge.matiere, Challenge.date)
        .where(Challenge.matiere == matiere)
        .order_by(Challenge.date, Challenge.id)
    ).all()
    
    if not challenges:
        return None
    
    # Convert to challenge-like objects with generated refs
    challenge_objects = []
    for c in challenges:
        challenge_obj = type('Challenge', (), {
            'id': c[0],
            'question': c[1], 
            'matiere': c[2],
            'date': c[3],
            'ref': f"{c[2]}-{c[0]:03d}",
            'dict': lambda self: {
                'id': self.id,
                'question': self.question,
                'matiere': self.matiere, 
                'date': self.date,
                'ref': self.ref
            }
        })()
        challenge_objects.append(challenge_obj)
    
    # 3. Calculate current tick
    current_tick = compute_tick(granularite, challenge_objects[0].date)
    
    # 4. Check if we already have a challenge served for this tick
    served_challenge = session.exec(
        select(ChallengeServed)
        .where(
            ChallengeServed.matiere == matiere,
            ChallengeServed.granularite == granularite,
            ChallengeServed.tick == current_tick
        )
    ).first()
    
    if served_challenge:
        # Return the already served challenge for this tick
        for challenge in challenge_objects:
            if challenge.ref == served_challenge.challenge_ref:
                return challenge
        # If challenge not found (shouldn't happen), fall through to create new one
    
    # 5. No challenge served yet for this tick, determine which one to serve
    # Get all previously served challenges (from previous ticks)
    all_served_refs = set(
        row.challenge_ref for row in session.exec(
            select(ChallengeServed).where(
                ChallengeServed.matiere == matiere,
                ChallengeServed.granularite == granularite
            )
        ).all()
    )
    
    # 6. Find the first unserved challenge or cycle back to the beginning
    selected_challenge = None
    for challenge in challenge_objects:
        if challenge.ref not in all_served_refs:
            selected_challenge = challenge
            break
    
    # If all challenges have been served, reset and start over
    if not selected_challenge:
        # Delete all previous served challenges to reset the cycle
        delete_query = select(ChallengeServed).where(
            ChallengeServed.matiere == matiere,
            ChallengeServed.granularite == granularite
        )
        served_entries = session.exec(delete_query).all()
        for entry in served_entries:
            session.delete(entry)
        session.commit()
        
        # Take the first challenge
        selected_challenge = challenge_objects[0]
    
    # 7. Record this challenge as served for the current tick
    cs = ChallengeServed(
        matiere=matiere, 
        granularite=granularite, 
        challenge_ref=selected_challenge.ref, 
        tick=current_tick
    )
    session.add(cs)
    session.commit()
    
    return selected_challenge

def get_next_challenge_for_matiere(matiere: str, session, granularite: str = None):
    """
    DEPRECATED: Use get_challenge_for_current_tick instead.
    This function is kept for backward compatibility but now calls the tick-aware version.
    """
    return get_challenge_for_current_tick(matiere, session, granularite)

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

def get_today_challenge_for_user(user_subscriptions: str, session) -> Optional[Dict]:
    """
    Get today's challenge for a user based on their subscriptions.
    Uses tick logic to determine which challenge should be served today.
    
    Args:
        user_subscriptions: Comma-separated string of user's subscribed subjects
        session: Database session
        
    Returns:
        Dict with today's challenge or None if no challenge available
    """
    if not user_subscriptions:
        return None
    
    # Parse user subscriptions
    subscribed_subjects = [s.strip() for s in user_subscriptions.split(',') if s.strip()]
    
    if not subscribed_subjects:
        return None
    
    # Try to get a challenge from each subscribed subject
    today_challenges = []
    
    for matiere in subscribed_subjects:
        try:
            challenge = get_challenge_for_current_tick(matiere, session)
            if challenge:
                today_challenges.append({
                    "challenge": challenge,
                    "matiere": matiere
                })
        except Exception as e:
            print(f"Error getting challenge for {matiere}: {e}")
            continue
    
    if not today_challenges:
        return None
    
    # For now, return the first available challenge
    # In the future, this could implement more sophisticated logic like:
    # - Rotating between subjects
    # - Prioritizing subjects by user activity
    # - Considering challenge difficulty progression
    selected = today_challenges[0]
    
    return {
        "challenge_id": selected["challenge"].id,
        "ref": selected["challenge"].ref,
        "question": selected["challenge"].question,
        "matiere": selected["matiere"],
        "date": selected["challenge"].date,
        "matieres": [selected["matiere"]]  # Keep as array for backward compatibility
    }

if __name__ == "__main__":
    challenge_data = {
        "question": "Qu'est-ce que Kafka ?",
        "matiere": "SYD",
        "date": "2025-05-27"
    }
    creer_challenge(challenge_data)
    lister_challenges(matiere="SYD")