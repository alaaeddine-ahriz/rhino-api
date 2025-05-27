def upload_document(matiere: str, file, is_exam: bool):
    """Upload un document pour une matière."""
    return {"success": True, "message": f"Document {getattr(file, 'filename', 'unknown')} uploadé", "data": {"file_path": f"cours/{matiere}/{getattr(file, 'filename', 'unknown')}"}}

def lister_documents(matiere: str):
    """Liste les documents d'une matière."""
    return {"success": True, "data": [
        {"id": "doc1", "filename": "cours_intro.pdf", "matiere": matiere}
    ]}

def supprimer_document(matiere: str, document_id: str):
    """Supprime un document d'une matière."""
    return {"success": True, "message": f"Document {document_id} supprimé"} 