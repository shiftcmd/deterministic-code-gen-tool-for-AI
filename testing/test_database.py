#!/usr/bin/env python3
"""
Test script for the Framework Database and Configuration

Tests database functionality and Neo4j data copying.
"""

import json
import os
from pathlib import Path
from backend_api import DatabaseManager

def test_database_functionality():
    """Test database creation and functionality"""
    print("🔧 Testing Database Functionality\n")
    
    # Initialize database manager
    db_manager = DatabaseManager("test_framework.db")
    
    print("✅ Database initialized successfully")
    print(f"📂 Database location: {os.path.abspath(db_manager.db_path)}")
    
    # Test configuration
    print("\n📋 Testing Configuration:")
    
    # Get all config
    config = db_manager.get_all_config()
    print(f"   • Found {len(config)} configuration items")
    
    for key, value in config.items():
        print(f"   • {key}: {value['value']} ({value['type']})")
    
    # Test setting custom config
    db_manager.set_config("test_setting", "test_value", "string", "Test configuration")
    print("   • Added test configuration")
    
    # Create a test run
    print("\n🚀 Testing Run Creation:")
    test_files = ["test1.py", "test2.py", "test3.py"]
    run_id = db_manager.create_run("/test/project/path", test_files)
    print(f"   • Created run: {run_id}")
    
    # Update run status
    db_manager.update_run(run_id, status='completed')
    print("   • Updated run status to completed")
    
    # Add some logs
    db_manager.add_log(run_id, "INFO", "Test log message")
    db_manager.add_log(run_id, "DEBUG", "Another test message")
    print("   • Added test logs")
    
    # Save test results
    test_results = {
        "files_analyzed": 3,
        "issues_found": 0,
        "health_score": 95.5
    }
    db_manager.save_result(run_id, "test_analysis", test_results)
    print("   • Saved test results")
    
    # Retrieve and display data
    print("\n📊 Testing Data Retrieval:")
    
    runs = db_manager.get_runs()
    print(f"   • Found {len(runs)} runs")
    
    if runs:
        latest_run = runs[0]
        print(f"   • Latest run: {latest_run['id']} - {latest_run['status']}")
        print(f"   • Project: {latest_run['project_path']}")
        print(f"   • Files: {latest_run['file_count']}")
    
    # Test results retrieval
    results = db_manager.get_results(run_id)
    print(f"   • Retrieved {len(results)} result types")
    
    for result_type, data in results.items():
        print(f"     - {result_type}: {len(str(data))} characters")
    
    return db_manager, run_id

def test_neo4j_data_structure():
    """Test Neo4j data export structure"""
    print("\n🗂️  Testing Neo4j Export Structure:")
    
    # Create mock Neo4j data directory
    mock_neo4j_dir = Path("./mock_neo4j_data")
    mock_neo4j_dir.mkdir(exist_ok=True)
    
    # Create mock data files
    databases_dir = mock_neo4j_dir / "databases"
    databases_dir.mkdir(exist_ok=True)
    
    # Create mock database files
    (databases_dir / "neo4j").mkdir(exist_ok=True)
    (databases_dir / "neo4j" / "neostore").write_text("mock neo4j data")
    (databases_dir / "neo4j" / "schema").mkdir(exist_ok=True)
    
    print(f"   • Created mock Neo4j data at: {mock_neo4j_dir}")
    print(f"   • Data structure:")
    for item in mock_neo4j_dir.rglob("*"):
        if item.is_file():
            print(f"     - {item.relative_to(mock_neo4j_dir)}")
    
    return mock_neo4j_dir

def show_database_schema():
    """Show the database schema"""
    print("\n📋 Database Schema:")
    
    import sqlite3
    with sqlite3.connect("test_framework.db") as conn:
        cursor = conn.execute("""
            SELECT name, sql FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        
        for table_name, create_sql in tables:
            print(f"\n📊 Table: {table_name}")
            print("   Columns:")
            
            # Get column info
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                nullable = "NULL" if col[3] == 0 else "NOT NULL"
                default = f"DEFAULT {col[4]}" if col[4] else ""
                pk = "PRIMARY KEY" if col[5] == 1 else ""
                
                print(f"     • {col_name} {col_type} {nullable} {default} {pk}".strip())

def show_exports_directory():
    """Show the exports directory structure"""
    print("\n📁 Exports Directory Structure:")
    
    exports_dir = Path("./exports")
    if exports_dir.exists():
        print(f"   📂 {exports_dir}")
        for item in exports_dir.rglob("*"):
            depth = len(item.relative_to(exports_dir).parts)
            indent = "   " + "  " * depth
            icon = "📁" if item.is_dir() else "📄"
            print(f"{indent}{icon} {item.name}")
    else:
        print("   • No exports directory found")

def main():
    """Main test function"""
    print("🧪 Framework Database & Configuration Test\n")
    
    try:
        # Test database functionality
        db_manager, run_id = test_database_functionality()
        
        # Test Neo4j structure
        mock_neo4j_dir = test_neo4j_data_structure()
        
        # Show database schema
        show_database_schema()
        
        # Show exports directory
        show_exports_directory()
        
        print("\n✅ All tests completed successfully!")
        
        print(f"\n📍 Important Locations:")
        print(f"   • Database: {os.path.abspath(db_manager.db_path)}")
        print(f"   • Mock Neo4j: {os.path.abspath(mock_neo4j_dir)}")
        print(f"   • Test Run ID: {run_id}")
        
        print(f"\n🔍 To inspect the database:")
        print(f"   sqlite3 {os.path.abspath(db_manager.db_path)}")
        print(f"   .tables")
        print(f"   SELECT * FROM runs;")
        print(f"   SELECT * FROM framework_config;")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()