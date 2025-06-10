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

def evaluer_reponse(evaluation_data):
    """Évalue une réponse générique."""
    return {
        "success": True,
        "data": {
            "score": 80,
            "feedback": "Bonne réponse avec quelques améliorations possibles.",
            "grade": "B+",
            "suggestions": ["Ajouter plus d'exemples", "Clarifier certains points"]
        }
    }

def creer_evaluation(matiere: str, titre: str, questions: list):
    """Crée une nouvelle évaluation."""
    return {
        "success": True,
        "data": {
            "evaluation_id": "eval_001",
            "matiere": matiere,
            "titre": titre,
            "nb_questions": len(questions),
            "status": "created"
        }
    }

def obtenir_evaluations(matiere: str = None):
    """Obtient la liste des évaluations."""
    evaluations = [
        {
            "id": "eval_001",
            "titre": "Évaluation de base",
            "matiere": "SYD",
            "nb_questions": 5,
            "status": "active"
        },
        {
            "id": "eval_002", 
            "titre": "Test intermédiaire",
            "matiere": "TCP",
            "nb_questions": 8,
            "status": "active"
        }
    ]
    
    if matiere:
        evaluations = [e for e in evaluations if e["matiere"] == matiere]
    
    return {
        "success": True,
        "data": {
            "evaluations": evaluations,
            "count": len(evaluations)
        }
    } 