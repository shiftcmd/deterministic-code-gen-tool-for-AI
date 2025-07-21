#!/usr/bin/env python3
"""
Supabase Knowledge Assistant

This script adapts the existing knowledge assistant examples to use Supabase as both
the vector database and LLM provider. It:
1. Takes a user question
2. Searches for relevant document chunks in Supabase using vector similarity
3. Uses Supabase Edge Functions or integrates with AI services for response generation
4. Returns contextual answers based on the retrieved information

Features:
- Uses Supabase for vector storage and similarity search
- Supports multiple document types and metadata
- Configurable through environment variables
- Comprehensive logging and error handling
"""

import os
import sys
import argparse
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('supabase_knowledge_assistant.log')
    ]
)
logger = logging.getLogger(__name__)

# Import Supabase client
try:
    from supabase import create_client, Client
    logger.info("Supabase client imported successfully")
except ImportError:
    logger.error("Supabase package not found. Install with: pip install supabase")
    sys.exit(1)

# Import OpenAI for LLM functionality as fallback/complement to Supabase
try:
    import openai
    from openai import OpenAI
    openai_available = True
    logger.info("OpenAI client available")
except ImportError:
    openai_available = False
    logger.warning("OpenAI not available - will use basic Supabase functionality only")

class SupabaseKnowledgeAssistant:
    """
    Knowledge Assistant using Supabase for vector storage and document retrieval.
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        table_name: str = "documents",
        embedding_table: str = "document_embeddings",
        similarity_threshold: float = 0.7,
        max_chunks: int = 10
    ):
        """
        Initialize the Supabase Knowledge Assistant.
        
        Args:
            supabase_url: Supabase project URL (defaults to env var)
            supabase_key: Supabase service key (defaults to env var)
            openai_api_key: OpenAI API key for LLM responses (defaults to env var)
            table_name: Name of the documents table
            embedding_table: Name of the embeddings table
            similarity_threshold: Minimum similarity score for relevant chunks
            max_chunks: Maximum number of chunks to retrieve
        """
        # Initialize Supabase connection
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Service Key are required. Check your .env file.")
        
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            logger.info(f"Connected to Supabase at {self.supabase_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
        
        # Initialize OpenAI client if available and key provided
        self.openai_client = None
        if openai_available:
            self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if self.openai_api_key:
                try:
                    self.openai_client = OpenAI(api_key=self.openai_api_key)
                    logger.info("OpenAI client initialized for LLM responses")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Configuration
        self.table_name = table_name
        self.embedding_table = embedding_table
        self.similarity_threshold = similarity_threshold
        self.max_chunks = max_chunks
        
        # Verify database tables exist
        self._verify_database_setup()
    
    def _verify_database_setup(self) -> bool:
        """
        Verify that required database tables exist.
        
        Returns:
            True if tables exist, False otherwise
        """
        try:
            # Check if documents table exists
            result = self.supabase.table(self.table_name).select("id").limit(1).execute()
            logger.info(f"Documents table '{self.table_name}' verified")
            
            # Check if embeddings table exists
            result = self.supabase.table(self.embedding_table).select("id").limit(1).execute()
            logger.info(f"Embeddings table '{self.embedding_table}' verified")
            
            return True
        except Exception as e:
            logger.warning(f"Database table verification failed: {e}")
            logger.info("You may need to set up the database schema first")
            return False
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding for the given text using OpenAI or Supabase.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Failed to create embedding with OpenAI: {e}")
        
        # Fallback: Use Supabase edge function or return empty list
        logger.warning("No embedding service available - using basic text search")
        return []
    
    def search_knowledge_base(
        self,
        query: str,
        num_results: int = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant document chunks.
        
        Args:
            query: Search query
            num_results: Number of results to return (defaults to max_chunks)
            include_metadata: Whether to include document metadata
            
        Returns:
            List of relevant document chunks with metadata
        """
        if num_results is None:
            num_results = self.max_chunks
        
        try:
            # Try vector similarity search if embeddings are available
            query_embedding = self.create_embedding(query)
            
            if query_embedding:
                # Use RPC function for vector similarity search
                results = self.supabase.rpc(
                    'search_documents',
                    {
                        'query_embedding': query_embedding,
                        'similarity_threshold': self.similarity_threshold,
                        'match_count': num_results
                    }
                ).execute()
                
                if results.data:
                    logger.info(f"Found {len(results.data)} similar documents using vector search")
                    return results.data
            
            # Fallback to text search
            logger.info("Using text search fallback")
            results = self.supabase.table(self.table_name).select(
                "id, content, metadata, created_at, title, document_type"
            ).or_(
                f"content.ilike.%{query}%,title.ilike.%{query}%"
            ).limit(num_results).execute()
            
            if results.data:
                logger.info(f"Found {len(results.data)} documents using text search")
                return results.data
            else:
                logger.info("No relevant documents found")
                return []
                
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
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
            title = chunk.get('title', f'Document {i+1}')
            content = chunk.get('content', '')
            doc_type = chunk.get('document_type', 'Unknown')
            metadata = chunk.get('metadata', {})
            
            context_part = f"[{title}] (Type: {doc_type})\n"
            
            # Add relevant metadata
            if isinstance(metadata, dict):
                if 'tags' in metadata:
                    context_part += f"Tags: {', '.join(metadata['tags'])}\n"
                if 'source' in metadata:
                    context_part += f"Source: {metadata['source']}\n"
            
            context_part += f"Content: {content}"
            context_parts.append(context_part)
        
        return "\n\n---\n\n".join(context_parts)
    
    def generate_response(
        self,
        question: str,
        context: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a response using the LLM with the provided context.
        
        Args:
            question: User's question
            context: Context information from retrieved chunks
            model: LLM model to use
            temperature: Response creativity (0.0-1.0)
            max_tokens: Maximum response length
            
        Returns:
            Generated response
        """
        if not self.openai_client:
            return f"""
Based on the available information:

{context}

---

Note: This is a basic response using retrieved context only. 
For AI-generated responses, please configure OpenAI API key.

Your question was: {question}
"""
        
        # Create prompt for the LLM
        prompt = f"""You are a helpful knowledge assistant that answers questions based only on the provided context information.

If the context doesn't contain enough information to answer the question completely, acknowledge what you don't know and suggest what additional information might be helpful.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a knowledgeable assistant that provides accurate answers based on context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating AI response: {str(e)}\n\nContext was:\n{context}"
    
    def ask_question(
        self,
        question: str,
        num_chunks: int = None,
        show_context: bool = False,
        model: str = "gpt-3.5-turbo"
    ) -> Dict[str, Any]:
        """
        Ask a question and get a comprehensive response.
        
        Args:
            question: User's question
            num_chunks: Number of chunks to retrieve
            show_context: Whether to include context in response
            model: LLM model to use
            
        Returns:
            Dictionary with answer, context, and metadata
        """
        logger.info(f"Processing question: {question}")
        
        # Search for relevant information
        chunks = self.search_knowledge_base(question, num_chunks)
        
        # Format context
        context = self.format_context(chunks)
        
        # Generate response
        answer = self.generate_response(question, context, model)
        
        # Prepare response
        response = {
            "question": question,
            "answer": answer,
            "num_chunks_found": len(chunks),
            "timestamp": datetime.now().isoformat()
        }
        
        if show_context:
            response["context"] = context
            response["chunks"] = chunks
        
        return response
    
    def add_document(
        self,
        content: str,
        title: str,
        document_type: str = "text",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a document to the knowledge base.
        
        Args:
            content: Document content
            title: Document title
            document_type: Type of document
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Insert document
            doc_data = {
                "title": title,
                "content": content,
                "document_type": document_type,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat()
            }
            
            result = self.supabase.table(self.table_name).insert(doc_data).execute()
            
            if result.data:
                doc_id = result.data[0]["id"]
                logger.info(f"Document '{title}' added with ID: {doc_id}")
                
                # Create and store embedding if possible
                embedding = self.create_embedding(content)
                if embedding:
                    embedding_data = {
                        "document_id": doc_id,
                        "embedding": embedding
                    }
                    self.supabase.table(self.embedding_table).insert(embedding_data).execute()
                    logger.info(f"Embedding created for document {doc_id}")
                
                return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the knowledge base.
        
        Returns:
            Database statistics and information
        """
        try:
            # Count documents
            docs_result = self.supabase.table(self.table_name).select("id", count="exact").execute()
            doc_count = docs_result.count
            
            # Count embeddings
            emb_result = self.supabase.table(self.embedding_table).select("id", count="exact").execute()
            emb_count = emb_result.count
            
            # Get document types
            types_result = self.supabase.table(self.table_name).select("document_type").execute()
            doc_types = list(set([doc.get("document_type", "unknown") for doc in types_result.data]))
            
            return {
                "total_documents": doc_count,
                "total_embeddings": emb_count,
                "document_types": doc_types,
                "database_url": self.supabase_url,
                "embedding_model": "text-embedding-3-small" if self.openai_client else "none",
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}


def main():
    """Main function for the Supabase Knowledge Assistant."""
    parser = argparse.ArgumentParser(description="Supabase Knowledge Assistant")
    parser.add_argument("--question", type=str, help="Question to ask")
    parser.add_argument("--num-chunks", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument("--show-context", action="store_true", help="Show retrieved context")
    parser.add_argument("--show-info", action="store_true", help="Show database information")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo", help="LLM model to use")
    parser.add_argument("--add-document", action="store_true", help="Add a document to the knowledge base")
    parser.add_argument("--doc-title", type=str, help="Title for new document")
    parser.add_argument("--doc-content", type=str, help="Content for new document")
    parser.add_argument("--doc-type", type=str, default="text", help="Type of new document")
    
    args = parser.parse_args()
    
    try:
        # Initialize the assistant
        assistant = SupabaseKnowledgeAssistant()
        
        # Show database info if requested
        if args.show_info:
            info = assistant.get_database_info()
            print("\n=== DATABASE INFO ===")
            print(json.dumps(info, indent=2))
            print("======================\n")
        
        # Add document if requested
        if args.add_document:
            if not args.doc_title or not args.doc_content:
                print("Error: --doc-title and --doc-content are required when adding a document")
                return
            
            success = assistant.add_document(
                content=args.doc_content,
                title=args.doc_title,
                document_type=args.doc_type
            )
            
            if success:
                print(f"Successfully added document: {args.doc_title}")
            else:
                print("Failed to add document")
            return
        
        # Get question from arguments or prompt the user
        question = args.question
        if not question:
            question = input("Enter your question: ")
        
        if not question.strip():
            print("No question provided.")
            return
        
        print(f"\n=== QUESTION ===")
        print(question)
        print("================\n")
        
        # Ask the question
        response = assistant.ask_question(
            question=question,
            num_chunks=args.num_chunks,
            show_context=args.show_context,
            model=args.model
        )
        
        # Display results
        print("=== ANSWER ===")
        print(response["answer"])
        print("==============\n")
        
        print(f"Found {response['num_chunks_found']} relevant chunks")
        print(f"Response generated at: {response['timestamp']}")
        
        if args.show_context and "context" in response:
            print("\n=== CONTEXT ===")
            print(response["context"])
            print("===============\n")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
