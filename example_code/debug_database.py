#!/usr/bin/env python3
"""
Debug script to check what's in the Neo4j database
"""
import asyncio
import os
from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase

async def debug_database():
    """Debug what's in the database"""
    load_dotenv()
    
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USER', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'no_auth')
    
    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        async with driver.session() as session:
            # Check codebase
            print("🔍 Checking Codebase nodes:")
            result = await session.run("MATCH (c:Codebase) RETURN c.name as name")
            codebases = [record['name'] async for record in result]
            print(f"   Found codebases: {codebases}")
            
            if codebases:
                repo_name = codebases[0]
                print(f"\n🔍 Checking relationships for {repo_name}:")
                
                # Check files
                result = await session.run("""
                    MATCH (c:Codebase {name: $repo_name})-[:CONTAINS]->(f:File)
                    RETURN count(f) as file_count
                """, repo_name=repo_name)
                file_count = await result.single()
                print(f"   Files: {file_count['file_count']}")
                
                # Check classes
                result = await session.run("""
                    MATCH (c:Codebase {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(cls:Class)
                    RETURN count(cls) as class_count
                """, repo_name=repo_name)
                class_count = await result.single()
                print(f"   Classes: {class_count['class_count']}")
                
                # Check methods
                result = await session.run("""
                    MATCH (c:Codebase {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(cls:Class)-[:HAS_METHOD]->(m:Method)
                    RETURN count(m) as method_count
                """, repo_name=repo_name)
                method_count = await result.single()
                print(f"   Methods: {method_count['method_count']}")
                
                # Check functions
                result = await session.run("""
                    MATCH (c:Codebase {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(func:Function)
                    RETURN count(func) as function_count
                """, repo_name=repo_name)
                function_count = await result.single()
                print(f"   Functions: {function_count['function_count']}")
                
                # Show some sample classes
                print(f"\n🔍 Sample classes:")
                result = await session.run("""
                    MATCH (c:Codebase {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(cls:Class)
                    RETURN cls.name as class_name, cls.module as module, f.name as file_name
                    LIMIT 5
                """, repo_name=repo_name)
                async for record in result:
                    print(f"   {record['class_name']} in {record['module']} ({record['file_name']})")
                
                # Show some sample methods  
                print(f"\n🔍 Sample methods:")
                result = await session.run("""
                    MATCH (c:Codebase {name: $repo_name})-[:CONTAINS]->(f:File)-[:DEFINES]->(cls:Class)-[:HAS_METHOD]->(m:Method)
                    RETURN m.name as method_name, cls.name as class_name, f.name as file_name
                    LIMIT 5
                """, repo_name=repo_name)
                async for record in result:
                    print(f"   {record['method_name']} in {record['class_name']} ({record['file_name']})")
                
                # Debug the problematic query
                print(f"\n🔍 Testing the problematic query:")
                stats_result = await session.run(f"""
                    MATCH (c:Codebase {{name: '{repo_name}'}})
                    OPTIONAL MATCH (r)-[:CONTAINS]->(f:File)
                    OPTIONAL MATCH (stub:File {{is_stub_file: true}})
                    OPTIONAL MATCH (impl:File {{is_stub_file: false}})
                    OPTIONAL MATCH (f)-[:DEFINES]->(c:Class)
                    OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
                    OPTIONAL MATCH (f)-[:DEFINES]->(func:Function)
                    OPTIONAL MATCH (stub)-[:VALIDATES]->(impl)
                    RETURN 
                        count(DISTINCT f) as total_files,
                        count(DISTINCT stub) as stub_files,
                        count(DISTINCT impl) as implementation_files,
                        count(DISTINCT c) as classes,
                        count(DISTINCT m) as methods,
                        count(DISTINCT func) as functions,
                        count(DISTINCT stub) as validation_relationships,
                        r.has_stubs as has_stubs
                """)
                
                record = await stats_result.single()
                if record:
                    print(f"   PROBLEMATIC QUERY Results:")
                    print(f"      Total files: {record['total_files']}")
                    print(f"      Classes: {record['classes']}")
                    print(f"      Methods: {record['methods']}")
                    print(f"      Functions: {record['functions']}")
                
                # Test the corrected query
                print(f"\n🔍 Testing the corrected query:")
                corrected_result = await session.run(f"""
                    MATCH (c:Codebase {{name: '{repo_name}'}})
                    OPTIONAL MATCH (c)-[:CONTAINS]->(f:File)
                    OPTIONAL MATCH (stub:File {{is_stub_file: true}})
                    OPTIONAL MATCH (impl:File {{is_stub_file: false}})
                    OPTIONAL MATCH (f)-[:DEFINES]->(cls:Class)
                    OPTIONAL MATCH (cls)-[:HAS_METHOD]->(m:Method)
                    OPTIONAL MATCH (f)-[:DEFINES]->(func:Function)
                    OPTIONAL MATCH (stub)-[:VALIDATES]->(impl)
                    RETURN 
                        count(DISTINCT f) as total_files,
                        count(DISTINCT stub) as stub_files,
                        count(DISTINCT impl) as implementation_files,
                        count(DISTINCT cls) as classes,
                        count(DISTINCT m) as methods,
                        count(DISTINCT func) as functions,
                        count(DISTINCT stub) as validation_relationships,
                        c.has_stubs as has_stubs
                """)
                
                record = await corrected_result.single()
                if record:
                    print(f"   CORRECTED QUERY Results:")
                    print(f"      Total files: {record['total_files']}")
                    print(f"      Classes: {record['classes']}")
                    print(f"      Methods: {record['methods']}")
                    print(f"      Functions: {record['functions']}")
                    
    finally:
        await driver.close()

if __name__ == "__main__":
    asyncio.run(debug_database())