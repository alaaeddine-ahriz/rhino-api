"""RAG (Retrieval-Augmented Generation) service module."""

from app.services.rag.core import (
    initialize_pinecone,
    setup_embeddings,
    create_or_get_index,
    setup_rag_system
)

from app.services.rag.documents import (
    initialiser_structure_dossiers,
    lire_fichiers_matiere,
    split_document
)

from app.services.rag.questions import (
    generer_question_reflexion,
    generer_question_qcm,
    evaluer_reponse_etudiant,
    generer_serie_questions
)

__all__ = [
    # Core RAG functionality
    "initialize_pinecone",
    "setup_embeddings",
    "create_or_get_index",
    "setup_rag_system",
    
    # Document processing
    "initialiser_structure_dossiers",
    "lire_fichiers_matiere",
    "split_document",
    
    # Question generation and evaluation
    "generer_question_reflexion",
    "generer_question_qcm",
    "evaluer_reponse_etudiant",
    "generer_serie_questions"
]
