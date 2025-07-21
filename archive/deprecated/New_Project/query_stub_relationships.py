#!/usr/bin/env python3
"""
Query script to show relationships between .pyi stub files and their implementations
"""

import asyncio

from neo4j import AsyncGraphDatabase


async def query_stub_relationships():
    """Query Neo4j to show relationships between stub files and implementations"""

    # Neo4j connection parameters
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "no_auth"

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    try:
        async with driver.session() as session:
            print("🔍 Querying stub file relationships...\n")

            # 1. Show file-level validation relationships
            print("📄 FILE-LEVEL VALIDATION RELATIONSHIPS:")
            print("=" * 50)
            result = await session.run(
                """
                MATCH (stub:File {is_stub_file: true})-[:VALIDATES]->(impl:File {is_stub_file: false})
                RETURN stub.path as stub_file, impl.path as impl_file, stub.module_name as module
                ORDER BY module
            """
            )

            async for record in result:
                data = record.data()
                print(f"📝 {data['module']}")
                print(f"   Stub: {data['stub_file']}")
                print(f"   Impl: {data['impl_file']}")
                print()

            # 2. Show method-level validation relationships
            print("\n⚙️  METHOD-LEVEL VALIDATION RELATIONSHIPS:")
            print("=" * 50)
            result = await session.run(
                """
                MATCH (stub:Method {is_stub_definition: true})-[:VALIDATES_METHOD]->(impl:Method {is_stub_definition: false})
                RETURN stub.class as class_name, stub.name as method_name,
                       stub.signature as stub_signature, impl.signature as impl_signature,
                       stub.from_file as stub_file, impl.from_file as impl_file
                ORDER BY class_name, method_name
            """
            )

            method_count = 0
            async for record in result:
                data = record.data()
                method_count += 1
                print(f"🔧 {data['class_name']}.{data['method_name']}")
                print(f"   Stub signature: {data['stub_signature']}")
                print(f"   Impl signature: {data['impl_signature']}")
                print(f"   Files: {data['stub_file']} → {data['impl_file']}")
                print()

            if method_count == 0:
                print("   No method validation relationships found")

            # 3. Show function-level validation relationships
            print(f"\n🔧 FUNCTION-LEVEL VALIDATION RELATIONSHIPS:")
            print("=" * 50)
            result = await session.run(
                """
                MATCH (stub:Function {is_stub_definition: true})-[:VALIDATES_FUNCTION]->(impl:Function {is_stub_definition: false})
                RETURN stub.module as module, stub.name as function_name,
                       stub.signature as stub_signature, impl.signature as impl_signature,
                       stub.from_file as stub_file, impl.from_file as impl_file
                ORDER BY module, function_name
            """
            )

            function_count = 0
            async for record in result:
                data = record.data()
                function_count += 1
                print(f"⚡ {data['module']}.{data['function_name']}")
                print(f"   Stub signature: {data['stub_signature']}")
                print(f"   Impl signature: {data['impl_signature']}")
                print(f"   Files: {data['stub_file']} → {data['impl_file']}")
                print()

            if function_count == 0:
                print("   No function validation relationships found")

            # 4. Show class-level validation relationships
            print(f"\n🏗️  CLASS-LEVEL VALIDATION RELATIONSHIPS:")
            print("=" * 50)
            result = await session.run(
                """
                MATCH (stub:Class {is_from_stub: true})-[:VALIDATES_CLASS]->(impl:Class {is_from_stub: false})
                RETURN stub.module as module, stub.name as class_name,
                       stub.from_file as stub_file, impl.from_file as impl_file
                ORDER BY module, class_name
            """
            )

            class_count = 0
            async for record in result:
                data = record.data()
                class_count += 1
                print(f"🏛️  {data['module']}.{data['class_name']}")
                print(f"   Files: {data['stub_file']} → {data['impl_file']}")
                print()

            if class_count == 0:
                print("   No class validation relationships found")

            # 5. Show summary of stub files and what they impact
            print(f"\n📊 STUB FILES IMPACT SUMMARY:")
            print("=" * 50)
            result = await session.run(
                """
                MATCH (stub:File {is_stub_file: true})
                OPTIONAL MATCH (stub)-[:DEFINES]->(c:Class)
                OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method {is_from_stub: true})
                OPTIONAL MATCH (stub)-[:DEFINES]->(f:Function {is_from_stub: true})
                RETURN stub.path as stub_file, stub.module_name as module,
                       count(DISTINCT c) as classes_defined,
                       count(DISTINCT m) as methods_defined,
                       count(DISTINCT f) as functions_defined
                ORDER BY module
            """
            )

            async for record in result:
                data = record.data()
                print(f"📋 {data['module']} ({data['stub_file']})")
                print(f"   Classes: {data['classes_defined']}")
                print(f"   Methods: {data['methods_defined']}")
                print(f"   Functions: {data['functions_defined']}")
                print()

    finally:
        await driver.close()


async def main():
    print("🚀 Starting stub relationship query...\n")
    await query_stub_relationships()
    print("✅ Query completed!")


if __name__ == "__main__":
    asyncio.run(main())
