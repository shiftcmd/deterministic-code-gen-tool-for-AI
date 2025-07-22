#!/usr/bin/env python3
"""
CLI Knowledge Agent with OpenAI Function Calling

This script creates a command line interface that connects to OpenAI and uses
function calling to query the Supabase Knowledge Assistant. The OpenAI agent
can intelligently decide when to search the knowledge base and provide
contextual responses.

Usage:
    python cli_knowledge_agent.py --question "Your question here"
    python cli_knowledge_agent.py --interactive
    python cli_knowledge_agent.py --help
"""

import os
import sys
import json
import argparse
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cli_knowledge_agent.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import required libraries
try:
    from openai import OpenAI
except ImportError:
    logger.error("OpenAI package not found. Install with: pip install openai")
    sys.exit(1)

# Import our Project Knowledge Assistant
try:
    from project_knowledge_assistant import ProjectKnowledgeAssistant
except ImportError as e:
    logger.error(f"Could not import ProjectKnowledgeAssistant: {e}")
    logger.error("Make sure project_knowledge_assistant.py is in the same directory")
    sys.exit(1)

class CLIKnowledgeAgent:
    """
    CLI agent that uses OpenAI function calling to interact with Supabase Knowledge Assistant.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_tokens: int = 1500,
        temperature: float = 0.7
    ):
        """
        Initialize the CLI Knowledge Agent.
        
        Args:
            openai_api_key: OpenAI API key (defaults to env var)
            model: OpenAI model to use
            max_tokens: Maximum tokens in response
            temperature: Response creativity (0.0-1.0)
        """
        # Initialize OpenAI client
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env or pass as parameter")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize Project Knowledge Assistant
        try:
            self.knowledge_assistant = ProjectKnowledgeAssistant()
            logger.info("Project Knowledge Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Project Knowledge Assistant: {e}")
            raise
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # Define available tools for OpenAI function calling using current format
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_base",
                    "description": "Search the Supabase knowledge base for relevant information. Use this when the user asks questions that might be answered by stored documents or when you need to find specific information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query or question to look for in the knowledge base"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of document chunks to retrieve (default: 5, max: 20)",
                                "default": 5,
                                "minimum": 1,
                                "maximum": 20
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_database_info",
                    "description": "Get information about the knowledge base including number of documents, document types, and statistics. Use this when the user asks about the knowledge base itself.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_detailed_question",
                    "description": "Ask a detailed question to the knowledge assistant which will search for relevant information and provide an AI-generated response based on the found context. Use this for complex questions that need comprehensive answers.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The detailed question to ask"
                            },
                            "num_chunks": {
                                "type": "integer",
                                "description": "Number of chunks to use for context (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["question"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_project_file",
                    "description": "Read the contents of a file from the project directory. Use this when the user asks about specific files, configuration, code structure, or wants to see the actual content of files in the project.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Relative path to the file from the project root (e.g., 'frontend/src/App.js', 'README.md', 'package.json')"
                            },
                            "max_lines": {
                                "type": "integer",
                                "description": "Maximum number of lines to read (default: 100 to avoid overwhelming responses)",
                                "default": 100,
                                "minimum": 1,
                                "maximum": 1000
                            }
                        },
                        "required": ["file_path"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_project_files",
                    "description": "List files and directories in the project. Use this to explore the project structure or find specific files when the user asks about what files exist.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "Relative path to directory from project root (empty string or '.' for root directory)",
                                "default": "."
                            },
                            "include_hidden": {
                                "type": "boolean",
                                "description": "Whether to include hidden files (starting with .)",
                                "default": False
                            },
                            "max_items": {
                                "type": "integer",
                                "description": "Maximum number of items to return",
                                "default": 50,
                                "minimum": 1,
                                "maximum": 200
                            }
                        },
                        "additionalProperties": False
                    }
                }
            }
        ]
        
        # System message for the agent
        self.system_message = """You are a helpful AI assistant that can access a knowledge base and project files through various tools. 

You have access to the following capabilities:
1. search_knowledge_base: Search for specific information in the crawled pages and code examples database
2. get_database_info: Get statistics and information about the knowledge base
3. ask_detailed_question: Ask complex questions that require contextual analysis of the database
4. read_project_file: Read the contents of specific files in the project directory
5. list_project_files: List files and directories to explore the project structure

When a user asks a question:
- If it's about the knowledge base itself (size, contents, etc.), use get_database_info
- If it's asking about specific project files, configuration, or code structure, use read_project_file or list_project_files
- If it's a search for information that might be in crawled pages or code examples, use search_knowledge_base
- If it's a complex question requiring analysis and synthesis, use ask_detailed_question
- If they want to explore the project structure, use list_project_files first

Always be helpful, accurate, and provide context when possible. You can combine multiple tools to give comprehensive answers. For example, you might list files to understand structure, then read specific files to provide detailed information.

Security: You can only access files within the project directory for safety."""

    def search_knowledge_base(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            Search results with metadata
        """
        try:
            results = self.knowledge_assistant.search_all_sources(
                query=query,
                num_results=num_results//2,  # Split between sources
                include_code=True,
                include_pages=True
            )
            
            # Flatten results for compatibility
            flat_results = []
            for source_type, items in results.items():
                for item in items:
                    item['source_type'] = source_type
                    flat_results.append(item)
            
            return {
                "success": True,
                "query": query,
                "num_results": len(flat_results),
                "results": flat_results,
                "by_source": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the knowledge base.
        
        Returns:
            Database statistics and information
        """
        try:
            info = self.knowledge_assistant.get_database_stats()
            return {
                "success": True,
                "database_info": info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def ask_detailed_question(self, question: str, num_chunks: int = 5) -> Dict[str, Any]:
        """
        Ask a detailed question to the knowledge assistant.
        
        Args:
            question: The question to ask
            num_chunks: Number of chunks to use for context
            
        Returns:
            Detailed response with context
        """
        try:
            response = self.knowledge_assistant.ask_question(
                question=question,
                num_chunks=num_chunks,
                include_code=True,
                include_pages=True
            )
            
            return {
                "success": True,
                "question": question,
                "answer": response.get("answer", ""),
                "num_chunks_found": response.get("num_chunks_found", 0),
                "context_available": "context" in response,
                "timestamp": response.get("timestamp", datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"Error asking detailed question: {e}")
            return {
                "success": False,
                "error": str(e),
                "question": question
            }
    
    def read_project_file(self, file_path: str, max_lines: int = 100) -> Dict[str, Any]:
        """
        Read contents of a file from the project directory.
        
        Args:
            file_path: Relative path to file from project root
            max_lines: Maximum number of lines to read
            
        Returns:
            Dictionary with file contents and metadata
        """
        try:
            # Get the project root directory (two levels up from tools/agents/)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            full_path = os.path.join(project_root, file_path)
            
            # Security check - ensure the file is within the project directory
            if not os.path.abspath(full_path).startswith(project_root):
                return {
                    "success": False,
                    "error": "Access denied: File path outside project directory",
                    "file_path": file_path
                }
            
            # Check if file exists
            if not os.path.exists(full_path):
                return {
                    "success": False,
                    "error": "File not found",
                    "file_path": file_path
                }
            
            # Check if it's actually a file (not a directory)
            if not os.path.isfile(full_path):
                return {
                    "success": False,
                    "error": "Path is not a file",
                    "file_path": file_path
                }
            
            # Read the file
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip('\n\r'))
                
                content = '\n'.join(lines)
            
            # Get file stats
            file_stats = os.stat(full_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "content": content,
                "lines_read": len(lines),
                "max_lines_reached": len(lines) == max_lines,
                "file_size_bytes": file_stats.st_size,
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def list_project_files(self, directory_path: str = ".", include_hidden: bool = False, max_items: int = 50) -> Dict[str, Any]:
        """
        List files and directories in the project.
        
        Args:
            directory_path: Relative path to directory from project root
            include_hidden: Whether to include hidden files
            max_items: Maximum number of items to return
            
        Returns:
            Dictionary with directory listing
        """
        try:
            # Get the project root directory (two levels up from tools/agents/)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(script_dir))
            
            # Handle empty or current directory path
            if not directory_path or directory_path == ".":
                full_path = project_root
            else:
                full_path = os.path.join(project_root, directory_path)
            
            # Security check - ensure the path is within the project directory
            if not os.path.abspath(full_path).startswith(project_root):
                return {
                    "success": False,
                    "error": "Access denied: Path outside project directory",
                    "directory_path": directory_path
                }
            
            # Check if directory exists
            if not os.path.exists(full_path):
                return {
                    "success": False,
                    "error": "Directory not found",
                    "directory_path": directory_path
                }
            
            # Check if it's actually a directory
            if not os.path.isdir(full_path):
                return {
                    "success": False,
                    "error": "Path is not a directory",
                    "directory_path": directory_path
                }
            
            # List directory contents
            items = []
            try:
                for item_name in os.listdir(full_path):
                    # Skip hidden files unless requested
                    if not include_hidden and item_name.startswith('.'):
                        continue
                    
                    # Stop if we've reached max items
                    if len(items) >= max_items:
                        break
                    
                    item_path = os.path.join(full_path, item_name)
                    item_stat = os.stat(item_path)
                    
                    item_info = {
                        "name": item_name,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size_bytes": item_stat.st_size if os.path.isfile(item_path) else None,
                        "last_modified": datetime.fromtimestamp(item_stat.st_mtime).isoformat()
                    }
                    
                    # Add extension for files
                    if os.path.isfile(item_path):
                        _, ext = os.path.splitext(item_name)
                        if ext:
                            item_info["extension"] = ext.lower()
                    
                    items.append(item_info)
                
                # Sort items: directories first, then files, both alphabetically
                items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
                
            except PermissionError:
                return {
                    "success": False,
                    "error": "Permission denied",
                    "directory_path": directory_path
                }
            
            return {
                "success": True,
                "directory_path": directory_path,
                "items": items,
                "total_items": len(items),
                "max_items_reached": len(items) == max_items,
                "include_hidden": include_hidden,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error listing directory {directory_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "directory_path": directory_path
            }
    
    def execute_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a function call from OpenAI.
        
        Args:
            function_name: Name of the function to call
            arguments: Function arguments
            
        Returns:
            JSON string with function results
        """
        try:
            if function_name == "search_knowledge_base":
                result = self.search_knowledge_base(
                    query=arguments.get("query", ""),
                    num_results=arguments.get("num_results", 5)
                )
            elif function_name == "get_database_info":
                result = self.get_database_info()
            elif function_name == "ask_detailed_question":
                result = self.ask_detailed_question(
                    question=arguments.get("question", ""),
                    num_chunks=arguments.get("num_chunks", 5)
                )
            elif function_name == "read_project_file":
                result = self.read_project_file(
                    file_path=arguments.get("file_path", ""),
                    max_lines=arguments.get("max_lines", 100)
                )
            elif function_name == "list_project_files":
                result = self.list_project_files(
                    directory_path=arguments.get("directory_path", "."),
                    include_hidden=arguments.get("include_hidden", False),
                    max_items=arguments.get("max_items", 50)
                )
            else:
                result = {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "function": function_name
            })
    
    def ask_question(self, question: str, conversation_context: bool = True) -> str:
        """
        Ask a question to the OpenAI agent with function calling capability.
        
        Args:
            question: The user's question
            conversation_context: Whether to include conversation history
            
        Returns:
            The agent's response
        """
        try:
            # Prepare messages
            messages = [{"role": "system", "content": self.system_message}]
            
            # Add conversation history if requested
            if conversation_context:
                messages.extend(self.conversation_history)
            
            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Make the initial API call with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",  # Let the model decide when to use tools
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Get the response message
            response_message = response.choices[0].message
            
            # Check if the model wants to call functions
            if response_message.tool_calls:
                # Add the assistant's response to messages
                messages.append(response_message)
                
                # Process each tool call
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"🔧 Calling {function_name} with args: {function_args}")
                    
                    # Execute the function
                    function_result = self.execute_function_call(function_name, function_args)
                    
                    # Add function result to messages
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_result
                    })
                
                # Get final response from the model
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature
                )
                
                final_answer = final_response.choices[0].message.content
                
            else:
                # No function calls needed
                final_answer = response_message.content
            
            # Update conversation history
            if conversation_context:
                self.conversation_history.append({"role": "user", "content": question})
                self.conversation_history.append({"role": "assistant", "content": final_answer})
                
                # Keep only last 10 exchanges to manage context length
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
            
            return final_answer
            
        except Exception as e:
            logger.error(f"Error in ask_question: {e}")
            return f"Sorry, I encountered an error while processing your question: {str(e)}"
    
    def interactive_mode(self):
        """Run the agent in interactive mode."""
        print("\n" + "=" * 60)
        print("🧠 CLI KNOWLEDGE AGENT - INTERACTIVE MODE")
        print("=" * 60)
        print("Ask questions and I'll use the knowledge base to help you!")
        print("Type 'quit', 'exit', or 'q' to stop.")
        print("Type 'clear' to clear conversation history.")
        print("Type 'info' to get database information.")
        print("-" * 60)
        
        try:
            while True:
                print()
                user_input = input("🤔 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("🧹 Conversation history cleared!")
                    continue
                
                if user_input.lower() == 'info':
                    db_info = self.get_database_info()
                    if db_info.get("success"):
                        info = db_info["database_info"]
                        print("📊 Database Information:")
                        for key, value in info.items():
                            if key != 'database_url':  # Don't show full URL
                                print(f"   {key}: {value}")
                    else:
                        print(f"❌ Error getting database info: {db_info.get('error', 'Unknown error')}")
                    continue
                
                if not user_input:
                    print("Please enter a question.")
                    continue
                
                print("\n🤖 Assistant: ", end="", flush=True)
                
                # Get response from the agent
                response = self.ask_question(user_input, conversation_context=True)
                print(response)
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"❌ An error occurred: {e}")

def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="CLI Knowledge Agent with OpenAI Function Calling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_knowledge_agent.py --question "What is vector search?"
  python cli_knowledge_agent.py --interactive
  python cli_knowledge_agent.py --question "How many documents are in the database?" --model gpt-4
        """
    )
    
    parser.add_argument(
        "--question", "-q",
        type=str,
        help="Ask a single question"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive mode"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=0.7,
        help="Response creativity 0.0-1.0 (default: 0.7)"
    )
    
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1500,
        help="Maximum tokens in response (default: 1500)"
    )
    
    parser.add_argument(
        "--no-context",
        action="store_true",
        help="Don't use conversation context (for single questions)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize the agent
        print("🚀 Initializing CLI Knowledge Agent...")
        agent = CLIKnowledgeAgent(
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens
        )
        
        print(f"✅ Agent initialized with model: {args.model}")
        
        if args.interactive:
            # Start interactive mode
            agent.interactive_mode()
            
        elif args.question:
            # Ask single question
            print(f"\n🤔 Question: {args.question}")
            print("-" * 50)
            
            response = agent.ask_question(
                args.question, 
                conversation_context=not args.no_context
            )
            
            print(f"\n🤖 Response:")
            print(response)
            
        else:
            # No arguments provided - show help and start interactive
            parser.print_help()
            print("\nStarting interactive mode...")
            agent.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n\n👋 Operation cancelled by user")
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
