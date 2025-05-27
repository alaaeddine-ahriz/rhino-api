def generer_challenge_quotidien():
    """Génère le challenge du jour."""
    return {"success": True, "data": {"challenge_id": "chall_1", "question": "Décrivez TCP/IP"}}

def lister_challenges(matiere=None):
    """Liste les challenges."""
    return {"success": True, "data": [
        {"challenge_id": "chall_1", "matiere": "TCP"}
    ]}

def creer_challenge(challenge):
    """Crée un challenge."""
    return {"success": True, "data": {"challenge_id": "new_chall", "challenge": challenge}}

def soumettre_reponse(challenge_id: str, reponse: str):
    """Soumet une réponse à un challenge."""
    return {"success": True, "data": {"challenge_id": challenge_id, "reponse": reponse}} 