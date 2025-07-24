#!/usr/bin/env python3
"""
Knowledge Assistant using LLM with ChromaDB embeddings.
This script:
1. Takes a user question
2. Retrieves relevant document chunks from ChromaDB using semantic search
3. Sends the chunks as context to a Vertex AI LLM
4. Returns the LLM's answer based on the retrieved context
"""

import os
import sys
import argparse
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('knowledge_assistant.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the test_embeddings_simple module for ChromaDB search
from test_embeddings_simple import search_chroma, get_database_info

# Initialize Vertex AI
try:
    from google.cloud import aiplatform
    # Initialize with project and location
    aiplatform.init(project="30211686184", location="us-central1")
    logger.info("Initialized Vertex AI with project ID: 30211686184")
except ImportError:
    logger.error("Google Cloud AI Platform not found. Install with: pip install google-cloud-aiplatform")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error initializing Vertex AI: {e}")
    sys.exit(1)

# Import Vertex AI models - try both paths for compatibility
gemini_available = False
text_model_available = False

# Try to import text models first (these are more reliable)
try:
    import vertexai
    from vertexai.language_models import TextGenerationModel
    text_model_available = True
    logger.info("Text generation models available")
except ImportError:
    logger.warning("Text generation models not available")

# Try to import Gemini models
try:
    try:
        # Try the preview path first
        from vertexai.preview.generative_models import GenerativeModel
        gemini_available = True
        logger.info("Using preview generative models")
    except ImportError:
        # Try the stable path
        from vertexai.generative_models import GenerativeModel
        gemini_available = True
        logger.info("Using stable generative models")
except ImportError:
    logger.warning("Vertex AI generative models not available")
    
if not gemini_available and not text_model_available:
    logger.error("Neither generative models nor text models are available")
    logger.error("Install with: pip install google-cloud-aiplatform")
    sys.exit(1)

def format_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Format the retrieved chunks into a context string for the LLM.
    
    Args:
        chunks: List of document chunks with content and metadata
        
    Returns:
        Formatted context string
    """
    if not chunks:
        return "No relevant information found."
    
    context_parts = []
    for i, chunk in enumerate(chunks):
        source = chunk.get('filename', 'Unknown source')
        content = chunk.get('chunk_content', '')
        doc_type = chunk.get('doc_type', 'Unknown type')
        tags = chunk.get('tags', [])
        
        context_part = f"[Document {i+1}] {source} (Type: {doc_type})\n"
        if tags:
            context_part += f"Tags: {', '.join(tags)}\n"
        context_part += f"Content: {content}"
        
        context_parts.append(context_part)
    
    return "\n\n---\n\n".join(context_parts)

def query_llm(question: str, context: str, model_name: str = "text-bison") -> str:
    """
    Query the LLM with the user's question and retrieved context.
    
    Args:
        question: User's question
        context: Context information from retrieved chunks
        model_name: Name of the Vertex AI model to use
        
    Returns:
        LLM's response
    """
    # Create prompt with context and question
    prompt = f"""
You are a helpful knowledge assistant that answers questions based only on the provided context information.
If the context doesn't contain relevant information to answer the question, admit that you don't know
rather than making up an answer. Use only the information in the context to answer the question.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""
    
    try:
        # Fix model name format - remove any version suffix with @ symbol
        if '@' in model_name:
            base_model_name = model_name.split('@')[0]
            logger.info(f"Converting model name from {model_name} to {base_model_name}")
            model_name = base_model_name
            
        # Check if model name is a Gemini model
        if model_name.startswith("gemini") and gemini_available:
            logger.info(f"Using Gemini model: {model_name}")
            model = GenerativeModel(model_name)
            response = model.generate_content(prompt, generation_config={
                "max_output_tokens": 1024,
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40
            })
            return response.text
        
        # If not Gemini or Gemini not available, try text model
        elif text_model_available:
            # Convert Gemini model name to text model if needed
            if model_name.startswith("gemini"):
                logger.info(f"Gemini model {model_name} requested but using text-bison instead")
                model_name = "text-bison"
            
            logger.info(f"Using text generation model: {model_name}")
            model = TextGenerationModel.from_pretrained(model_name)
            response = model.predict(
                prompt,
                temperature=0.2,
                max_output_tokens=1024,
                top_k=40,
                top_p=0.8,
            )
            return response.text
        
        else:
            return "Error: No suitable model available. Please install Vertex AI SDK."
    
    except Exception as e:
        logger.error(f"Error querying LLM: {e}", exc_info=True)
        error_msg = str(e)
        
        # If we get a 404 error, try a different model format
        if "404" in error_msg and text_model_available:
            logger.info(f"Falling back to text-bison after error with {model_name}")
            try:
                # Try without version number
                model = TextGenerationModel.from_pretrained("text-bison")
                response = model.predict(
                    prompt,
                    temperature=0.2,
                    max_output_tokens=1024,
                    top_k=40,
                    top_p=0.8,
                )
                return response.text
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return f"Error with {model_name}, and fallback to text-bison also failed: {str(fallback_error)}"
        
        return f"Error generating response: {error_msg}"

def main():
    """Main function for the knowledge assistant."""
    parser = argparse.ArgumentParser(description="Knowledge Assistant using LLM with ChromaDB")
    parser.add_argument("--question", type=str, help="Question to ask")
    parser.add_argument("--num-chunks", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument("--show-context", action="store_true", help="Show retrieved context")
    parser.add_argument("--db-path", type=str, default="./knowledgebase.db", help="Path to SQLite database")
    parser.add_argument("--chroma-dir", type=str, default="./chroma_db_data", help="Path to ChromaDB directory")
    parser.add_argument("--collection", type=str, default="vertex_ai_embeddings", help="ChromaDB collection name")
    parser.add_argument("--model", type=str, default="text-bison", 
                       help="Model to use (e.g., text-bison, gemini-pro)")
    args = parser.parse_args()
    
    # Get question from arguments or prompt the user
    question = args.question
    if not question:
        question = input("Enter your question: ")
    
    logger.info(f"Question: {question}")
    
    # Get database info
    db_info = get_database_info(args.db_path)
    logger.info(f"Database has {db_info['total_chunks']} chunks, {db_info['embedded_chunks']} with embeddings")
    
    # Search ChromaDB for relevant chunks
    logger.info(f"Searching for relevant chunks using {args.collection} collection")
    results = search_chroma(
        query=question,
        collection_name=args.collection,
        persist_directory=args.chroma_dir,
        num_results=args.num_chunks,
        db_path=args.db_path
    )
    
    if not results:
        print("No relevant information found.")
        return
    
    logger.info(f"Found {len(results)} relevant chunks")
    
    # Format context for LLM
    context = format_context(results)
    
    # Show context if requested
    if args.show_context:
        print("\n=== CONTEXT ===\n")
        print(context)
        print("\n=== END CONTEXT ===\n")
    
    # Query LLM
    logger.info(f"Querying LLM with model: {args.model}")
    answer = query_llm(question, context, args.model)
    
    # Print answer
    print("\n=== ANSWER ===\n")
    print(answer)
    print("\n=== END ANSWER ===\n")

if __name__ == "__main__":
    main()
