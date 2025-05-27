def initialiser_structure_dossiers(nom: str):
    """Initialise la structure de dossiers pour une matière."""
    return {"success": True, "message": f"Matière {nom} créée", "data": {"path": f"cours/{nom}"}}

def lister_matieres():
    """Liste toutes les matières disponibles."""
    return {"success": True, "data": ["SYD", "TCP"]}

def mettre_a_jour_matiere(nom: str):
    """Met à jour l'index d'une matière."""
    return {"success": True, "message": f"Matière {nom} mise à jour"} 