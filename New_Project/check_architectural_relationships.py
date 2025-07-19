#!/usr/bin/env python3
"""
Check if architectural relationships are being created in the knowledge graph
"""
import asyncio
import os

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase


async def check_architectural_relationships():
    """Check architectural relationships in the database"""
    load_dotenv()

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "no_auth")

    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    try:
        async with driver.session() as session:
            # Check if hexagonal architectural metadata is present
            print("🔍 Checking hexagonal architectural metadata:")

            # Check classes with architectural information
            result = await session.run(
                """
                MATCH (c:Class)
                WHERE c.architectural_type IS NOT NULL
                RETURN
                    c.name as class_name,
                    c.architectural_type as arch_type,
                    c.layer as layer,
                    c.hexagonal_role as hex_role,
                    c.arch_confidence as confidence
                LIMIT 10
            """
            )

            classes_with_arch = []
            async for record in result:
                classes_with_arch.append(
                    {
                        "name": record["class_name"],
                        "arch_type": record["arch_type"],
                        "layer": record["layer"],
                        "hex_role": record["hex_role"],
                        "confidence": record["confidence"],
                    }
                )

            print(
                f"   Found {len(classes_with_arch)} classes with architectural metadata"
            )
            for cls in classes_with_arch[:5]:
                print(
                    f"      {cls['name']}: {cls['arch_type']} ({cls['layer']} layer, {cls['hex_role']})"
                )

            # Check files with architectural information
            print("\n🔍 Checking files with architectural metadata:")
            result = await session.run(
                """
                MATCH (f:File)
                WHERE f.dominant_layer IS NOT NULL
                RETURN
                    f.name as file_name,
                    f.dominant_layer as layer,
                    f.component_count as components,
                    f.cyclomatic_complexity as complexity
                LIMIT 10
            """
            )

            files_with_arch = []
            async for record in result:
                files_with_arch.append(
                    {
                        "name": record["file_name"],
                        "layer": record["layer"],
                        "components": record["components"],
                        "complexity": record["complexity"],
                    }
                )

            print(f"   Found {len(files_with_arch)} files with architectural metadata")
            for file in files_with_arch[:5]:
                print(
                    f"      {file['name']}: {file['layer']} layer ({file['components']} components, {file['complexity']} complexity)"
                )

            # Check architectural relationships
            print("\n🔍 Checking architectural relationships:")

            # Check INHERITS_FROM relationships
            result = await session.run(
                """
                MATCH (child:Class)-[r:INHERITS_FROM]->(parent:Class)
                RETURN count(r) as inheritance_count
            """
            )
            inheritance_count = await result.single()
            print(
                f"   Inheritance relationships: {inheritance_count['inheritance_count']}"
            )

            # Check DEPENDS_ON relationships
            result = await session.run(
                """
                MATCH (source:Class)-[r:DEPENDS_ON]->(target:Class)
                RETURN count(r) as dependency_count
            """
            )
            dependency_count = await result.single()
            print(
                f"   Dependency relationships: {dependency_count['dependency_count']}"
            )

            # Show some sample relationships
            if inheritance_count["inheritance_count"] > 0:
                print("\n   Sample inheritance relationships:")
                result = await session.run(
                    """
                    MATCH (child:Class)-[r:INHERITS_FROM]->(parent:Class)
                    RETURN child.name as child_name, parent.name as parent_name, r.confidence as confidence
                    LIMIT 5
                """
                )
                async for record in result:
                    print(
                        f"      {record['child_name']} -> {record['parent_name']} (confidence: {record['confidence']})"
                    )

            if dependency_count["dependency_count"] > 0:
                print("\n   Sample dependency relationships:")
                result = await session.run(
                    """
                    MATCH (source:Class)-[r:DEPENDS_ON]->(target:Class)
                    RETURN source.name as source_name, target.name as target_name,
                           r.source_layer as source_layer, r.target_layer as target_layer
                    LIMIT 5
                """
                )
                async for record in result:
                    print(
                        f"      {record['source_name']} ({record['source_layer']}) -> {record['target_name']} ({record['target_layer']})"
                    )

            # Check architectural layer distribution
            print("\n🔍 Checking architectural layer distribution:")
            result = await session.run(
                """
                MATCH (c:Class)
                WHERE c.layer IS NOT NULL
                RETURN c.layer as layer, count(c) as count
                ORDER BY count DESC
            """
            )

            layer_distribution = {}
            async for record in result:
                layer_distribution[record["layer"]] = record["count"]

            if layer_distribution:
                print("   Layer distribution:")
                for layer, count in layer_distribution.items():
                    print(f"      {layer}: {count} classes")
            else:
                print("   No layer distribution found")

            # Check hexagonal role distribution
            print("\n🔍 Checking hexagonal role distribution:")
            result = await session.run(
                """
                MATCH (c:Class)
                WHERE c.hexagonal_role IS NOT NULL
                RETURN c.hexagonal_role as role, count(c) as count
                ORDER BY count DESC
            """
            )

            role_distribution = {}
            async for record in result:
                role_distribution[record["role"]] = record["count"]

            if role_distribution:
                print("   Hexagonal role distribution:")
                for role, count in role_distribution.items():
                    print(f"      {role}: {count} classes")
            else:
                print("   No hexagonal role distribution found")

    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(check_architectural_relationships())
