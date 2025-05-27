def evaluer_reponse_etudiant(matiere: str, question: str, reponse: str):
    """Évalue la réponse d'un étudiant."""
    return {
        "success": True,
        "data": {
            "note": 75,
            "points_forts": ["Bonne compréhension"],
            "points_ameliorer": ["Approfondir l'analyse"],
            "justification_note": "Réponse correcte mais manque de détails."
        }
    } 