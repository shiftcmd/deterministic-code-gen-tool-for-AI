#!/usr/bin/env python3
"""
Script to query the knowledge base using an LLM.
This script:
1. Takes a user query
2. Retrieves relevant chunks from ChromaDB using embeddings
3. Sends the chunks and query to a language model
4. Returns the LLM's response based on the retrieved information
"""

import argparse
import logging
import os
import sys
import json
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('llm_query.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the test_embeddings module for searching the knowledge base
from test_embeddings import search_knowledge_base, get_document_info
from utils import config_manager

# Import Google Vertex AI for LLM
try:
    from langchain_google_vertexai import VertexAI
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError:
    logger.error("Required packages not found. Install with: pip install langchain langchain-google-vertexai")
    sys.exit(1)

def format_chunks_for_llm(chunks: List[Dict[str, Any]]) -> str:
    """
    Format retrieved chunks into a context string for the LLM.
    
    Args:
        chunks: List of chunk dictionaries with content and metadata
        
    Returns:
        Formatted context string
    """
    if not chunks:
        return "No relevant information found."
    
    context_parts = []
    for i, chunk in enumerate(chunks):
        # Format each chunk with its source and content
        chunk_text = f"[Document: {chunk.get('original_filename', 'Unknown')}]\n"
        chunk_text += f"{chunk.get('chunk_content', 'No content available')}\n"
        context_parts.append(chunk_text)
    
    return "\n---\n".join(context_parts)

def query_llm(config: Dict[str, Any], query: str, context: str) -> str:
    """
    Query the language model with the user's question and retrieved context.
    
    Args:
        config: Application configuration
        query: User's query
        context: Context information from retrieved chunks
        
    Returns:
        LLM's response
    """
    # Get Vertex AI settings from config
    vertex_project_id = config.get("embedding", {}).get("vertex_project_id", "30211686184")
    vertex_location = config.get("embedding", {}).get("vertex_location", "us-central1")
    
    try:
        # Initialize the Vertex AI model
        llm = VertexAI(
            project=vertex_project_id,
            location=vertex_location,
            model_name="gemini-1.0-pro",
            max_output_tokens=1024,
            temperature=0.1,
            top_p=0.8,
            top_k=40
        )
        
        # Create a prompt template
        template = """
        You are a helpful assistant that answers questions based on the provided context information.
        If the context doesn't contain relevant information to answer the question, admit that you don't know
        rather than making up an answer. Use only the information in the context to answer the question.
        
        CONTEXT:
        {context}
        
        QUESTION:
        {question}
        
        ANSWER:
        """
        
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=template
        )
        
        # Create and run the chain
        chain = LLMChain(llm=llm, prompt=prompt)
        response = chain.run(context=context, question=query)
        
        return response.strip()
    
    except Exception as e:
        logger.error(f"Error querying LLM: {e}", exc_info=True)
        return f"Error generating response: {str(e)}"

def main():
    """Main function to query the knowledge base with an LLM."""
    parser = argparse.ArgumentParser(description="Query the knowledge base using an LLM")
    parser.add_argument("--query", type=str, help="Query to search for")
    parser.add_argument("--num-results", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument("--show-context", action="store_true", help="Show the context sent to the LLM")
    args = parser.parse_args()
    
    # Load configuration
    config_path = "config.yaml"
    config = config_manager.load_config(config_path)
    if not config:
        logger.error(f"Failed to load configuration from {config_path}")
        return
    
    # Get query from arguments or prompt the user
    query = args.query
    if not query:
        query = input("Enter your question: ")
    
    print(f"\n===== QUERY: '{query}' =====\n")
    
    # Search the knowledge base
    logger.info(f"Searching knowledge base for: {query}")
    chunks = search_knowledge_base(config, query, args.num_results)
    
    if not chunks:
        print("No relevant information found in the knowledge base.")
        return
    
    # Format chunks for the LLM
    context = format_chunks_for_llm(chunks)
    
    # Show context if requested
    if args.show_context:
        print("\n===== CONTEXT SENT TO LLM =====\n")
        print(context)
        print("\n" + "=" * 50 + "\n")
    
    # Query the LLM
    logger.info("Querying language model")
    response = query_llm(config, query, context)
    
    # Display the response
    print("\n===== LLM RESPONSE =====\n")
    print(response)
    print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    main()
