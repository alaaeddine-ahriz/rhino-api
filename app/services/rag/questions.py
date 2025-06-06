"""Question generation and evaluation using RAG system."""
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from langchain.schema import Document
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

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
    Based on the following context about {concept_cle} in {matiere},
    generate a thought-provoking reflection question that:
    1. Tests deep understanding of the concept
    2. Encourages critical thinking
    3. Relates to real-world applications
    
    Context:
    {context}
    
    Generate a JSON response with the following structure:
    {{
        "question": "The reflection question",
        "concept": "{concept_cle}",
        "difficulty": "medium",
        "type": "reflection",
        "hints": [
            "First hint to guide the student",
            "Second hint if needed"
        ]
    }}
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["concept_cle", "matiere", "context"]
    )
    
    # Get relevant context using RAG
    response = retrieval_chain.invoke({"input": concept_cle})
    context = response["context"] if isinstance(response, dict) else str(response)
    
    # Generate question using LLM
    llm = ChatOpenAI(
        model_name=settings.OPENAI_MODEL,
        temperature=0.7
    )
    
    # Create the chain using the new pattern
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "concept_cle": concept_cle,
            "matiere": matiere,
            "context": context
        })
        
        # Parse JSON response
        question_data = json.loads(response.content)
        
        # Add metadata
        question_data.update({
            "matiere": matiere,
            "generated_at": datetime.now().isoformat(),
            "source_documents": []
        })
        
        return question_data
        
    except Exception as e:
        return {
            "error": f"Failed to generate question: {str(e)}",
            "status": "error"
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
    Based on the following context about {concept} in {matiere},
    generate a multiple-choice question with {nombre_options} options.
    The question should:
    1. Test understanding of key concepts
    2. Have one correct answer
    3. Have plausible distractors
    
    Context:
    {context}
    
    Generate a JSON response with the following structure:
    {{
        "question": "The multiple-choice question",
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
        "explanation": "Explanation of the correct answer"
    }}
    """
    
    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["concept", "matiere", "context", "nombre_options"]
    )
    
    # Get relevant context using RAG
    response = retrieval_chain.invoke({"input": concept})
    context = response["context"] if isinstance(response, dict) else str(response)
    
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
            "context": context,
            "nombre_options": nombre_options
        })
        
        # Parse JSON response
        question_data = json.loads(response.content)
        
        # Add metadata
        question_data.update({
            "matiere": matiere,
            "generated_at": datetime.now().isoformat(),
            "source_documents": []
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
        Evaluate the student's response to the following reflection question:
        
        Question: {question}
        Student's Response: {reponse}
        
        Consider the following context:
        {context}
        
        Generate a JSON response with the following structure:
        {{
            "score": 0-100,
            "feedback": "Detailed feedback on the response",
            "strengths": ["List of strengths in the response"],
            "areas_for_improvement": ["List of areas that need improvement"],
            "suggestions": ["Suggestions for better understanding"]
        }}
        """
        
        # Get relevant context using RAG
        response = retrieval_chain.invoke({"input": question["concept"]})
        context = response["context"] if isinstance(response, dict) else str(response)
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["question", "reponse", "context"]
        )
    
    # Generate evaluation using LLM
    llm = ChatOpenAI(
        model_name=settings.OPENAI_MODEL,
        temperature=0.3  # Lower temperature for more consistent evaluations
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        if question["type"] == "mcq":
            response = chain.run(
                question=question["question"],
                correct_answer=correct_answer,
                reponse=reponse
            )
        else:
            response = chain.run(
                question=question["question"],
                reponse=reponse,
                context=context
            )
        
        # Parse JSON response
        evaluation = json.loads(response)
        
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