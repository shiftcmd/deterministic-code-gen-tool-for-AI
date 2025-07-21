#!/usr/bin/env python3
"""
Example usage of the Supabase Knowledge Assistant.

This script demonstrates various ways to use the knowledge assistant:
1. Adding documents to the knowledge base
2. Searching for information
3. Asking questions and getting AI-powered responses
4. Managing the document collection
"""

import os
import sys
import json
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_knowledge_assistant import SupabaseKnowledgeAssistant

def demonstrate_basic_usage():
    """Demonstrate basic usage of the knowledge assistant."""
    print("\n" + "=" * 60)
    print("SUPABASE KNOWLEDGE ASSISTANT DEMO")
    print("=" * 60)
    
    try:
        # Initialize the assistant
        print("\n1. Initializing Knowledge Assistant...")
        assistant = SupabaseKnowledgeAssistant()
        print("✓ Assistant initialized successfully")
        
        # Get database info
        print("\n2. Getting Database Information...")
        db_info = assistant.get_database_info()
        print(f"📊 Database Stats:")
        for key, value in db_info.items():
            if key != 'database_url':  # Don't print the full URL for security
                print(f"   {key}: {value}")
        
        # Example questions to ask
        example_questions = [
            "What is vector search?",
            "How does the database schema work?",
            "What is the Supabase Knowledge Assistant?",
            "Tell me about embeddings",
        ]
        
        print(f"\n3. Asking Example Questions...")
        print("-" * 40)
        
        for i, question in enumerate(example_questions[:2], 1):  # Limit to 2 questions for demo
            print(f"\n🤔 Question {i}: {question}")
            print("-" * 30)
            
            # Ask the question
            response = assistant.ask_question(
                question=question,
                num_chunks=3,
                show_context=False
            )
            
            print(f"📝 Answer:")
            print(response['answer'])
            print(f"\n📊 Found {response['num_chunks_found']} relevant chunks")
            print(f"⏰ Generated at: {response['timestamp']}")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        return False

def demonstrate_document_management():
    """Demonstrate adding and managing documents."""
    print("\n" + "=" * 60)
    print("DOCUMENT MANAGEMENT DEMO")
    print("=" * 60)
    
    try:
        assistant = SupabaseKnowledgeAssistant()
        
        # Sample documents to add
        sample_documents = [
            {
                "title": "Python Best Practices",
                "content": """
                Here are some essential Python best practices:
                
                1. Use meaningful variable names that describe what they contain
                2. Follow PEP 8 style guidelines for consistent code formatting
                3. Write docstrings for all functions, classes, and modules
                4. Use type hints to improve code readability and catch errors
                5. Handle exceptions appropriately with try-except blocks
                6. Use virtual environments to manage dependencies
                7. Write unit tests for your code to ensure reliability
                8. Use list comprehensions for simple transformations
                9. Avoid global variables when possible
                10. Use context managers (with statements) for resource management
                """,
                "document_type": "programming",
                "metadata": {
                    "tags": ["python", "best-practices", "coding"],
                    "difficulty": "intermediate",
                    "category": "programming"
                }
            },
            {
                "title": "Database Design Principles",
                "content": """
                Key principles for good database design:
                
                1. Normalization: Organize data to reduce redundancy
                2. Primary Keys: Each table should have a unique identifier
                3. Foreign Keys: Use relationships to connect related data
                4. Indexing: Create indexes on frequently queried columns
                5. Data Types: Choose appropriate data types for each column
                6. Constraints: Use constraints to maintain data integrity
                7. Security: Implement proper access controls and authentication
                8. Backup Strategy: Regular backups and disaster recovery plans
                9. Performance: Monitor and optimize query performance
                10. Documentation: Document your schema and relationships
                """,
                "document_type": "database",
                "metadata": {
                    "tags": ["database", "design", "sql"],
                    "difficulty": "intermediate",
                    "category": "data-management"
                }
            }
        ]
        
        print("\n1. Adding Sample Documents...")
        for i, doc in enumerate(sample_documents, 1):
            print(f"\n📄 Adding Document {i}: {doc['title']}")
            success = assistant.add_document(
                content=doc['content'],
                title=doc['title'],
                document_type=doc['document_type'],
                metadata=doc['metadata']
            )
            
            if success:
                print(f"✓ Successfully added '{doc['title']}'")
            else:
                print(f"❌ Failed to add '{doc['title']}'")
        
        # Test searching with the new documents
        print(f"\n2. Testing Search with New Documents...")
        test_queries = [
            "How should I handle exceptions in Python?",
            "What are the principles of database normalization?",
        ]
        
        for query in test_queries:
            print(f"\n🔍 Searching for: '{query}'")
            chunks = assistant.search_knowledge_base(query, num_results=2)
            print(f"📊 Found {len(chunks)} relevant chunks")
            
            for j, chunk in enumerate(chunks[:1], 1):  # Show first result
                title = chunk.get('title', 'Untitled')
                doc_type = chunk.get('document_type', 'unknown')
                print(f"   {j}. {title} (Type: {doc_type})")
        
        # Get updated database info
        print(f"\n3. Updated Database Information...")
        db_info = assistant.get_database_info()
        print(f"📊 Total Documents: {db_info.get('total_documents', 'unknown')}")
        print(f"📊 Total Embeddings: {db_info.get('total_embeddings', 'unknown')}")
        print(f"📊 Document Types: {', '.join(db_info.get('document_types', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during document management demo: {e}")
        return False

def demonstrate_advanced_search():
    """Demonstrate advanced search capabilities."""
    print("\n" + "=" * 60)
    print("ADVANCED SEARCH DEMO")
    print("=" * 60)
    
    try:
        assistant = SupabaseKnowledgeAssistant()
        
        # Advanced search queries
        search_scenarios = [
            {
                "query": "machine learning algorithms",
                "description": "Technical topic search"
            },
            {
                "query": "how to optimize database performance",
                "description": "Problem-solving query"
            },
            {
                "query": "security best practices",
                "description": "Security-related content"
            }
        ]
        
        print("\n1. Running Advanced Search Scenarios...")
        
        for i, scenario in enumerate(search_scenarios, 1):
            print(f"\n🔍 Scenario {i}: {scenario['description']}")
            print(f"Query: '{scenario['query']}'")
            print("-" * 40)
            
            # Search with context
            response = assistant.ask_question(
                question=scenario['query'],
                num_chunks=3,
                show_context=True,
                model="gpt-3.5-turbo"
            )
            
            print(f"📝 Answer:")
            print(response['answer'][:300] + "..." if len(response['answer']) > 300 else response['answer'])
            print(f"\n📊 Chunks found: {response['num_chunks_found']}")
            
            if 'context' in response and response['context']:
                print(f"\n📄 Context sources used:")
                # Extract document titles from context
                context_lines = response['context'].split('\n')
                for line in context_lines:
                    if line.startswith('[') and '] (' in line:
                        title_part = line.split('] (')[0][1:]  # Extract title
                        print(f"   • {title_part}")
                        break  # Just show first source for brevity
            
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during advanced search demo: {e}")
        return False

def interactive_mode():
    """Run the assistant in interactive mode."""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)
    print("Ask questions to the knowledge assistant. Type 'quit' to exit.")
    
    try:
        assistant = SupabaseKnowledgeAssistant()
        
        while True:
            print("\n" + "-" * 40)
            question = input("🤔 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                print("Please enter a question.")
                continue
            
            print(f"\n🔍 Searching for: '{question}'")
            print("⏳ Processing...")
            
            # Get response
            response = assistant.ask_question(
                question=question,
                num_chunks=5,
                show_context=False
            )
            
            print(f"\n📝 Answer:")
            print(response['answer'])
            print(f"\n📊 Found {response['num_chunks_found']} relevant chunks")
            
            # Ask if user wants to see context
            show_context = input("\n💡 Show context sources? (y/n): ").lower().startswith('y')
            if show_context:
                detailed_response = assistant.ask_question(
                    question=question,
                    num_chunks=5,
                    show_context=True
                )
                if 'context' in detailed_response:
                    print(f"\n📄 Context:")
                    print(detailed_response['context'])
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error in interactive mode: {e}")

def main():
    """Main function with menu system."""
    print("🧠 Supabase Knowledge Assistant - Example Usage")
    
    while True:
        print("\n" + "=" * 50)
        print("MENU OPTIONS")
        print("=" * 50)
        print("1. Basic Usage Demo")
        print("2. Document Management Demo")
        print("3. Advanced Search Demo")
        print("4. Interactive Mode")
        print("5. Exit")
        
        try:
            choice = input("\nSelect an option (1-5): ").strip()
            
            if choice == '1':
                demonstrate_basic_usage()
            elif choice == '2':
                demonstrate_document_management()
            elif choice == '3':
                demonstrate_advanced_search()
            elif choice == '4':
                interactive_mode()
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please choose 1-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
