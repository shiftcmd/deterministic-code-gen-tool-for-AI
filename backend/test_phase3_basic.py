#!/usr/bin/env python3
"""
Basic Phase 3 Integration Test

Tests the core Phase 3 components to ensure they work correctly.
"""

import asyncio
import logging
import sys
import tempfile
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_neo4j_manager():
    """Test Neo4j Manager components."""
    logger.info("=== Testing Neo4j Manager ===")
    
    try:
        from neo4j_manager import BackupService, DatabaseTracker, BackupManager
        
        # Test BackupService initialization
        backup_service = BackupService()
        logger.info("✓ BackupService initialized")
        
        # Test DatabaseTracker initialization
        database_tracker = DatabaseTracker()
        logger.info("✓ DatabaseTracker initialized")
        
        # Test BackupManager initialization
        backup_manager = BackupManager()
        logger.info("✓ BackupManager initialized")
        
        # Test listing backups (should be empty initially)
        backups = await database_tracker.list_all_backups()
        logger.info(f"✓ Listed backups: {len(backups)} found")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Neo4j Manager test failed: {e}")
        return False


async def test_uploader():
    """Test Uploader components."""
    logger.info("=== Testing Uploader ===")
    
    try:
        from uploader import ValidationService, BatchUploader
        from uploader.core.neo4j_client import NEO4J_AVAILABLE
        
        # Test ValidationService
        validator = ValidationService()
        logger.info("✓ ValidationService initialized")
        
        # Test with sample Cypher content
        sample_cypher = """
        // Sample Cypher commands
        CREATE (n:TestNode {name: "test"});
        CREATE (m:TestNode {name: "test2"});
        CREATE (n)-[:TEST_REL]->(m);
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cypher', delete=False) as f:
            f.write(sample_cypher)
            temp_file = f.name
        
        try:
            # Test validation
            validation_result = await validator.validate_cypher_file(temp_file)
            logger.info(f"✓ Validation result: valid={validation_result.is_valid}, "
                       f"commands={validation_result.total_commands}")
            
            if NEO4J_AVAILABLE:
                # Only test Neo4jClient if Neo4j driver is available
                from uploader import Neo4jClient
                
                # Test Neo4jClient initialization (won't connect without Neo4j running)
                try:
                    neo4j_client = Neo4jClient()
                    logger.info("✓ Neo4jClient initialized")
                    
                    # Test BatchUploader initialization
                    uploader = BatchUploader(neo4j_client)
                    logger.info("✓ BatchUploader initialized")
                    
                except Exception as e:
                    if "connection" in str(e).lower() or "unavailable" in str(e).lower():
                        logger.info("✓ Neo4jClient/BatchUploader - No connection (expected without running Neo4j)")
                    else:
                        raise
            else:
                logger.info("✓ Neo4j driver not available - skipping connection tests")
                
        finally:
            # Clean up temp file
            Path(temp_file).unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Uploader test failed: {e}")
        return False


async def test_config_integration():
    """Test configuration integration."""
    logger.info("=== Testing Configuration ===")
    
    try:
        from config import get_settings
        
        settings = get_settings()
        neo4j_config = settings.get_neo4j_config()
        
        logger.info(f"✓ Neo4j URI: {neo4j_config['uri']}")
        logger.info(f"✓ Neo4j Database: {neo4j_config['database']}")
        logger.info(f"✓ Neo4j Backup Dir: {settings.database.neo4j_backup_dir}")
        
        # Check if backup directory exists
        backup_dir = Path(settings.database.neo4j_backup_dir)
        if backup_dir.exists():
            logger.info(f"✓ Backup directory exists: {backup_dir}")
        else:
            logger.info(f"✓ Backup directory will be created: {backup_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


async def test_models():
    """Test Phase 3 models."""
    logger.info("=== Testing Models ===")
    
    try:
        from neo4j_manager.models import BackupResult, BackupMetadata
        from uploader.models import UploadResult, ValidationResult
        
        # Test BackupResult
        backup_result = BackupResult(job_id="test_job")
        backup_result.success = True
        backup_result.backup_size_bytes = 1024000
        logger.info(f"✓ BackupResult: size_mb={backup_result.size_mb}")
        
        # Test UploadResult
        upload_result = UploadResult(job_id="test_job")
        upload_result.nodes_created = 10
        upload_result.relationships_created = 5
        logger.info(f"✓ UploadResult: completion={upload_result.completion_percentage}%")
        
        # Test ValidationResult
        validation_result = ValidationResult(is_valid=True, file_path="/test/path")
        validation_result.total_commands = 3
        validation_result.estimated_nodes = 2
        logger.info(f"✓ ValidationResult: commands={validation_result.total_commands}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Models test failed: {e}")
        return False


async def main():
    """Run all Phase 3 tests."""
    logger.info("Starting Phase 3 Basic Integration Tests")
    logger.info("=" * 50)
    
    tests = [
        ("Configuration", test_config_integration),
        ("Models", test_models),
        ("Neo4j Manager", test_neo4j_manager),
        ("Uploader", test_uploader),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
        
        logger.info("")  # Empty line between tests
    
    # Summary
    logger.info("=" * 50)
    logger.info("Phase 3 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Phase 3 basic tests passed!")
        logger.info("\nNext steps:")
        logger.info("1. Install Neo4j driver: pip install neo4j")
        logger.info("2. Start Neo4j database")
        logger.info("3. Run end-to-end integration tests")
        logger.info("4. Test with frontend UI")
    else:
        logger.info("❌ Some tests failed - check implementation")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())