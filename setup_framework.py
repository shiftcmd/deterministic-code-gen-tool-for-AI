#!/usr/bin/env python3
"""
Setup script for the Deterministic AI Code Generation Framework

This script helps set up the framework components and validates the environment.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple
import time

def run_command(command: str, description: str) -> Tuple[bool, str]:
    """Run a shell command and return success status and output"""
    print(f"⚡ {description}...")
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {description} completed")
            return True, result.stdout
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out")
        return False, "Command timed out"
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False, str(e)

def check_python_version() -> bool:
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} is not supported. Requires Python 3.8+")
        return False

def install_dependencies() -> bool:
    """Install required Python packages"""
    print("📦 Installing Python dependencies...")
    
    # Check if requirements file exists
    req_file = "requirements_framework.txt"
    if not Path(req_file).exists():
        print(f"❌ Requirements file {req_file} not found")
        return False
    
    success, output = run_command(
        f"pip install -r {req_file}",
        "Installing dependencies"
    )
    return success

def check_services() -> Dict[str, bool]:
    """Check if required services are running"""
    print("🔧 Checking required services...")
    
    services = {
        "neo4j": False,
        "postgresql": False
    }
    
    # Check Neo4j
    try:
        import neo4j
        driver = neo4j.GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        with driver.session() as session:
            session.run("RETURN 1")
        services["neo4j"] = True
        print("✅ Neo4j is running and accessible")
        driver.close()
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
    
    # Check PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://postgres:password@localhost/postgres"
        )
        conn.close()
        services["postgresql"] = True
        print("✅ PostgreSQL is running and accessible")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
    
    return services

def setup_docker_services() -> bool:
    """Set up Docker services for Neo4j and PostgreSQL"""
    print("🐳 Setting up Docker services...")
    
    # Check if Docker is available
    success, _ = run_command("docker --version", "Checking Docker")
    if not success:
        print("❌ Docker is not available. Please install Docker first.")
        return False
    
    # Start Neo4j
    print("🚀 Starting Neo4j container...")
    success, _ = run_command(
        "docker run -d --name neo4j-framework -p 7474:7474 -p 7687:7687 "
        "-e NEO4J_AUTH=neo4j/password neo4j:latest",
        "Starting Neo4j"
    )
    
    if not success:
        # Try to start existing container
        run_command("docker start neo4j-framework", "Starting existing Neo4j container")
    
    # Start PostgreSQL
    print("🚀 Starting PostgreSQL container...")
    success, _ = run_command(
        "docker run -d --name postgres-framework -p 5432:5432 "
        "-e POSTGRES_PASSWORD=password postgres:latest",
        "Starting PostgreSQL"
    )
    
    if not success:
        # Try to start existing container
        run_command("docker start postgres-framework", "Starting existing PostgreSQL container")
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(10)
    
    return True

def create_config_files() -> bool:
    """Create configuration files if they don't exist"""
    print("📄 Creating configuration files...")
    
    configs = {
        ".ai_assistant.yml": '''# AI Code Assistant Configuration
neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "password"

postgresql:
  connection_string: "postgresql://postgres:password@localhost/postgres"

openai:
  api_key: "${OPENAI_API_KEY}"

generation:
  default_type: "hybrid"
  max_iterations: 3
  max_risk_level: "medium"

output:
  save_to_file: true
  show_validation: true
  format_code: true
''',
        ".validator.yml": '''# Validator Configuration
neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "password"

validation:
  check_imports: true
  check_methods: true
  check_hallucinations: true
  max_risk_level: "medium"

patterns:
  suspicious_prefixes:
    - "auto_"
    - "smart_"
    - "enhanced_"
    - "magic_"
  
  blocked_imports:
    - "magic"
    - "utils.helpers"
  
  placeholder_patterns:
    - "TODO"
    - "FIXME"
    - "Your code here"
    - "..."
''',
        ".env.example": '''# Environment Variables for AI Framework
OPENAI_API_KEY=your_openai_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
POSTGRES_CONNECTION=postgresql://postgres:password@localhost/postgres
'''
    }
    
    created_count = 0
    for filename, content in configs.items():
        if not Path(filename).exists():
            with open(filename, 'w') as f:
                f.write(content)
            print(f"✅ Created {filename}")
            created_count += 1
        else:
            print(f"ℹ️  {filename} already exists")
    
    return created_count > 0

def setup_database_schema() -> bool:
    """Set up database schema for the framework"""
    print("🗄️  Setting up database schema...")
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            "postgresql://postgres:password@localhost/postgres"
        )
        cursor = conn.cursor()
        
        # Create tables for storing generated code and validation results
        schema_sql = '''
        CREATE TABLE IF NOT EXISTS generated_code (
            id SERIAL PRIMARY KEY,
            code TEXT NOT NULL,
            valid BOOLEAN NOT NULL,
            confidence FLOAT NOT NULL,
            risk_level VARCHAR(20) NOT NULL,
            issues JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS validation_runs (
            id SERIAL PRIMARY KEY,
            file_path TEXT NOT NULL,
            valid BOOLEAN NOT NULL,
            issues JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_generated_code_created_at ON generated_code(created_at);
        CREATE INDEX IF NOT EXISTS idx_validation_runs_file_path ON validation_runs(file_path);
        '''
        
        cursor.execute(schema_sql)
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database schema created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database schema: {e}")
        return False

def create_knowledge_graph_schema() -> bool:
    """Create basic knowledge graph schema in Neo4j"""
    print("🕸️  Setting up knowledge graph schema...")
    
    try:
        import neo4j
        driver = neo4j.GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        
        with driver.session() as session:
            # Create constraints and indexes
            queries = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Module) REQUIRE m.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.name IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Function) REQUIRE f.name IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR (m:Module) ON (m.domain)",
                "CREATE INDEX IF NOT EXISTS FOR (c:Class) ON (c.layer)",
                "CREATE INDEX IF NOT EXISTS FOR (f:Function) ON (f.signature)"
            ]
            
            for query in queries:
                session.run(query)
            
            # Add some basic Python standard library modules
            basic_modules = [
                "os", "sys", "json", "re", "time", "datetime", "typing",
                "pathlib", "collections", "itertools", "functools"
            ]
            
            for module in basic_modules:
                session.run(
                    "MERGE (m:Module {name: $name, type: 'stdlib'})",
                    name=module
                )
        
        driver.close()
        print("✅ Knowledge graph schema created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create knowledge graph schema: {e}")
        return False

def run_tests() -> bool:
    """Run basic tests to validate the setup"""
    print("🧪 Running setup validation tests...")
    
    try:
        # Test imports
        print("  Testing imports...")
        import neo4j
        import psycopg2
        import openai
        import yaml
        print("  ✅ All required packages imported successfully")
        
        # Test configuration loading
        print("  Testing configuration...")
        if Path(".ai_assistant.yml").exists():
            with open(".ai_assistant.yml", 'r') as f:
                config = yaml.safe_load(f)
            print("  ✅ Configuration file loaded successfully")
        
        # Test database connections
        print("  Testing database connections...")
        services = check_services()
        if services["neo4j"] and services["postgresql"]:
            print("  ✅ Database connections working")
        else:
            print("  ⚠️  Some database connections failed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Deterministic AI Code Generation Framework Setup")
    print("=" * 60)
    
    success_count = 0
    total_steps = 8
    
    # Step 1: Check Python version
    if check_python_version():
        success_count += 1
    
    # Step 2: Install dependencies
    if install_dependencies():
        success_count += 1
    
    # Step 3: Setup Docker services
    if setup_docker_services():
        success_count += 1
    
    # Step 4: Create config files
    if create_config_files():
        success_count += 1
    else:
        success_count += 1  # Still count as success if files exist
    
    # Step 5: Check services
    services = check_services()
    if any(services.values()):
        success_count += 1
    
    # Step 6: Setup database schema
    if setup_database_schema():
        success_count += 1
    
    # Step 7: Setup knowledge graph schema
    if create_knowledge_graph_schema():
        success_count += 1
    
    # Step 8: Run tests
    if run_tests():
        success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Setup Summary: {success_count}/{total_steps} steps completed")
    
    if success_count == total_steps:
        print("🎉 Setup completed successfully!")
        print("\n📚 Next steps:")
        print("  1. Set your OpenAI API key in .env file")
        print("  2. Run: python ai_code_assistant.py --interactive")
        print("  3. Try: python dev_validator.py example_file.py")
    else:
        print("⚠️  Setup completed with some issues.")
        print("   Check the error messages above and resolve them.")
    
    print("\n📖 See DETERMINISTIC_AI_FRAMEWORK.md for detailed usage instructions")

if __name__ == "__main__":
    main()