"""Question generation and evaluation using RAG system."""
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from langchain.schema import Document
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import openai

from app.core.config import settings
from app.services.rag.core import (
    setup_rag_system,
    create_json_prompt,
    initialize_pinecone,
    setup_embeddings,
    create_or_get_index
)
from app.services.rag.documents import lire_fichiers_matiere, split_document

# Global variables for RAG system components
_pc = None
_index_name = None
_embeddings = None
_vector_store = None

def initialize_rag_components():
    """Initialize RAG system components if not already initialized."""
    global _pc, _index_name, _embeddings, _vector_store
    
    if _pc is None:
        _pc, _index_name, spec = initialize_pinecone()
        _embeddings = setup_embeddings()
        _vector_store = create_or_get_index(_pc, _index_name, _embeddings, spec)
    
    return _pc, _index_name, _embeddings, _vector_store

def generer_question_reflexion(matiere: str, concept_cle: str) -> Dict[str, Any]:
    """
    Generate a reflection question on a key concept using RAG.
    
    Args:
        matiere: Subject identifier
        concept_cle: Key concept to generate question about
        
    Returns:
        Dict[str, Any]: Generated question with metadata
    """
    try:
        # Initialize RAG system
        _, index_name, embeddings, _ = initialize_rag_components()
        retrieval_chain, vector_store = setup_rag_system(
            index_name=index_name,
            embeddings=embeddings,
            matiere=matiere
        )
        
        if not retrieval_chain:
            return {
                "error": "Failed to initialize RAG system",
                "status": "error"
            }
        
        # Create prompt for reflection question
        prompt_template = """
        Vous êtes un tuteur IA spécialisé dans la matière {matiere}, disposant d'un accès direct aux documents de cours via un système de recherche sémantique (RAG).

        Votre tâche est de générer une question de réflexion originale sur le concept {concept_cle}, en vous basant strictement sur les extraits suivants:

        {context}

        IMPORTANT CONCERNANT LES EXAMENS:
        Certains des documents fournis peuvent être des fichiers d'examens (identifiés par "is_exam": true dans les métadonnées).
        Si ces documents sont présents parmi les sources, vous devez:
        1. Analyser le style, le niveau et le type de questions posées par les professeurs dans ces examens
        2. Comprendre la structure et la formulation typique des questions d'examen
        3. Créer une question ORIGINALE qui suit le même style et niveau, mais qui:
           - N'est PAS une variation ou reformulation des questions existantes
           - Aborde un aspect différent ou complémentaire du concept
           - Utilise un angle d'approche nouveau
           - Reste dans le même niveau de difficulté et de réflexion

        La question doit :
        1. Être ORIGINALE et non une reformulation des questions existantes
        2. Solliciter l'analyse critique d'un concept ou d'une relation entre plusieurs notions
        3. Être formulée de manière claire, concise et précise, avec un vocabulaire académique adapté
        4. Favoriser une réponse argumentée plutôt qu'une simple définition
        5. Suivre le style et le niveau des questions d'examen si des documents d'examen font partie des sources

        Votre réponse DOIT être strictement au format JSON suivant:

        {{
            "question": "La question de réflexion originale",
            "concept": "{concept_cle}",
            "difficulty": "medium",
            "type": "reflection",
            "hints": [
                "Premier élément attendu dans la réponse",
                "Deuxième élément attendu dans la réponse",
                "Troisième élément attendu dans la réponse"
            ],
            "concepts_abordés": ["concept1", "concept2", "concept3"],
            "compétences_visées": ["analyse critique", "synthèse", "application pratique"],
            "basé_sur_examen": true/false,
            "originalité": "Explication de l'angle original choisi pour la question"
        }}
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["concept_cle", "matiere", "context"]
        )
        
        # Get relevant context using RAG
        response = retrieval_chain.invoke({"input": concept_cle})
        context = response.get("context", []) if isinstance(response, dict) else []
        
        # Generate question using LLM
        llm = ChatOpenAI(
            model_name=settings.OPENAI_MODEL,
            temperature=0.7
        )
        
        # Create the chain using the new pattern
        chain = prompt | llm
        
        response = chain.invoke({
            "concept_cle": concept_cle,
            "matiere": matiere,
            "context": "\n".join([doc.page_content for doc in context])
        })
        
        # Parse JSON response from AIMessage content
        question_data = json.loads(response.content)
        
        # Add metadata and source documents
        sources = []
        for i, doc in enumerate(context):
            source_entry = {
                "document": i + 1,
                "source": doc.metadata.get('source', 'Source inconnue'),
                "is_exam": doc.metadata.get('is_exam', False)
            }
            
            # Add section if it exists
            if "Header 2" in doc.metadata:
                source_entry["section"] = doc.metadata["Header 2"]
            elif "Header 3" in doc.metadata:
                source_entry["section"] = doc.metadata["Header 3"]
            
            # Limit content to avoid too long excerpts
            max_content_length = 250  # Characters
            content = doc.page_content
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            source_entry["contenu"] = content
            sources.append(source_entry)
        
        question_data.update({
            "matiere": matiere,
            "generated_at": datetime.now().isoformat(),
            "source_documents": sources
        })
        
        return question_data
        
    except openai.RateLimitError as e:
        return {
            "error": "OpenAI API quota exceeded. Please check your billing details and try again later.",
            "status": "quota_exceeded",
            "details": str(e)
        }
    except openai.AuthenticationError as e:
        return {
            "error": "OpenAI API authentication failed. Please check your API key.",
            "status": "auth_error",
            "details": str(e)
        }
    except openai.APIError as e:
        return {
            "error": f"OpenAI API error: {str(e)}",
            "status": "api_error",
            "details": str(e)
        }
    except json.JSONDecodeError as e:
        return {
            "error": "Failed to parse generated question as JSON. The AI response may be malformed.",
            "status": "json_parse_error",
            "details": str(e)
        }
    except Exception as e:
        return {
            "error": f"Failed to generate question: {str(e)}",
            "status": "error",
            "details": str(e)
        }

def generer_question_qcm(matiere: str, concept: str, nombre_options: int = 4) -> Dict[str, Any]:
    """
    Generate a multiple-choice question using RAG.
    
    Args:
        matiere: Subject identifier
        concept: Concept to generate question about
        nombre_options: Number of answer options (default: 4)
        
    Returns:
        Dict[str, Any]: Generated MCQ with metadata
    """
    # Initialize RAG system
    _, index_name, embeddings, _ = initialize_rag_components()
    retrieval_chain, vector_store = setup_rag_system(
        index_name=index_name,
        embeddings=embeddings,
        matiere=matiere
    )
    
    if not retrieval_chain:
        return {
            "error": "Failed to initialize RAG system",
            "status": "error"
        }
    
    # Create prompt for MCQ generation
    prompt_template = """
    Vous êtes un tuteur IA spécialisé dans la matière {matiere}, disposant d'un accès direct aux documents de cours via un système de recherche sémantique (RAG).

    Votre tâche est de générer une question à choix multiples originale sur le concept {concept}, en vous basant strictement sur les extraits suivants:

    {context}

    IMPORTANT CONCERNANT LES EXAMENS:
    Certains des documents fournis peuvent être des fichiers d'examens (identifiés par "is_exam": true dans les métadonnées).
    Si ces documents sont présents parmi les sources, vous devez:
    1. Analyser le style, le niveau et le type de questions posées par les professeurs dans ces examens
    2. Comprendre la structure et la formulation typique des questions d'examen
    3. Créer une question ORIGINALE qui suit le même style et niveau, mais qui:
       - N'est PAS une variation ou reformulation des questions existantes
       - Aborde un aspect différent ou complémentaire du concept
       - Utilise un angle d'approche nouveau
       - Reste dans le même niveau de difficulté et de réflexion

    La question doit :
    1. Être ORIGINALE et non une reformulation des questions existantes
    2. Tester la compréhension des concepts clés
    3. Avoir une seule réponse correcte
    4. Avoir des distracteurs plausibles
    5. Suivre le style et le niveau des questions d'examen si des documents d'examen font partie des sources

    Votre réponse DOIT être strictement au format JSON suivant:

    {{
        "question": "La question à choix multiples originale",
        "options": [
            {{
                "text": "Option text",
                "is_correct": true/false
            }},
            ...
        ],
        "concept": "{concept}",
        "difficulty": "medium",
        "type": "mcq",
        "explanation": "Explication détaillée de la réponse correcte",
        "concepts_abordés": ["concept1", "concept2", "concept3"],
        "compétences_visées": ["compréhension", "application", "analyse"],
        "basé_sur_examen": true/false,
        "originalité": "Explication de l'angle original choisi pour la question"
    }}
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["concept", "matiere", "context", "nombre_options"]
    )
    
    # Get relevant context using RAG
    response = retrieval_chain.invoke({"input": concept})
    context = response.get("context", []) if isinstance(response, dict) else []
    
    # Generate question using LLM
    llm = ChatOpenAI(
        model_name=settings.OPENAI_MODEL,
        temperature=0.7
    )
    
    # Create the chain using the new pattern
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "concept": concept,
            "matiere": matiere,
            "context": "\n".join([doc.page_content for doc in context]),
            "nombre_options": nombre_options
        })
        
        # Parse JSON response from AIMessage content
        question_data = json.loads(response.content)
        
        # Add metadata and source documents
        sources = []
        for i, doc in enumerate(context):
            source_entry = {
                "document": i + 1,
                "source": doc.metadata.get('source', 'Source inconnue'),
                "is_exam": doc.metadata.get('is_exam', False)
            }
            
            # Add section if it exists
            if "Header 2" in doc.metadata:
                source_entry["section"] = doc.metadata["Header 2"]
            elif "Header 3" in doc.metadata:
                source_entry["section"] = doc.metadata["Header 3"]
            
            # Limit content to avoid too long excerpts
            max_content_length = 250  # Characters
            content = doc.page_content
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            source_entry["contenu"] = content
            sources.append(source_entry)
        
        question_data.update({
            "matiere": matiere,
            "generated_at": datetime.now().isoformat(),
            "source_documents": sources
        })
        
        return question_data
        
    except Exception as e:
        return {
            "error": f"Failed to generate MCQ: {str(e)}",
            "status": "error"
        }

def evaluer_reponse_etudiant(
    matiere: str,
    question: Dict[str, Any],
    reponse: str
) -> Dict[str, Any]:
    """
    Evaluate a student's response to a question using RAG.
    
    Args:
        matiere: Subject identifier
        question: Question data
        reponse: Student's response
        
    Returns:
        Dict[str, Any]: Evaluation results
    """
    # Initialize RAG system
    _, index_name, embeddings, _ = initialize_rag_components()
    retrieval_chain, vector_store = setup_rag_system(
        index_name=index_name,
        embeddings=embeddings,
        matiere=matiere
    )
    
    if not retrieval_chain:
        return {
            "error": "Failed to initialize RAG system",
            "status": "error"
        }
    
    # Create evaluation prompt based on question type
    if question["type"] == "mcq":
        prompt_template = """
        Evaluate the student's response to the following multiple-choice question:
        
        Question: {question}
        Correct Answer: {correct_answer}
        Student's Response: {reponse}
        
        Generate a JSON response with the following structure:
        {{
            "is_correct": true/false,
            "score": 0-100,
            "feedback": "Detailed feedback on the response",
            "explanation": "Explanation of the correct answer"
        }}
        """
        
        correct_answer = next(
            (opt["text"] for opt in question["options"] if opt["is_correct"]),
            None
        )
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["question", "correct_answer", "reponse"]
        )
        
    else:  # reflection question
        prompt_template = """
        Vous êtes un examinateur académique automatisé spécialisé dans la matière {matiere}. 
        Votre rôle est d'évaluer la réponse d'un étudiant à une question de réflexion, en vous basant strictement sur le contenu du cours.

        Question posée: {question}
        
        Réponse de l'étudiant: {reponse}
        
        Contexte du cours (utilisez ces extraits comme référence pour évaluer la pertinence et l'exactitude des connaissances):
        {context}
        
        IMPORTANT CONCERNANT LES EXAMENS:
        Certains des documents fournis peuvent être des fichiers d'examens (identifiés par "is_exam": true dans les métadonnées).
        Si ces documents sont présents parmi les sources, vous devez:
        1. Observer attentivement le style et les critères d'évaluation utilisés par les professeurs dans ces examens
        2. Appliquer des standards d'évaluation similaires à ceux qu'un professeur utiliserait pour cette matière
        3. Tenir compte du niveau de difficulté et de précision attendu dans les examens officiels
        
        Procédez de façon rigoureuse, pédagogique et structurée selon les étapes suivantes:
        
        1. Évaluez la réponse en considérant:
           - Pertinence des idées: Les arguments répondent-ils à la question?
           - Qualité de l'argumentation: Les idées sont-elles développées et logiques?
           - Maîtrise des connaissances: L'étudiant utilise-t-il correctement les concepts du cours?
           - Originalité et pensée critique: La réponse montre-t-elle une réflexion personnelle?
           - Clarté et structure: L'expression est-elle compréhensible et organisée?
        
        2. Rédigez une réponse modèle concise mais complète
        
        3. Identifiez 3 points forts et 3 points à améliorer
        
        4. Attribuez une note sur 100 et justifiez-la. Elle doit avoir une granularité de 5 points
        
        5. Proposez un conseil personnalisé pour améliorer
        
        Votre évaluation DOIT être retournée strictement au format JSON suivant:
        
        {{
            "score": 85,
            "feedback": "Explication détaillée de la note attribuée",
            "strengths": [
                "Point fort 1",
                "Point fort 2",
                "Point fort 3"
            ],
            "areas_for_improvement": [
                "Point à améliorer 1",
                "Point à améliorer 2",
                "Point à améliorer 3"
            ],
            "suggestions": ["Un conseil spécifique pour aider l'étudiant à progresser"],
            "model_answer": "Une réponse modèle concise mais complète",
            "basé_sur_examen": true
        }}
        
        IMPORTANT:
        - Le champ "basé_sur_examen" doit être true si des documents d'examen ont influencé l'évaluation, false sinon
        - Ne mentionnez pas et n'ajoutez pas de sources dans votre réponse
        - N'incluez aucun autre champ que ceux spécifiés ci-dessus
        - Soyez rigoureux mais juste dans votre évaluation
        """
        
        # Get relevant context using RAG
        response = retrieval_chain.invoke({"input": question["concept"]})
        context = response.get("context", []) if isinstance(response, dict) else []
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["question", "reponse", "context"]
        )
    
    # Generate evaluation using LLM
    llm = ChatOpenAI(
        model_name=settings.OPENAI_MODEL,
        temperature=0.3  # Lower temperature for more consistent evaluations
    )
    
    # Create the chain using the new pattern
    chain = prompt | llm
    
    try:
        if question["type"] == "mcq":
            response = chain.invoke({
                "question": question["question"],
                "correct_answer": correct_answer,
                "reponse": reponse
            })
        else:
            response = chain.invoke({
                "matiere": matiere,
                "question": question["question"],
                "reponse": reponse,
                "context": "\n".join([doc.page_content for doc in context])
            })
        
        # Parse JSON response
        evaluation = json.loads(response.content)
        
        # Add metadata
        evaluation.update({
            "matiere": matiere,
            "question_id": question.get("id", ""),
            "evaluated_at": datetime.now().isoformat()
        })
        
        return evaluation
        
    except Exception as e:
        return {
            "error": f"Failed to evaluate response: {str(e)}",
            "status": "error"
        }

def generer_serie_questions(
    matiere: str,
    concepts: List[str],
    nombre_questions: int = 5,
    types_questions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate a series of questions covering multiple concepts.
    
    Args:
        matiere: Subject identifier
        concepts: List of concepts to cover
        nombre_questions: Number of questions to generate
        types_questions: List of question types to include (default: ["mcq", "reflection"])
        
    Returns:
        List[Dict[str, Any]]: List of generated questions
    """
    if types_questions is None:
        types_questions = ["mcq", "reflection"]
    
    questions = []
    
    # Calculate questions per concept
    questions_per_concept = nombre_questions // len(concepts)
    remaining_questions = nombre_questions % len(concepts)
    
    for concept in concepts:
        # Generate questions for this concept
        concept_questions = []
        
        # Generate MCQs if requested
        if "mcq" in types_questions:
            mcq = generer_question_qcm(matiere, concept)
            if "error" not in mcq:
                concept_questions.append(mcq)
        
        # Generate reflection questions if requested
        if "reflection" in types_questions:
            reflection = generer_question_reflexion(matiere, concept)
            if "error" not in reflection:
                concept_questions.append(reflection)
        
        # Add questions to the series
        questions.extend(concept_questions[:questions_per_concept])
    
    # Add remaining questions
    if remaining_questions > 0:
        remaining_concepts = concepts[:remaining_questions]
        for concept in remaining_concepts:
            if "mcq" in types_questions:
                mcq = generer_question_qcm(matiere, concept)
                if "error" not in mcq:
                    questions.append(mcq)
            elif "reflection" in types_questions:
                reflection = generer_question_reflexion(matiere, concept)
                if "error" not in reflection:
                    questions.append(reflection)
    
    return questions

if __name__ == "__main__":
    # Test configuration
    matiere = "SYD"
    concept = "système d'information"
    concepts = ["système d'information", "base de données", "réseaux"]
    
    print("\n=== Testing RAG Question Generation ===")
    
    try:
        # Initialize RAG system components
        print("\nInitializing RAG system...")
        initialize_rag_components()
        
        # Test 1: Generate reflection question
        print("\n1. Testing generer_question_reflexion:")
        print("-" * 50)
        question_reflexion = generer_question_reflexion(matiere, concept)
        print(json.dumps(question_reflexion, indent=2, ensure_ascii=False))
        
        # Test 2: Generate MCQ
        print("\n2. Testing generer_question_qcm:")
        print("-" * 50)
        question_qcm = generer_question_qcm(matiere, concept, nombre_options=4)
        print(json.dumps(question_qcm, indent=2, ensure_ascii=False))
        
        # Test 3: Evaluate MCQ response
        print("\n3. Testing evaluer_reponse_etudiant (MCQ):")
        print("-" * 50)
        if "error" not in question_qcm:
            reponse_mcq = "Option 1"  # Simulated student response
            evaluation_mcq = evaluer_reponse_etudiant(matiere, question_qcm, reponse_mcq)
            print(json.dumps(evaluation_mcq, indent=2, ensure_ascii=False))
        
        # Test 4: Evaluate reflection response
        print("\n4. Testing evaluer_reponse_etudiant (Reflection):")
        print("-" * 50)
        if "error" not in question_reflexion:
            reponse_reflexion = "Voici ma réponse détaillée sur le concept..."  # Simulated student response
            evaluation_reflexion = evaluer_reponse_etudiant(matiere, question_reflexion, reponse_reflexion)
            print(json.dumps(evaluation_reflexion, indent=2, ensure_ascii=False))
        
        # Test 5: Generate series of questions
        print("\n5. Testing generer_serie_questions:")
        print("-" * 50)
        questions_series = generer_serie_questions(
            matiere=matiere,
            concepts=concepts,
            nombre_questions=4,
            types_questions=["mcq", "reflection"]
        )
        print(f"Generated {len(questions_series)} questions:")
        for i, q in enumerate(questions_series, 1):
            print(f"\nQuestion {i}:")
            print(json.dumps(q, indent=2, ensure_ascii=False))
        
        print("\n=== Test Suite Completed ===")
        
    except Exception as e:
        print(f"\nError during test execution: {str(e)}")
        raise