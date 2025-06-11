"""Services for managing matières (subjects)."""
import os
import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

def initialiser_structure_dossiers(nom: str) -> Dict[str, Any]:
    """
    Initialise la structure de dossiers pour une matière.
    
    Args:
        nom: Nom de la matière
        
    Returns:
        Dict avec le statut et les informations de la matière créée
    """
    try:
        # Créer le chemin complet du dossier de la matière
        matiere_dir = os.path.join(settings.COURS_DIR, nom)
        
        # Vérifier si le dossier existe déjà
        if os.path.exists(matiere_dir):
            return {
                "success": False, 
                "message": f"La matière {nom} existe déjà",
                "data": {"path": f"{settings.COURS_DIR}/{nom}"}
            }
        
        # Créer le dossier principal de la matière
        os.makedirs(matiere_dir, exist_ok=True)
        
        # Créer le sous-dossier pour les examens
        examens_dir = os.path.join(matiere_dir, "examens")
        os.makedirs(examens_dir, exist_ok=True)
        
        # Créer un fichier README explicatif
        readme_path = os.path.join(matiere_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# Documents de cours pour {nom}\n\n")
            f.write("Placez vos documents de cours pour cette matière ici.\n")
            f.write("Formats supportés : .md, .txt, .pdf, .docx, .pptx\n\n")
            f.write("Structure recommandée pour les fichiers markdown :\n")
            f.write("- Utilisez ## pour les sections principales\n")
            f.write("- Chaque fichier devrait couvrir un concept ou sujet\n\n")
            f.write("## Dossier examens\n")
            f.write("Le sous-dossier `examens/` est destiné aux sujets d'examens et corrigés.\n")
        
        logger.info(f"Dossier créé pour la matière {nom} avec README explicatif")
        
        return {
            "success": True, 
            "message": f"Matière {nom} créée avec succès", 
            "data": {"path": f"{settings.COURS_DIR}/{nom}"}
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du dossier pour {nom}: {e}")
        return {
            "success": False, 
            "message": f"Erreur lors de la création de la matière {nom}: {str(e)}",
            "data": None
        }

def lister_matieres() -> Dict[str, Any]:
    """
    Liste toutes les matières disponibles en scannant le dossier cours.
    
    Returns:
        Dict avec la liste des matières disponibles
    """
    try:
        # Vérifier que le dossier cours existe
        if not os.path.exists(settings.COURS_DIR):
            logger.warning(f"Le dossier {settings.COURS_DIR} n'existe pas, création automatique")
            os.makedirs(settings.COURS_DIR, exist_ok=True)
            return {"success": True, "data": []}
        
        # Scanner le dossier cours pour trouver les sous-dossiers
        matieres = []
        for item in os.listdir(settings.COURS_DIR):
            item_path = os.path.join(settings.COURS_DIR, item)
            # Ignorer les fichiers cachés et ne garder que les dossiers
            if os.path.isdir(item_path) and not item.startswith('.'):
                matieres.append(item)
        
        # Trier la liste alphabétiquement
        matieres.sort()
        
        logger.info(f"Matières trouvées: {matieres}")
        return {"success": True, "data": matieres}
        
    except Exception as e:
        logger.error(f"Erreur lors de la liste des matières: {e}")
        return {"success": False, "data": [], "message": f"Erreur: {str(e)}"}



def supprimer_matiere(nom: str) -> Dict[str, Any]:
    """
    Supprime une matière et tous ses documents.
    
    Args:
        nom: Nom de la matière à supprimer
        
    Returns:
        Dict avec le statut de la suppression
    """
    try:
        import shutil
        
        # Vérifier que la matière existe
        matiere_dir = os.path.join(settings.COURS_DIR, nom)
        if not os.path.exists(matiere_dir):
            return {
                "success": False, 
                "message": f"La matière {nom} n'existe pas"
            }
        
        # Supprimer le dossier et tout son contenu
        shutil.rmtree(matiere_dir)
        
        logger.info(f"Matière {nom} supprimée avec succès")
        return {"success": True, "message": f"Matière {nom} supprimée avec succès"}
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de {nom}: {e}")
        return {
            "success": False, 
            "message": f"Erreur lors de la suppression de {nom}: {str(e)}"
        }

def obtenir_info_matiere(nom: str) -> Dict[str, Any]:
    """
    Obtient les informations détaillées d'une matière.
    
    Args:
        nom: Nom de la matière
        
    Returns:
        Dict avec les informations de la matière
    """
    try:
        matiere_dir = os.path.join(settings.COURS_DIR, nom)
        
        if not os.path.exists(matiere_dir):
            return {
                "success": False, 
                "message": f"La matière {nom} n'existe pas"
            }
        
        # Compter les documents
        document_count = 0
        last_update = None
        
        # Extensions supportées
        extensions = ['.md', '.txt', '.pdf', '.docx', '.pptx', '.doc', '.odt', '.odp']
        
        for root, dirs, files in os.walk(matiere_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    # Ignorer le README.md
                    if file.lower() != 'readme.md':
                        document_count += 1
                        
                        # Obtenir la date de dernière modification
                        file_path = os.path.join(root, file)
                        file_stat = os.stat(file_path)
                        file_mtime = file_stat.st_mtime
                        
                        if last_update is None or file_mtime > last_update:
                            last_update = file_mtime
        
        # Convertir le timestamp en ISO format si disponible
        last_update_iso = None
        if last_update:
            from datetime import datetime
            last_update_iso = datetime.fromtimestamp(last_update).isoformat()
        
        return {
            "success": True,
            "data": {
                "name": nom,
                "document_count": document_count,
                "last_update": last_update_iso,
                "path": matiere_dir
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des infos pour {nom}: {e}")
        return {
            "success": False, 
            "message": f"Erreur: {str(e)}"
        } 