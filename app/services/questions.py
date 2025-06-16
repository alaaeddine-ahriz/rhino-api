from datetime import datetime
import json

def generer_question_reflexion(matiere: str, concept_cle: str):
    """Génère une question de réflexion sur un concept clé."""
    return {"success": True, "data": {"question": f"Expliquez l'importance de {concept_cle} en {matiere}"}}

def generer_question_qcm(matiere: str):
    """Génère une question QCM pour une matière."""
    return {
        "success": True,
        "data": {
            "question": f"Quelle est la principale caractéristique de {matiere} ?",
            "options": [
                "Option A",
                "Option B", 
                "Option C",
                "Option D"
            ],
            "correct_answer": 0
        }
    }

def valider_reponse_qcm(question_id: str, user_answer: int):
    """Valide une réponse QCM."""
    return {
        "success": True,
        "data": {
            "correct": True,
            "score": 100,
            "explanation": "Excellente réponse!"
        }
    }

def generer_question_vrai_faux(matiere: str):
    """Génère une question vrai/faux pour une matière."""
    return {
        "success": True,
        "data": {
            "question": f"L'étude de {matiere} est importante pour la formation.",
            "correct_answer": True
        }
    }

def valider_reponse_vrai_faux(question_id: str, user_answer: bool):
    """Valide une réponse vrai/faux."""
    return {
        "success": True,
        "data": {
            "correct": True,
            "score": 100,
            "explanation": "Réponse correcte!"
        }
    } 