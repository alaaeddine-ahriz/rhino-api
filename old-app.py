from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uvicorn
import io
import sys
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr

# Import functionality from main.py
try:
    from main import (
        initialiser_structure_dossiers,
        mettre_a_jour_matiere,
        interroger_matiere,
        generer_question_reflexion,
        evaluer_reponse_etudiant,
        initialize_pinecone,
        setup_embeddings,
        create_or_get_index,
        COURS_DIR,
        INDEX_NAME
    )
except ImportError as e:
    print(f"Error importing from main.py: {e}")
    # Optional fallback imports if needed
    # from your_alternative_module import ...

app = FastAPI(
    title="Le Rhino API",
    description="API pour gérer des documents de cours et générer des questions via RAG",
    version="1.0.0"
)

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Pinecone and embeddings at startup
@app.on_event("startup")
async def startup_db_client():
    try:
        app.pc, app.index_name, app.spec = initialize_pinecone()
        app.embeddings = setup_embeddings()
        app.index = create_or_get_index(app.pc, app.index_name, app.embeddings, app.spec)
        initialiser_structure_dossiers()
    except Exception as e:
        print(f"Error during startup: {e}")
        # Optional fallback initialization if needed

# Define API models
class QuestionRequest(BaseModel):
    matiere: str
    query: str
    output_format: str = "text"
    save_output: bool = True

class ReflectionQuestionRequest(BaseModel):
    matiere: str
    concept_cle: Optional[str] = ""
    output_format: str = "text"
    save_output: bool = True
    
class UpdateRequest(BaseModel):
    matiere: str

class EvaluationRequest(BaseModel):
    matiere: str
    question: str
    student_response: str
    save_output: bool = True

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = datetime.now().isoformat()

# Capture les logs d'une fonction
def capture_logs(func, *args, **kwargs):
    # Capturer la sortie standard et les erreurs
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        result = func(*args, **kwargs)
    
    # Récupérer les logs
    stdout_logs = stdout_buffer.getvalue()
    stderr_logs = stderr_buffer.getvalue()
    
    # Combiner les logs
    logs = stdout_logs
    if stderr_logs:
        logs += "\n--- ERREURS ---\n" + stderr_logs
    
    return result, logs

# Serve the frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    static_file_path = os.path.join("static", "index.html")
    if os.path.exists(static_file_path):
        with open(static_file_path, "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    else:
        return HTMLResponse(content="<html><body><h1>Error: index.html not found</h1></body></html>")

# API Routes
@app.get("/api", response_model=ApiResponse)
async def root():
    return {
        "success": True,
        "message": "Le Rhino API", 
        "data": {"status": "online"}
    }

@app.get("/matieres", response_model=ApiResponse)
async def get_matieres():
    """Liste toutes les matières disponibles"""
    matieres = []
    if os.path.exists(COURS_DIR):
        for item in os.listdir(COURS_DIR):
            item_path = os.path.join(COURS_DIR, item)
            if os.path.isdir(item_path) and not item.startswith('.'):
                matieres.append(item)
    
    return {
        "success": True,
        "message": f"{len(matieres)} matières trouvées",
        "data": {"matieres": matieres}
    }

@app.post("/matieres/update", response_model=ApiResponse)
async def update_matiere(request: UpdateRequest):
    """Met à jour l'index pour une matière spécifique"""
    matiere = request.matiere.upper()
    
    # Vérifier si la matière existe
    if not os.path.exists(os.path.join(COURS_DIR, matiere)):
        raise HTTPException(status_code=404, detail=f"Matière '{matiere}' non trouvée")
    
    # Mettre à jour la matière et capturer les logs
    try:
        updated, logs = capture_logs(mettre_a_jour_matiere, app.pc, app.index_name, app.embeddings, matiere)
        
        if updated:
            return {
                "success": True,
                "message": f"Matière {matiere} mise à jour avec succès",
                "data": {
                    "matiere": matiere, 
                    "updated": True,
                    "logs": logs
                }
            }
        else:
            return {
                "success": True,
                "message": f"Aucune mise à jour nécessaire pour la matière {matiere}",
                "data": {
                    "matiere": matiere, 
                    "updated": False,
                    "logs": logs
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour: {str(e)}")

@app.post("/question", response_model=ApiResponse)
async def ask_question(request: QuestionRequest):
    """Poser une question sur une matière spécifique"""
    matiere = request.matiere.upper()
    
    # Vérifier si la matière existe
    if not os.path.exists(os.path.join(COURS_DIR, matiere)):
        raise HTTPException(status_code=404, detail=f"Matière '{matiere}' non trouvée")
    
    try:
        response = interroger_matiere(
            app.index_name, 
            app.embeddings, 
            matiere, 
            request.query, 
            output_format=request.output_format,
            save_output=request.save_output
        )
        
        # Préparer les sources pour la réponse
        sources = []
        for i, doc in enumerate(response["context"]):
            source_info = {
                "document": i+1,
                "source": doc.metadata.get('source', 'Source inconnue')
            }
            
            # Ajouter la section si disponible
            if "Header 2" in doc.metadata:
                source_info["section"] = doc.metadata["Header 2"]
            elif "Header 3" in doc.metadata:
                source_info["section"] = doc.metadata["Header 3"]
            
            # Limiter la taille du contenu
            content = doc.page_content
            if len(content) > 250:
                content = content[:250] + "..."
            source_info["contenu"] = content
            
            sources.append(source_info)
        
        return {
            "success": True,
            "message": "Réponse générée avec succès",
            "data": {
                "response": response["answer"],
                "sources": sources,
                "matiere": matiere,
                "query": request.query
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de la réponse: {str(e)}")

@app.post("/question/reflection", response_model=ApiResponse)
async def generate_reflection_question(request: ReflectionQuestionRequest):
    """Générer une question de réflexion sur un concept clé"""
    matiere = request.matiere.upper()
    
    # Vérifier si la matière existe
    if not os.path.exists(os.path.join(COURS_DIR, matiere)):
        raise HTTPException(status_code=404, detail=f"Matière '{matiere}' non trouvée")
    
    try:
        response = generer_question_reflexion(
            app.index_name,
            app.embeddings,
            matiere,
            request.concept_cle,
            output_format=request.output_format,
            save_output=request.save_output
        )
        
        return {
            "success": True,
            "message": "Question de réflexion générée avec succès",
            "data": {
                "question": response,
                "matiere": matiere,
                "concept": request.concept_cle,
                "format": request.output_format
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de la question: {str(e)}")

@app.post("/evaluation/response", response_model=ApiResponse)
async def evaluate_student_response(request: EvaluationRequest):
    """Évaluer la réponse d'un étudiant à une question"""
    matiere = request.matiere.upper()
    
    # Vérifier si la matière existe
    if not os.path.exists(os.path.join(COURS_DIR, matiere)):
        raise HTTPException(status_code=404, detail=f"Matière '{matiere}' non trouvée")
    
    try:
        # Capturer les logs et exécuter l'évaluation
        response, logs = capture_logs(
            evaluer_reponse_etudiant,
            app.index_name,
            app.embeddings,
            matiere,
            request.question,
            request.student_response,
            output_format="json",
            save_output=request.save_output
        )
        
        # Extraire les données d'évaluation (déjà en format JSON)
        import json
        evaluation_data = json.loads(response["answer"])
        
        return {
            "success": True,
            "message": "Évaluation générée avec succès",
            "data": {
                "evaluation": evaluation_data,
                "matiere": matiere,
                "logs": logs
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'évaluation: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 