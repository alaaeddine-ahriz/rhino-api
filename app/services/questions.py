def interroger_matiere(matiere: str, query: str):
    """Interroge la matière via RAG."""
    return {"success": True, "data": {"response": f"Réponse simulée pour {matiere} : {query}"}}

def generer_question_reflexion(matiere: str, concept_cle: str):
    """Génère une question de réflexion sur un concept clé."""
    return {"success": True, "data": {"question": f"Expliquez l'importance de {concept_cle} en {matiere}"}} 