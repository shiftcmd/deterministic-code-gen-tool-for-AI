#!/usr/bin/env python3
"""
AI Code Assistant

A practical command-line tool that generates clean, validated Python code
using the deterministic framework.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any
import yaml

# Import our framework components
from deterministic_code_framework import (
    DeterministicCodeGenerator, 
    GenerationType, 
    RiskLevel
)
from dev_validator import QuickValidator


class AICodeAssistant:
    """Command-line interface for AI code generation"""
    
    def __init__(self, config_file: str = ".ai_assistant.yml"):
        self.config = self._load_config(config_file)
        self._init_generator()
        self.validator = QuickValidator()
    
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "password"
            },
            "postgresql": {
                "connection_string": "postgresql://user:password@localhost/codedb"
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY")
            },
            "generation": {
                "default_type": "hybrid",
                "max_iterations": 3,
                "max_risk_level": "medium"
            },
            "output": {
                "save_to_file": True,
                "show_validation": True,
                "format_code": True
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                return {**default_config, **user_config}
        except FileNotFoundError:
            print(f"⚠️  Config file {config_file} not found, using defaults")
            return default_config
    
    def _init_generator(self):
        """Initialize the code generator"""
        try:
            self.generator = DeterministicCodeGenerator(
                neo4j_uri=self.config["neo4j"]["uri"],
                neo4j_user=self.config["neo4j"]["user"],
                neo4j_password=self.config["neo4j"]["password"],
                pg_connection_string=self.config["postgresql"]["connection_string"],
                openai_api_key=self.config["openai"]["api_key"]
            )
            print("✅ AI Code Generator initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize generator: {e}")
            print("💡 Check your configuration and ensure services are running")
            self.generator = None
    
    def generate_code(self, requirement: str, **kwargs) -> Dict[str, Any]:
        """Generate code from requirement"""
        if not self.generator:
            return {
                "success": False,
                "error": "Generator not initialized. Check configuration."
            }
        
        print(f"🤖 Generating code for: {requirement}")
        print("=" * 60)
        
        # Parse generation type
        gen_type_str = kwargs.get('type', self.config["generation"]["default_type"])
        gen_type = GenerationType(gen_type_str.lower())
        
        # Parse other parameters
        max_iterations = kwargs.get('iterations', self.config["generation"]["max_iterations"])
        context_files = kwargs.get('context', [])
        
        try:
            # Generate code
            code, validation = self.generator.generate_code(
                requirement=requirement,
                generation_type=gen_type,
                context_files=context_files,
                max_iterations=max_iterations
            )
            
            # Format output
            result = {
                "success": True,
                "code": code,
                "validation": {
                    "valid": validation.valid,
                    "confidence": validation.confidence,
                    "risk_level": validation.risk_level.value,
                    "issues": validation.issues,
                    "suggestions": validation.suggestions
                },
                "metadata": {
                    "generation_type": gen_type.value,
                    "iterations": max_iterations,
                    "requirement": requirement
                }
            }
            
            # Check if risk level is acceptable
            max_risk = self.config["generation"]["max_risk_level"]
            risk_acceptable = self._is_risk_acceptable(validation.risk_level, max_risk)
            
            if not risk_acceptable:
                result["warning"] = f"Risk level {validation.risk_level.value} exceeds maximum {max_risk}"
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_risk_acceptable(self, current_risk: RiskLevel, max_risk: str) -> bool:
        """Check if risk level is acceptable"""
        risk_order = {
            "low": 0,
            "medium": 1,
            "high": 2,
            "critical": 3
        }
        
        current_level = risk_order.get(current_risk.value, 3)
        max_level = risk_order.get(max_risk, 1)
        
        return current_level <= max_level
    
    def save_code(self, code: str, filename: str) -> bool:
        """Save generated code to file"""
        try:
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                f.write(code)
            
            print(f"💾 Code saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to save code: {e}")
            return False
    
    def validate_existing_file(self, filename: str) -> Dict[str, Any]:
        """Validate an existing Python file"""
        print(f"🔍 Validating: {filename}")
        
        valid, issues, metadata = self.validator.validate_file(filename)
        
        return {
            "file": filename,
            "valid": valid,
            "issues": issues,
            "metadata": metadata
        }
    
    def interactive_mode(self):
        """Start interactive code generation session"""
        print("\n🚀 AI Code Assistant - Interactive Mode")
        print("=" * 50)
        print("Type 'help' for commands or 'exit' to quit")
        
        while True:
            try:
                user_input = input("\n💡 What would you like to generate? ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                elif user_input.startswith('validate '):
                    filename = user_input[9:].strip()
                    result = self.validate_existing_file(filename)
                    self._display_validation_result(result)
                    continue
                
                elif not user_input:
                    continue
                
                # Generate code
                result = self.generate_code(user_input)
                self._display_result(result)
                
                if result["success"] and result["validation"]["valid"]:
                    save = input("\n💾 Save to file? (y/N): ").strip().lower()
                    if save in ['y', 'yes']:
                        filename = input("📁 Filename: ").strip()
                        if filename:
                            self.save_code(result["code"], filename)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show help information"""
        print("\n📚 Available Commands:")
        print("  help              - Show this help")
        print("  validate <file>   - Validate existing Python file")
        print("  exit/quit/q       - Exit the assistant")
        print("\n🔧 Generation Examples:")
        print("  'Create an API client for user management'")
        print("  'Build a data processor for CSV files'")
        print("  'Make a function that validates email addresses'")
    
    def _display_result(self, result: Dict[str, Any]):
        """Display generation result"""
        if not result["success"]:
            print(f"❌ Generation failed: {result['error']}")
            return
        
        validation = result["validation"]
        
        # Show status
        if validation["valid"]:
            print("✅ Code generated successfully!")
        else:
            print("⚠️  Code generated with issues")
        
        print(f"🎯 Confidence: {validation['confidence']:.1%}")
        print(f"⚠️  Risk Level: {validation['risk_level'].upper()}")
        
        # Show issues if any
        if validation["issues"]:
            print("\n🚨 Issues Found:")
            for issue in validation["issues"]:
                print(f"   • {issue}")
        
        # Show suggestions if any
        if validation["suggestions"]:
            print("\n💡 Suggestions:")
            for suggestion in validation["suggestions"]:
                print(f"   • {suggestion}")
        
        # Show code
        print(f"\n📝 Generated Code:")
        print("-" * 40)
        print(result["code"])
        print("-" * 40)
    
    def _display_validation_result(self, result: Dict[str, Any]):
        """Display file validation result"""
        if result["valid"]:
            print(f"✅ {result['file']} is valid")
        else:
            print(f"❌ {result['file']} has issues:")
            for issue in result["issues"]:
                print(f"   • {issue}")
        
        print(f"ℹ️  Risk Level: {result['metadata']['risk_level'].upper()}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="AI Code Assistant - Generate clean, validated Python code"
    )
    
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start interactive mode"
    )
    
    parser.add_argument(
        "-r", "--requirement",
        help="Code requirement to generate"
    )
    
    parser.add_argument(
        "-t", "--type",
        choices=["template", "ai_guided", "hybrid"],
        default="hybrid",
        help="Generation type"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path"
    )
    
    parser.add_argument(
        "-c", "--context",
        nargs="*",
        help="Context files to include"
    )
    
    parser.add_argument(
        "-v", "--validate",
        help="Validate existing Python file"
    )
    
    parser.add_argument(
        "--config",
        default=".ai_assistant.yml",
        help="Configuration file"
    )
    
    args = parser.parse_args()
    
    # Initialize assistant
    assistant = AICodeAssistant(args.config)
    
    try:
        if args.validate:
            # Validate existing file
            result = assistant.validate_existing_file(args.validate)
            assistant._display_validation_result(result)
            
        elif args.interactive:
            # Interactive mode
            assistant.interactive_mode()
            
        elif args.requirement:
            # Generate code from requirement
            result = assistant.generate_code(
                requirement=args.requirement,
                type=args.type,
                context=args.context or []
            )
            
            assistant._display_result(result)
            
            # Save if output specified
            if args.output and result["success"]:
                assistant.save_code(result["code"], args.output)
        
        else:
            # Default to interactive mode
            assistant.interactive_mode()
    
    finally:
        # Cleanup
        if hasattr(assistant, 'validator'):
            assistant.validator.close()


# Example configuration file content
EXAMPLE_CONFIG = """
# AI Code Assistant Configuration

neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "password"

postgresql:
  connection_string: "postgresql://user:password@localhost/codedb"

openai:
  api_key: "${OPENAI_API_KEY}"

generation:
  default_type: "hybrid"  # template, ai_guided, hybrid
  max_iterations: 3
  max_risk_level: "medium"  # low, medium, high, critical

output:
  save_to_file: true
  show_validation: true
  format_code: true
"""


if __name__ == "__main__":
    # Create example config if it doesn't exist
    config_path = ".ai_assistant.yml"
    if not Path(config_path).exists():
        print(f"📄 Creating example config file: {config_path}")
        with open(config_path, 'w') as f:
            f.write(EXAMPLE_CONFIG)
    
    main()