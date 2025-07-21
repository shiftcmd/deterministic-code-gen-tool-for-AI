#!/usr/bin/env python3
"""
Quick demonstration of the CLI Knowledge Agent functionality
"""

import os
import sys
from cli_knowledge_agent import CLIKnowledgeAgent

def run_demo():
    print("🧠 CLI Knowledge Agent Demonstration")
    print("=" * 50)
    
    try:
        # Initialize agent
        print("1. Initializing agent...")
        agent = CLIKnowledgeAgent()
        print("✅ Agent ready!\n")
        
        # Test questions
        questions = [
            "What is Supabase?",
            "Tell me about Python best practices",
            "How many documents are in the database?",
            "What are vector embeddings?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"{i}. Question: {question}")
            print("-" * 30)
            
            response = agent.ask_question(question, conversation_context=False)
            print(f"🤖 Answer: {response}\n")
            
            if i < len(questions):
                input("Press Enter for next question...")
                print()
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_demo()
