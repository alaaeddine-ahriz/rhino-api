"""Core RAG functionality for the application."""
import os
from typing import Tuple, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain import hub

from app.core.config import settings

# Initialize Pinecone and embeddings
def initialize_pinecone() -> Tuple[Pinecone, str, ServerlessSpec]:
    """
    Initialize Pinecone connection and create index if necessary.
    
    Returns:
        Tuple[Pinecone, str, ServerlessSpec]: Pinecone client, index name, and spec
    """
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    spec = ServerlessSpec(cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION)
    
    return pc, settings.PINECONE_INDEX_NAME, spec

def setup_embeddings() -> PineconeEmbeddings:
    """
    Initialize the embedding model for text vectorization.
    
    Returns:
        PineconeEmbeddings: Configured embedding model
    """
    model_name = 'multilingual-e5-large'
    
    embeddings = PineconeEmbeddings(
        model=model_name,
        pinecone_api_key=settings.PINECONE_API_KEY
    )
    
    return embeddings

def create_or_get_index(pc: Pinecone, index_name: str, embeddings: PineconeEmbeddings, spec: ServerlessSpec) -> PineconeVectorStore:
    """
    Create a new index if needed or retrieve an existing one.
    
    Args:
        pc: Pinecone client
        index_name: Name of the index
        embeddings: Embedding model
        spec: Serverless specifications
        
    Returns:
        PineconeVectorStore: Vector store instance
    """
    if index_name not in pc.list_indexes().names():
        print(f"Creating new index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=embeddings.dimension,
            metric="cosine",
            spec=spec
        )
    
    return PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )

def setup_rag_system(
    index_name: str,
    embeddings: PineconeEmbeddings,
    matiere: str,
    custom_prompt: Optional[ChatPromptTemplate] = None,
    output_format: str = "text"
) -> Tuple[create_retrieval_chain, PineconeVectorStore]:
    """
    Configure the RAG system for a specific subject.
    
    Args:
        index_name: Name of the Pinecone index
        embeddings: Embedding model
        matiere: Subject identifier
        custom_prompt: Optional custom prompt template
        output_format: Output format ("text" or "json")
        
    Returns:
        Tuple[create_retrieval_chain, PineconeVectorStore]: Retrieval chain and vector store
    """
    namespace = f"matiere-{matiere.lower()}"
    
    # Create vector store for this subject
    vector_store = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        namespace=namespace
    )
    
    # Configure the prompt
    if custom_prompt:
        retrieval_qa_chat_prompt = custom_prompt
    elif output_format == "json":
        retrieval_qa_chat_prompt = create_json_prompt(matiere)
    else:
        retrieval_qa_chat_prompt = hub.pull("langchain-ai/retrieval-qa-chat")
    
    # Configure retriever
    retriever = vector_store.as_retriever()
    
    # Configure language model
    llm = ChatOpenAI(
        openai_api_key=settings.OPENAI_API_KEY,
        model_name='gpt-4',
        temperature=0.0
    )
    
    # Create document processing chain
    combine_docs_chain = create_stuff_documents_chain(llm, retrieval_qa_chat_prompt)
    
    # Create retrieval chain
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)
    
    return retrieval_chain, vector_store

def create_json_prompt(matiere: str) -> ChatPromptTemplate:
    """
    Create a custom prompt for generating JSON responses.
    
    Args:
        matiere: Subject identifier
        
    Returns:
        ChatPromptTemplate: Configured prompt template
    """
    TEMPLATE_JSON = """
    You are an educational AI assistant specialized in {matiere}, with direct access to course documents via a semantic search system (RAG).

    Based on the following course excerpts:
    {context}
    
    Answer this question: {input}
    
    Your response MUST be in the following JSON format, WITHOUT sources (I'll add the sources myself):
    
    ```json
    {{
        "response": "The complete answer to the question",
        "confidence_level": 0.95
    }}
    ```
    
    OPTIONAL FIELDS:
    - If relevant, you can add a "key_concepts": ["concept1", "concept2", "concept3"] field
    - This field is OPTIONAL and should only be included if you can clearly identify key concepts
    
    IMPORTANT:
    - Do not mention or add sources in your response
    - Focus primarily on the answer
    - Only include the fields specified above
    
    Respond only with this JSON format, without any text before or after.
    """
    
    return ChatPromptTemplate.from_template(TEMPLATE_JSON).partial(matiere=matiere)
