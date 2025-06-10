import re
from datetime import datetime

def evaluer_reponse(evaluation):
    """Évalue une réponse d'étudiant basée sur l'objet d'évaluation en utilisant le système RAG IA."""
    from app.services.rag.questions import evaluer_reponse_etudiant as rag_evaluer_reponse
    
    # Extract data from evaluation object
    matiere = evaluation.matiere
    question_text = evaluation.question
    reponse_etudiant = evaluation.reponse_etudiant
    
    # Extract key concepts from the question for better RAG search
    # Remove common words and keep important concepts
    concept_keywords = re.findall(r'\b(?:virtualisation|système|réseau|serveur|TCP|UDP|OSI|HTTP|DNS|Kafka|architecture|données|sécurité|performance|protocole|infrastructure|cloud|container|docker|kubernetes|load|balancer|firewall|proxy|cache|database|sql|nosql|mongodb|redis|nginx|apache|linux|windows|unix|shell|api|rest|json|xml|yaml|configuration|monitoring|backup|recovery|scalability|availability|reliability|throughput|latency|bandwidth|encryption|authentication|authorization|ssl|tls|vpn|vlan|switch|router|gateway|subnet|nat|dhcp|ntp|snmp|ldap|active|directory|kerberos|oauth|saml|microservices|monolithe|devops|ci|cd|jenkins|git|svn|agile|scrum|kanban|test|unit|integration|deployment|staging|production|development|debugging|profiling|optimization|refactoring|documentation|versioning|release|hotfix|patch|feature|bug|issue|ticket|project|management|planning|estimation|risk|quality|assurance|performance|testing|load|stress|security|penetration|vulnerability|assessment|compliance|governance|audit|framework|design|pattern|architecture|mvc|mvp|mvvm|solid|dry|kiss|yagni|tdd|bdd|ddd|clean|code|code|review|pair|programming|refactoring|legacy|migration|upgrade|maintenance|support|troubleshooting|incident|monitoring|alerting|logging|metrics|dashboard|reporting|analytics|business|intelligence|data|mining|machine|learning|artificial|intelligence|neural|network|deep|learning|nlp|computer|vision|big|data|hadoop|spark|kafka|elasticsearch|kibana|grafana|prometheus|nagios|zabbix|ansible|puppet|chef|terraform|vagrant|docker|kubernetes|openshift|aws|azure|gcp|cloud|computing|saas|paas|iaas|serverless|lambda|functions|microservice|container|orchestration|service|mesh|istio|consul|vault|nomad|packer|boundary)\w*', question_text.lower())
    
    if concept_keywords:
        concept = " ".join(concept_keywords[:3])  # Use up to 3 key concepts
    else:
        # Fallback to question words, removing common words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', question_text)  # Words with 4+ letters
        concept = " ".join(words[:3]) if words else question_text[:50]
    
    # Create a question object for the RAG evaluation function
    question_data = {
        "question": question_text,
        "type": "reflection",  # Assume reflection type
        "concept": concept
    }
    
    try:
        # Call the AI evaluation function
        result = rag_evaluer_reponse(matiere, question_data, reponse_etudiant)
        
        # Check if evaluation was successful
        if "error" in result:
            # Return error response if AI evaluation fails
            return {
                "success": False,
                "message": f"Erreur d'évaluation IA: {result.get('error', 'Erreur inconnue')}",
                "data": {
                    "score": None,
                    "feedback": f"Évaluation automatique échouée pour la matière {matiere}. Veuillez réessayer plus tard.",
                    "note": None,
                    "points_forts": [],
                    "points_ameliorer": [],
                    "justification_note": "Évaluation automatique non disponible",
                    "suggestions": [],
                    "error_type": "rag_system_error",
                    "error_details": result.get('error', 'Erreur inconnue')
                }
            }
        
        # Transform the AI result to match our API format
        return {
            "success": True,
            "message": f"Évaluation IA terminée avec succès pour la matière {matiere}",
            "data": {
                "score": result.get("score", 0),
                "feedback": result.get("feedback", "Pas de feedback disponible"),
                "note": int(result.get("score", 0) * 20 / 100),  # Convert to /20 scale
                "points_forts": result.get("strengths", []),
                "points_ameliorer": result.get("areas_for_improvement", []),
                "justification_note": result.get("feedback", "Pas de justification disponible"),
                "suggestions": result.get("suggestions", []),
                "reponse_modele": result.get("model_answer", ""),
                "base_sur_examen": result.get("basé_sur_examen", False),
                "matiere": matiere,
                "evaluated_at": result.get("evaluated_at", datetime.now().isoformat())
            }
        }
        
    except Exception as e:
        # Return error response when AI evaluation fails
        return {
            "success": False,
            "message": f"Erreur lors de l'évaluation IA: {str(e)}",
            "data": {
                "score": None,
                "feedback": f"Évaluation IA indisponible pour la matière {matiere}. Veuillez réessayer plus tard.",
                "note": None,
                "points_forts": [],
                "points_ameliorer": [],
                "justification_note": "Évaluation automatique temporairement indisponible",
                "suggestions": [],
                "error_type": "ai_service_unavailable",
                "error_details": str(e)
            }
        } 