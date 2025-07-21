#!/usr/bin/env python3
"""
Project Knowledge Assistant - Read-only version

This assistant searches through the existing crawled pages, code examples, 
and sources in the Supabase database to answer questions about the codebase.
It uses vector similarity search and text search on existing data.
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('project_knowledge_assistant.log')
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

# Import OpenAI for embeddings
try:
    import openai
    from openai import OpenAI
    openai_available = True
    logger.info("OpenAI client available")
except ImportError:
    openai_available = False
    logger.warning("OpenAI not available - will use text search only")

class ProjectKnowledgeAssistant:
    """
    Read-only Knowledge Assistant for project data in Supabase.
    Searches crawled_pages, code_examples, and sources tables.
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        similarity_threshold: float = 0.7,
        max_chunks: int = 10
    ):
        """
        Initialize the Project Knowledge Assistant.
        
        Args:
            supabase_url: Supabase project URL (defaults to env var)
            supabase_key: Supabase service key (defaults to env var)
            openai_api_key: OpenAI API key for embeddings (defaults to env var)
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
                    logger.info("OpenAI client initialized for embeddings")
                except Exception as e:
                    logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Configuration
        self.similarity_threshold = similarity_threshold
        self.max_chunks = max_chunks
        
        logger.info("Project Knowledge Assistant initialized successfully")
    
    def create_embedding(self, text: str) -> List[float]:
        """Create an embedding for the given text using OpenAI."""
        if self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Failed to create embedding: {e}")
        return []
    
    def search_crawled_pages(
        self,
        query: str,
        num_results: int = None,
        use_embeddings: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search crawled pages for relevant content.
        
        Args:
            query: Search query
            num_results: Number of results to return
            use_embeddings: Whether to try vector search first
            
        Returns:
            List of relevant crawled page chunks
        """
        if num_results is None:
            num_results = self.max_chunks
        
        try:
            # Try vector similarity search if embeddings are available
            if use_embeddings:
                query_embedding = self.create_embedding(query)
                
                if query_embedding:
                    # Use existing vector search function if available
                    try:
                        results = self.supabase.rpc(
                            'match_crawled_pages',
                            {
                                'filter': {},
                                'match_count': num_results,
                                'query_embedding': query_embedding,
                                'source_filter': None
                            }
                        ).execute()
                        
                        if results.data:
                            logger.info(f"Found {len(results.data)} similar crawled pages using vector search")
                            return results.data
                    except Exception as e:
                        logger.info(f"Vector search not available: {e}")
            
            # Fallback to text search
            logger.info("Using text search on crawled_pages")
            results = self.supabase.table('crawled_pages').select(
                "id, url, content, metadata, source_id, created_at, chunk_number"
            ).or_(
                f"content.ilike.%{query}%,url.ilike.%{query}%"
            ).limit(num_results).execute()
            
            if results.data:
                logger.info(f"Found {len(results.data)} crawled pages using text search")
                return results.data
            else:
                logger.info("No relevant crawled pages found")
                return []
                
        except Exception as e:
            logger.error(f"Error searching crawled pages: {e}")
            return []
    
    def search_code_examples(
        self,
        query: str,
        num_results: int = None,
        use_embeddings: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search code examples for relevant content.
        
        Args:
            query: Search query
            num_results: Number of results to return
            use_embeddings: Whether to try vector search first
            
        Returns:
            List of relevant code example chunks
        """
        if num_results is None:
            num_results = self.max_chunks
        
        try:
            # Try vector similarity search if embeddings are available
            if use_embeddings:
                query_embedding = self.create_embedding(query)
                
                if query_embedding:
                    try:
                        results = self.supabase.rpc(
                            'match_code_examples',
                            {
                                'filter': {},
                                'match_count': num_results,
                                'query_embedding': query_embedding,
                                'source_filter': None
                            }
                        ).execute()
                        
                        if results.data:
                            logger.info(f"Found {len(results.data)} similar code examples using vector search")
                            return results.data
                    except Exception as e:
                        logger.info(f"Vector search not available for code examples: {e}")
            
            # Fallback to text search
            logger.info("Using text search on code_examples")
            results = self.supabase.table('code_examples').select(
                "id, url, content, summary, metadata, source_id, created_at, chunk_number"
            ).or_(
                f"content.ilike.%{query}%,summary.ilike.%{query}%,url.ilike.%{query}%"
            ).limit(num_results).execute()
            
            if results.data:
                logger.info(f"Found {len(results.data)} code examples using text search")
                return results.data
            else:
                logger.info("No relevant code examples found")
                return []
                
        except Exception as e:
            logger.error(f"Error searching code examples: {e}")
            return []
    
    def search_all_sources(
        self,
        query: str,
        num_results: int = None,
        include_code: bool = True,
        include_pages: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all available sources.
        
        Args:
            query: Search query
            num_results: Number of results per source
            include_code: Whether to include code examples
            include_pages: Whether to include crawled pages
            
        Returns:
            Dictionary with results from different sources
        """
        if num_results is None:
            num_results = self.max_chunks // 2  # Split between sources
        
        results = {}
        
        if include_pages:
            results['crawled_pages'] = self.search_crawled_pages(query, num_results)
        
        if include_code:
            results['code_examples'] = self.search_code_examples(query, num_results)
        
        return results
    
    def format_search_results(self, results: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Format search results into a readable context string.
        
        Args:
            results: Dictionary of search results from different sources
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for source_type, items in results.items():
            if not items:
                continue
            
            context_parts.append(f"=== {source_type.upper().replace('_', ' ')} ===")
            
            for i, item in enumerate(items[:5], 1):  # Limit to 5 items per source
                url = item.get('url', 'Unknown URL')
                content = item.get('content', '')
                summary = item.get('summary', '')
                metadata = item.get('metadata', {})
                
                part = f"[{i}] {url}\n"
                
                # Add summary if available
                if summary:
                    part += f"Summary: {summary}\n"
                
                # Add metadata context
                if isinstance(metadata, dict):
                    if 'headers' in metadata:
                        part += f"Headers: {metadata['headers']}\n"
                    if 'word_count' in metadata:
                        part += f"Word Count: {metadata['word_count']}\n"
                
                # Add content preview
                content_preview = content[:300] + "..." if len(content) > 300 else content
                part += f"Content: {content_preview}\n"
                
                context_parts.append(part)
        
        return "\n\n".join(context_parts)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the project database.
        
        Returns:
            Dictionary with database statistics
        """
        try:
            stats = {}
            
            # Count crawled pages
            pages_result = self.supabase.table('crawled_pages').select('id', count='exact').execute()
            stats['crawled_pages_count'] = pages_result.count or 0
            
            # Count code examples  
            code_result = self.supabase.table('code_examples').select('id', count='exact').execute()
            stats['code_examples_count'] = code_result.count or 0
            
            # Count sources
            sources_result = self.supabase.table('sources').select('source_id', count='exact').execute()
            stats['sources_count'] = sources_result.count or 0
            
            # Get unique sources
            sources_data = self.supabase.table('sources').select('source_id').execute()
            if sources_data.data:
                stats['unique_sources'] = [s['source_id'] for s in sources_data.data]
            
            # Sample URLs from crawled pages
            sample_urls = self.supabase.table('crawled_pages').select('url').limit(5).execute()
            if sample_urls.data:
                stats['sample_urls'] = [u['url'] for u in sample_urls.data]
            
            stats['last_updated'] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    def ask_question(
        self,
        question: str,
        num_chunks: int = None,
        include_code: bool = True,
        include_pages: bool = True
    ) -> Dict[str, Any]:
        """
        Ask a question and search for relevant information.
        
        Args:
            question: User's question
            num_chunks: Number of chunks to retrieve per source
            include_code: Whether to search code examples
            include_pages: Whether to search crawled pages
            
        Returns:
            Dictionary with search results and formatted context
        """
        logger.info(f"Processing question: {question}")
        
        # Search across sources
        results = self.search_all_sources(
            query=question,
            num_results=num_chunks,
            include_code=include_code,
            include_pages=include_pages
        )
        
        # Format context
        context = self.format_search_results(results)
        
        # Count total results
        total_results = sum(len(items) for items in results.values())
        
        response = {
            "question": question,
            "results": results,
            "formatted_context": context,
            "total_results": total_results,
            "timestamp": datetime.now().isoformat()
        }
        
        return response


def main():
    """Test the Project Knowledge Assistant."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Knowledge Assistant")
    parser.add_argument("--question", type=str, help="Question to ask")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--num-chunks", type=int, default=5, help="Number of chunks per source")
    
    args = parser.parse_args()
    
    try:
        # Initialize assistant
        assistant = ProjectKnowledgeAssistant()
        
        if args.stats:
            stats = assistant.get_database_stats()
            print("\n=== DATABASE STATISTICS ===")
            for key, value in stats.items():
                if isinstance(value, list):
                    print(f"{key}: {len(value)} items")
                    if len(value) <= 10:  # Show if not too many
                        for item in value:
                            print(f"  - {item}")
                else:
                    print(f"{key}: {value}")
            return
        
        question = args.question
        if not question:
            question = input("Enter your question: ")
        
        if not question.strip():
            print("No question provided.")
            return
        
        print(f"\n=== QUESTION ===")
        print(question)
        print("================\n")
        
        # Search for information
        response = assistant.ask_question(
            question=question,
            num_chunks=args.num_chunks
        )
        
        print(f"Found {response['total_results']} total results\n")
        
        print("=== FORMATTED CONTEXT ===")
        print(response['formatted_context'])
        print("==========================\n")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
