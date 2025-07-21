#!/usr/bin/env python3
"""
Setup script for the Supabase Knowledge Assistant.

This script:
1. Verifies environment variables are set
2. Tests Supabase connection
3. Sets up database schema if needed
4. Provides basic configuration validation
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
except ImportError:
    logger.error("Supabase package not found. Install with: pip install supabase")
    sys.exit(1)

try:
    import openai
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False
    logger.warning("OpenAI package not available - embeddings will not work")

class SupabaseAssistantSetup:
    """Setup and configuration for the Supabase Knowledge Assistant."""
    
    def __init__(self):
        """Initialize the setup class."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        self.supabase_client = None
        self.openai_client = None
    
    def check_environment(self) -> Dict[str, Any]:
        """
        Check if all required environment variables are set.
        
        Returns:
            Dictionary with environment check results
        """
        results = {
            "supabase_url": bool(self.supabase_url),
            "supabase_key": bool(self.supabase_key),
            "openai_key": bool(self.openai_api_key),
            "openai_available": openai_available
        }
        
        logger.info("Environment Check Results:")
        for key, value in results.items():
            status = "✓" if value else "✗"
            logger.info(f"  {key}: {status}")
        
        return results
    
    def test_supabase_connection(self) -> bool:
        """
        Test connection to Supabase.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.supabase_url or not self.supabase_key:
            logger.error("Supabase URL or key not found in environment")
            return False
        
        try:
            self.supabase_client = create_client(self.supabase_url, self.supabase_key)
            
            # Test connection by trying to list tables
            result = self.supabase_client.table('documents').select('id').limit(1).execute()
            logger.info("✓ Supabase connection successful")
            return True
            
        except Exception as e:
            logger.error(f"✗ Supabase connection failed: {e}")
            return False
    
    def test_openai_connection(self) -> bool:
        """
        Test connection to OpenAI.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not openai_available:
            logger.warning("OpenAI package not available")
            return False
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not found in environment")
            return False
        
        try:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            
            # Test with a simple embedding request
            response = self.openai_client.embeddings.create(
                input="test",
                model="text-embedding-3-small"
            )
            
            if response and response.data:
                logger.info("✓ OpenAI connection successful")
                return True
            else:
                logger.error("✗ OpenAI connection failed: No response data")
                return False
                
        except Exception as e:
            logger.error(f"✗ OpenAI connection failed: {e}")
            return False
    
    def check_database_schema(self) -> Dict[str, bool]:
        """
        Check if required database tables exist.
        
        Returns:
            Dictionary indicating which tables exist
        """
        if not self.supabase_client:
            if not self.test_supabase_connection():
                return {"error": "Cannot connect to Supabase"}
        
        results = {}
        
        # Check for documents table
        try:
            result = self.supabase_client.table('documents').select('id').limit(1).execute()
            results['documents_table'] = True
            logger.info("✓ Documents table exists")
        except Exception as e:
            results['documents_table'] = False
            logger.error(f"✗ Documents table missing or inaccessible: {e}")
        
        # Check for document_embeddings table
        try:
            result = self.supabase_client.table('document_embeddings').select('id').limit(1).execute()
            results['embeddings_table'] = True
            logger.info("✓ Document embeddings table exists")
        except Exception as e:
            results['embeddings_table'] = False
            logger.error(f"✗ Document embeddings table missing or inaccessible: {e}")
        
        # Check for search function
        try:
            result = self.supabase_client.rpc('get_document_stats').execute()
            results['search_functions'] = True
            logger.info("✓ Search functions available")
        except Exception as e:
            results['search_functions'] = False
            logger.error(f"✗ Search functions missing: {e}")
        
        return results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current database.
        
        Returns:
            Dictionary with database statistics
        """
        if not self.supabase_client:
            if not self.test_supabase_connection():
                return {"error": "Cannot connect to Supabase"}
        
        try:
            # Get document count
            doc_result = self.supabase_client.table('documents').select('id', count='exact').execute()
            doc_count = doc_result.count if doc_result.count is not None else 0
            
            # Get embedding count
            emb_result = self.supabase_client.table('document_embeddings').select('id', count='exact').execute()
            emb_count = emb_result.count if emb_result.count is not None else 0
            
            # Get document types
            types_result = self.supabase_client.table('documents').select('document_type').execute()
            doc_types = list(set([doc.get('document_type', 'unknown') for doc in types_result.data])) if types_result.data else []
            
            return {
                "total_documents": doc_count,
                "total_embeddings": emb_count,
                "document_types": doc_types,
                "embeddings_coverage": f"{(emb_count/doc_count*100):.1f}%" if doc_count > 0 else "0%"
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    def create_sample_documents(self, overwrite: bool = False) -> bool:
        """
        Create sample documents for testing.
        
        Args:
            overwrite: Whether to delete existing sample documents first
            
        Returns:
            True if successful, False otherwise
        """
        if not self.supabase_client:
            if not self.test_supabase_connection():
                return False
        
        sample_docs = [
            {
                "title": "Supabase Knowledge Assistant Introduction",
                "content": "The Supabase Knowledge Assistant is a powerful tool for storing, searching, and retrieving information using vector embeddings and semantic search. It combines the robust database capabilities of Supabase with advanced AI techniques to provide intelligent document retrieval and question answering.",
                "document_type": "documentation",
                "metadata": {
                    "tags": ["introduction", "knowledge-assistant", "supabase"],
                    "category": "getting-started"
                }
            },
            {
                "title": "Vector Embeddings Explained",
                "content": "Vector embeddings are numerical representations of text that capture semantic meaning. They allow computers to understand the context and relationships between different pieces of text. In this system, we use OpenAI's text-embedding-3-small model to convert documents into 1536-dimensional vectors that can be searched efficiently.",
                "document_type": "technical",
                "metadata": {
                    "tags": ["embeddings", "vectors", "semantic-search"],
                    "category": "technical-concepts"
                }
            },
            {
                "title": "Database Architecture",
                "content": "The knowledge assistant uses a two-table architecture: the 'documents' table stores the actual content with metadata, while the 'document_embeddings' table stores the vector representations. This separation allows for efficient storage and fast similarity searches using PostgreSQL's pgvector extension.",
                "document_type": "architecture",
                "metadata": {
                    "tags": ["database", "architecture", "postgresql"],
                    "category": "system-design"
                }
            }
        ]
        
        try:
            if overwrite:
                # Delete existing sample documents
                self.supabase_client.table('documents').delete().eq('document_type', 'documentation').execute()
                logger.info("Deleted existing sample documents")
            
            for doc in sample_docs:
                result = self.supabase_client.table('documents').insert(doc).execute()
                if result.data:
                    logger.info(f"Created sample document: {doc['title']}")
                    
                    # Create embedding if OpenAI is available
                    if self.openai_client:
                        try:
                            embedding_response = self.openai_client.embeddings.create(
                                input=doc['content'],
                                model="text-embedding-3-small"
                            )
                            
                            embedding_data = {
                                "document_id": result.data[0]['id'],
                                "embedding": embedding_response.data[0].embedding
                            }
                            
                            self.supabase_client.table('document_embeddings').insert(embedding_data).execute()
                            logger.info(f"Created embedding for: {doc['title']}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to create embedding for {doc['title']}: {e}")
            
            logger.info("✓ Sample documents created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create sample documents: {e}")
            return False
    
    def run_full_setup(self) -> Dict[str, Any]:
        """
        Run complete setup and validation.
        
        Returns:
            Dictionary with setup results
        """
        logger.info("=" * 50)
        logger.info("SUPABASE KNOWLEDGE ASSISTANT SETUP")
        logger.info("=" * 50)
        
        results = {}
        
        # Check environment
        logger.info("\n1. Checking Environment Variables...")
        results['environment'] = self.check_environment()
        
        # Test connections
        logger.info("\n2. Testing Connections...")
        results['supabase_connection'] = self.test_supabase_connection()
        results['openai_connection'] = self.test_openai_connection()
        
        # Check database schema
        logger.info("\n3. Checking Database Schema...")
        results['database_schema'] = self.check_database_schema()
        
        # Get database stats
        logger.info("\n4. Getting Database Statistics...")
        results['database_stats'] = self.get_database_stats()
        
        # Overall status
        all_good = (
            results['supabase_connection'] and
            results['database_schema'].get('documents_table', False) and
            results['database_schema'].get('embeddings_table', False)
        )
        
        logger.info("\n" + "=" * 50)
        if all_good:
            logger.info("✓ SETUP COMPLETE - Knowledge Assistant is ready to use!")
        else:
            logger.info("✗ SETUP INCOMPLETE - Please address the issues above")
        logger.info("=" * 50)
        
        return results


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Supabase Knowledge Assistant")
    parser.add_argument("--create-samples", action="store_true", help="Create sample documents")
    parser.add_argument("--overwrite-samples", action="store_true", help="Overwrite existing sample documents")
    args = parser.parse_args()
    
    setup = SupabaseAssistantSetup()
    
    # Run full setup
    results = setup.run_full_setup()
    
    # Create sample documents if requested
    if args.create_samples:
        logger.info("\n5. Creating Sample Documents...")
        setup.create_sample_documents(overwrite=args.overwrite_samples)
    
    # Print summary
    logger.info("\nSetup Summary:")
    if results.get('supabase_connection'):
        logger.info("  - Supabase: Connected ✓")
    else:
        logger.info("  - Supabase: Failed ✗")
    
    if results.get('openai_connection'):
        logger.info("  - OpenAI: Connected ✓")
    else:
        logger.info("  - OpenAI: Not connected ⚠")
    
    db_stats = results.get('database_stats', {})
    if 'error' not in db_stats:
        logger.info(f"  - Documents: {db_stats.get('total_documents', 0)}")
        logger.info(f"  - Embeddings: {db_stats.get('total_embeddings', 0)}")
    
    return results


if __name__ == "__main__":
    main()
