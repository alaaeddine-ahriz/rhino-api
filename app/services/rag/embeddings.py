"""Embeddings and vector operations for RAG system."""
from typing import List, Dict, Any
from langchain_pinecone import PineconeEmbeddings, PineconeVectorStore
from langchain.schema import Document
from pinecone import Pinecone

from app.core.config import settings
from app.services.rag.core import setup_embeddings

def get_matiere_namespace(matiere: str) -> str:
    """
    Generate a standardized namespace for a subject.
    
    Args:
        matiere: Subject identifier
        
    Returns:
        str: Standardized namespace
    """
    return f"matiere-{matiere.lower()}"

def upsert_documents(
    pc: Pinecone,
    index_name: str,
    embeddings: PineconeEmbeddings,
    matiere: str,
    docs: List[Document]
) -> tuple[PineconeVectorStore, str]:
    """
    Update the vector index with new or modified documents.
    
    Args:
        pc: Pinecone client
        index_name: Name of the index
        embeddings: Embedding model
        matiere: Subject identifier
        docs: List of document sections
        
    Returns:
        tuple[PineconeVectorStore, str]: Vector store and namespace used
    """
    if not docs:
        print(f"No documents to insert for subject {matiere}")
        return None, None
    
    namespace = get_matiere_namespace(matiere)
    
    try:
        print(f"Inserting {len(docs)} document sections into namespace '{namespace}'")
        vector_store = PineconeVectorStore.from_documents(
            documents=docs,
            index_name=index_name,
            embedding=embeddings,
            namespace=namespace
        )
        print("Insertion successful")
        return vector_store, namespace
    except Exception as e:
        print(f"Error during insertion: {e}")
        return None, None

def delete_documents(
    pc: Pinecone,
    index_name: str,
    matiere: str,
    file_paths: List[str]
) -> bool:
    """
    Delete documents from the vector index for files that have been removed.
    
    Args:
        pc: Pinecone client
        index_name: Name of the index
        matiere: Subject identifier
        file_paths: List of file paths to delete
        
    Returns:
        bool: True if deletions were performed, False otherwise
    """
    if not file_paths:
        return False
    
    namespace = get_matiere_namespace(matiere)
    
    try:
        index = pc.Index(index_name)
        deleted_count = 0
        
        # Get index information for debugging
        try:
            index_stats = index.describe_index_stats()
            print(f"Index '{index_name}' statistics:")
            print(f"- Dimension: {index_stats.dimension}")
            print(f"- Total vectors: {index_stats.total_vector_count}")
            
            # Show namespace information if available
            if hasattr(index_stats, 'namespaces') and namespace in index_stats.namespaces:
                ns_stats = index_stats.namespaces[namespace]
                print(f"- Namespace '{namespace}': {ns_stats.vector_count} vectors")
                
            # Get vector dimension for query
            dimension = index_stats.dimension
        except Exception as stats_error:
            print(f"Could not get index statistics: {stats_error}")
            dimension = 1024  # Default dimension
        
        # Process each file to delete
        for file_path in file_paths:
            print(f"\nDeleting vectors for: {file_path}")
            
            # Step 1: Identify vectors by query
            try:
                # Create a zero vector for query
                zero_vector = [0.0] * dimension
                
                # Execute query with large number of results
                print("1. Searching for vectors to delete...")
                query_results = index.query(
                    namespace=namespace,
                    vector=zero_vector,
                    top_k=1000,  # Increase if needed
                    include_metadata=True
                )
                
                # Prepare list of IDs to delete
                ids_to_delete = []
                
                # Check query results
                if hasattr(query_results, 'matches') and query_results.matches:
                    print(f"   Found vectors: {len(query_results.matches)}")
                    
                    # Identify vectors matching the deleted file
                    for match in query_results.matches:
                        if hasattr(match, 'metadata') and match.metadata:
                            if 'source' in match.metadata and match.metadata['source'] == file_path:
                                ids_to_delete.append(match.id)
                                # Show example for confirmation
                                if len(ids_to_delete) == 1:
                                    print(f"   Example metadata found: {match.metadata}")
                
                # Step 2: Delete identified vectors
                if ids_to_delete:
                    print(f"2. Deleting {len(ids_to_delete)} vectors...")
                    
                    # Delete in batches to avoid API limitations
                    batch_size = 100
                    for i in range(0, len(ids_to_delete), batch_size):
                        batch = ids_to_delete[i:i+batch_size]
                        delete_result = index.delete(
                            ids=batch,
                            namespace=namespace
                        )
                        
                        if hasattr(delete_result, 'deleted_count'):
                            print(f"   Batch {i//batch_size + 1}: {delete_result.deleted_count} vectors deleted")
                        else:
                            print(f"   Batch {i//batch_size + 1}: deletion completed")
                    
                    deleted_count += len(ids_to_delete)
                    print(f"✅ {len(ids_to_delete)} vectors deleted for {file_path}")
                else:
                    print(f"❌ No vectors found with source={file_path}")
                    
                    # Show sample metadata for debugging
                    if hasattr(query_results, 'matches') and query_results.matches:
                        print("Sample metadata in index (for debugging):")
                        samples_shown = 0
                        for match in query_results.matches:
                            if hasattr(match, 'metadata') and match.metadata and samples_shown < 3:
                                print(f"- ID: {match.id}")
                                for key, value in match.metadata.items():
                                    print(f"  {key}: {value}")
                                samples_shown += 1
                                print()
                
            except Exception as e:
                print(f"Error during search/deletion for {file_path}: {e}")
        
        # Summarize results
        if deleted_count > 0:
            print(f"\n✅ Total: {deleted_count} vectors deleted for {len(file_paths)} files")
            return True
        else:
            print(f"\n❌ No vectors could be deleted for the specified files")
            return False
            
    except Exception as e:
        print(f"General error during document deletion: {e}")
        return False
