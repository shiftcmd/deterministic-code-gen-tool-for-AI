#!/usr/bin/env python3
"""
Script to generate embeddings for existing data in crawled_pages and code_examples tables.
This will populate the embedding columns so vector search can work.
"""

import os
import sys
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self):
        """Initialize the embedding generator with Supabase and OpenAI clients."""
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info(f"Connected to Supabase at {supabase_url}")
        
        # Initialize OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set in .env file")
        
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        logger.info("OpenAI client initialized")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a piece of text using OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def process_crawled_pages(self, batch_size: int = 10):
        """Generate embeddings for all crawled_pages that don't have them."""
        logger.info("Processing crawled_pages table...")
        
        # Get pages without embeddings
        result = self.supabase.table('crawled_pages').select(
            "id, content, url"
        ).is_('embedding', 'null').limit(1000).execute()
        
        pages = result.data
        logger.info(f"Found {len(pages)} pages without embeddings")
        
        processed = 0
        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            
            for page in batch:
                try:
                    # Combine content and URL for better context
                    text_to_embed = f"{page.get('url', '')} {page.get('content', '')}"
                    
                    if not text_to_embed.strip():
                        logger.warning(f"Skipping page {page['id']} - no content")
                        continue
                    
                    # Generate embedding
                    embedding = self.generate_embedding(text_to_embed)
                    
                    if embedding:
                        # Update the database
                        self.supabase.table('crawled_pages').update({
                            'embedding': embedding
                        }).eq('id', page['id']).execute()
                        
                        processed += 1
                        logger.info(f"Generated embedding for page {page['id']} ({processed}/{len(pages)})")
                    
                    # Rate limiting - be nice to OpenAI API
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error processing page {page.get('id')}: {e}")
                    continue
        
        logger.info(f"Processed {processed} crawled_pages")
    
    def process_code_examples(self, batch_size: int = 10):
        """Generate embeddings for all code_examples that don't have them."""
        logger.info("Processing code_examples table...")
        
        # Get examples without embeddings
        result = self.supabase.table('code_examples').select(
            "id, content, summary, url"
        ).is_('embedding', 'null').limit(1000).execute()
        
        examples = result.data
        logger.info(f"Found {len(examples)} code examples without embeddings")
        
        processed = 0
        for i in range(0, len(examples), batch_size):
            batch = examples[i:i + batch_size]
            
            for example in batch:
                try:
                    # Combine content, summary, and URL for better context
                    text_parts = [
                        example.get('url', ''),
                        example.get('summary', ''),
                        example.get('content', '')
                    ]
                    text_to_embed = ' '.join(filter(None, text_parts))
                    
                    if not text_to_embed.strip():
                        logger.warning(f"Skipping example {example['id']} - no content")
                        continue
                    
                    # Generate embedding
                    embedding = self.generate_embedding(text_to_embed)
                    
                    if embedding:
                        # Update the database
                        self.supabase.table('code_examples').update({
                            'embedding': embedding
                        }).eq('id', example['id']).execute()
                        
                        processed += 1
                        logger.info(f"Generated embedding for example {example['id']} ({processed}/{len(examples)})")
                    
                    # Rate limiting - be nice to OpenAI API
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error processing example {example.get('id')}: {e}")
                    continue
        
        logger.info(f"Processed {processed} code examples")
    
    def get_stats(self):
        """Get statistics about embeddings in the database."""
        try:
            # Count crawled_pages with and without embeddings
            pages_with = self.supabase.table('crawled_pages').select(
                'id', count='exact'
            ).not_.is_('embedding', 'null').execute()
            
            pages_without = self.supabase.table('crawled_pages').select(
                'id', count='exact'
            ).is_('embedding', 'null').execute()
            
            # Count code_examples with and without embeddings
            examples_with = self.supabase.table('code_examples').select(
                'id', count='exact'
            ).not_.is_('embedding', 'null').execute()
            
            examples_without = self.supabase.table('code_examples').select(
                'id', count='exact'
            ).is_('embedding', 'null').execute()
            
            logger.info("=== Embedding Statistics ===")
            logger.info(f"Crawled Pages: {pages_with.count or 0} with embeddings, {pages_without.count or 0} without")
            logger.info(f"Code Examples: {examples_with.count or 0} with embeddings, {examples_without.count or 0} without")
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")

def main():
    """Main function to generate embeddings."""
    try:
        generator = EmbeddingGenerator()
        
        # Show current stats
        generator.get_stats()
        
        # Ask user what to process
        print("\nWhat would you like to do?")
        print("1. Generate embeddings for crawled_pages")
        print("2. Generate embeddings for code_examples") 
        print("3. Generate embeddings for both")
        print("4. Show stats only")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == '1':
            generator.process_crawled_pages()
        elif choice == '2':
            generator.process_code_examples()
        elif choice == '3':
            generator.process_crawled_pages()
            generator.process_code_examples()
        elif choice == '4':
            pass  # Stats already shown
        else:
            print("Invalid choice")
            return
        
        # Show final stats
        print("\n=== Final Statistics ===")
        generator.get_stats()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()