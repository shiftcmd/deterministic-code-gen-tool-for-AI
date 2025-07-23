#!/usr/bin/env python3
"""
OpenAI Knowledge Assistant

This script:
1. Connects to a specific OpenAI Assistant using your API key
2. Retrieves relevant document chunks from ChromaDB using semantic search
3. Sends the chunks as context to the OpenAI Assistant
4. Handles function calling for database interactions
5. Returns the Assistant's answer based on the retrieved context
"""

import os
import sys
import json
import time
import argparse
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('openai_assistant.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the test_embeddings_simple module for ChromaDB search
from test_embeddings_simple import search_chroma, get_database_info

try:
    from openai import OpenAI
except ImportError:
    logger.error("OpenAI package not found. Install with: pip install openai")
    sys.exit(1)

class OpenAIKnowledgeAssistant:
    """Class to interact with the OpenAI Assistant API."""
    
    def __init__(
        self, 
        api_key: str, 
        assistant_id: str,
        db_path: str = "./knowledgebase.db",
        chroma_dir: str = "./chroma_db_data",
        collection_name: str = "vertex_ai_embeddings"
    ):
        """
        Initialize the OpenAI Knowledge Assistant.
        
        Args:
            api_key: OpenAI API key
            assistant_id: ID of the OpenAI Assistant to use
            db_path: Path to the SQLite database
            chroma_dir: Path to the ChromaDB directory
            collection_name: ChromaDB collection name
        """
        self.api_key = api_key
        self.assistant_id = assistant_id
        self.db_path = db_path
        self.chroma_dir = chroma_dir
        self.collection_name = collection_name
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized OpenAI client with Assistant ID: {assistant_id}")
        
        # Get database info
        self.db_info = get_database_info(db_path)
        logger.info(f"Database has {self.db_info['total_chunks']} chunks, {self.db_info['embedded_chunks']} with embeddings")
    
    def format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format the retrieved chunks into a context string for the Assistant.
        
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
    
    def search_knowledge_base(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant chunks.
        
        Args:
            query: User's question or query
            num_results: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks
        """
        logger.info(f"Searching for relevant chunks for query: {query}")
        results = search_chroma(
            query=query,
            collection_name=self.collection_name,
            persist_directory=self.chroma_dir,
            num_results=num_results,
            db_path=self.db_path
        )
        
        logger.info(f"Found {len(results)} relevant chunks")
        return results
    
    def handle_function_calls(self, tool_calls: List[Dict[str, Any]], run_id: str, thread_id: str) -> None:
        """
        Handle function calls from the Assistant.
        
        Args:
            tool_calls: List of tool calls from the Assistant
            run_id: ID of the current run
            thread_id: ID of the current thread
        """
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_call_id = tool_call.id
            
            logger.info(f"Handling function call: {function_name} with args: {function_args}")
            
            response_message = None
            
            if function_name == "search_knowledge_base":
                query = function_args.get("query", "")
                num_results = function_args.get("num_results", 5)
                
                results = self.search_knowledge_base(query, num_results)
                
                # Format results for JSON serialization
                serializable_results = []
                for result in results:
                    # Convert any non-serializable objects to strings
                    serializable_result = {}
                    for key, value in result.items():
                        if isinstance(value, (str, int, float, bool, type(None))):
                            serializable_result[key] = value
                        elif isinstance(value, list):
                            # Handle lists of simple types
                            if all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                                serializable_result[key] = value
                            else:
                                serializable_result[key] = str(value)
                        else:
                            serializable_result[key] = str(value)
                    serializable_results.append(serializable_result)
                
                response_message = {
                    "results": serializable_results,
                    "count": len(results)
                }
            
            elif function_name == "get_database_info":
                # Make sure db_info is serializable
                serializable_info = {}
                for key, value in self.db_info.items():
                    if isinstance(value, (str, int, float, bool, type(None))):
                        serializable_info[key] = value
                    else:
                        serializable_info[key] = str(value)
                
                response_message = serializable_info
            
            # Add tool output
            if response_message:
                logger.info(f"Submitting tool output for {function_name}")
                tool_outputs.append({
                    "tool_call_id": tool_call_id,
                    "output": json.dumps(response_message)
                })
        
        # Submit all tool outputs at once
        if tool_outputs:
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs
            )
    
    def ask_question(self, question: str, show_context: bool = False, num_chunks: int = 5) -> str:
        """
        Ask a question to the OpenAI Assistant.
        
        Args:
            question: User's question
            show_context: Whether to show the retrieved context
            num_chunks: Number of chunks to retrieve
            
        Returns:
            Assistant's response
        """
        # First, retrieve relevant chunks
        chunks = self.search_knowledge_base(question, num_chunks)
        
        if not chunks:
            return "No relevant information found in the knowledge base."
        
        # Format chunks for the Assistant
        context = self.format_context(chunks)
        
        # Show context if requested
        if show_context:
            print("\n=== CONTEXT ===\n")
            print(context)
            print("\n=== END CONTEXT ===\n")
        
        # Create a new thread
        thread = self.client.beta.threads.create()
        logger.info(f"Created new thread with ID: {thread.id}")
        
        # Add user message with context and question
        message_content = f"""
I need you to answer a question based on the following context information.
If the context doesn't contain relevant information to answer the question, admit that you don't know
rather than making up an answer. Use only the information in the context to answer the question.

CONTEXT:
{context}

QUESTION:
{question}
"""
        
        # Add the message to the thread
        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message_content
        )
        
        # Run the Assistant on the thread
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )
        
        # Wait for the run to complete
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            
            if run.status == "completed":
                break
            elif run.status == "requires_action":
                # Handle function calls
                if run.required_action and run.required_action.type == "submit_tool_outputs":
                    self.handle_function_calls(
                        run.required_action.submit_tool_outputs.tool_calls,
                        run.id,
                        thread.id
                    )
            elif run.status in ["failed", "cancelled", "expired"]:
                return f"Error: Run ended with status {run.status}"
            
            time.sleep(1)  # Wait before checking again
        
        # Get the latest message from the Assistant
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Return the latest message from the Assistant
        for message in messages.data:
            if message.role == "assistant":
                # Check if the message has content
                if hasattr(message, 'content') and message.content:
                    # Get the text value from the first content item
                    for content_item in message.content:
                        if hasattr(content_item, 'text') and content_item.text:
                            return content_item.text.value
        
        return "No response from the Assistant."

def main():
    """Main function for the OpenAI Knowledge Assistant."""
    parser = argparse.ArgumentParser(description="OpenAI Knowledge Assistant")
    parser.add_argument("--question", type=str, help="Question to ask")
    parser.add_argument("--api-key", type=str, help="OpenAI API key")
    parser.add_argument("--assistant-id", type=str, help="OpenAI Assistant ID")
    parser.add_argument("--num-chunks", type=int, default=5, help="Number of chunks to retrieve")
    parser.add_argument("--show-context", action="store_true", help="Show retrieved context")
    parser.add_argument("--db-path", type=str, default="./knowledgebase.db", help="Path to SQLite database")
    parser.add_argument("--chroma-dir", type=str, default="./chroma_db_data", help="Path to ChromaDB directory")
    parser.add_argument("--collection", type=str, default="vertex_ai_embeddings", help="ChromaDB collection name")
    args = parser.parse_args()
    
    # Get API key from arguments or environment variable
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Enter your OpenAI API key: ")
    
    # Get Assistant ID from arguments or prompt the user
    assistant_id = args.assistant_id or os.environ.get("OPENAI_ASSISTANT_ID")
    if not assistant_id:
        assistant_id = input("Enter your OpenAI Assistant ID: ")
    
    # Get question from arguments or prompt the user
    question = args.question
    if not question:
        question = input("Enter your question: ")
    
    # Initialize the Assistant
    assistant = OpenAIKnowledgeAssistant(
        api_key=api_key,
        assistant_id=assistant_id,
        db_path=args.db_path,
        chroma_dir=args.chroma_dir,
        collection_name=args.collection
    )
    
    # Ask the question
    logger.info(f"Asking question: {question}")
    response = assistant.ask_question(
        question=question,
        show_context=args.show_context,
        num_chunks=args.num_chunks
    )
    
    # Print the response
    print("\n=== ANSWER ===\n")
    print(response)
    print("\n=== END ANSWER ===\n")

if __name__ == "__main__":
    main()
