#!/usr/bin/env python3
"""
Simple Folder Processing for Embeddings and AI Tagging

One script that does everything:
1. Copy folder to temp directory
2. Chunk Python files semantically 
3. Generate embeddings
4. Store in Supabase
5. Optionally apply AI-driven architectural tags

Usage: python process_folder_for_embeddings.py <folder_path>
"""

import os
import sys
import json
import shutil
import tempfile
import ast
import hashlib
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from dotenv import load_dotenv

# Suppress syntax warnings from processed files
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Load environment variables from .env file
project_root = Path(__file__).resolve().parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path, override=True)

# Import existing utilities
from src.utils import (
    get_supabase_client,
    create_embeddings_batch,
    create_embedding,
    openai_client
)

@dataclass
class SimpleCodeChunk:
    """Simple code chunk for embedding."""
    chunk_id: str
    project_name: str  # Name of the project/codebase this chunk belongs to
    file_name: str  # Just the file name with extension
    relative_path: str  # Path relative to the project root
    chunk_type: str  # 'function', 'class', 'module'
    name: str
    code: str
    docstring: Optional[str]
    architectural_layer: str
    embedding_text: str
    file_hash: Optional[str] = None
    embedding: Optional[List[float]] = None

class SimpleFolderProcessor:
    """Simple processor that handles the entire pipeline."""
    
    def __init__(self, hash_cache_path: Optional[str] = None):
        """Initialize the processor.
        
        Args:
            hash_cache_path: Optional path to the hash cache file. If not provided,
                           uses CODE_HASH_CACHE_PATH env var or defaults to .code_hashes.json
        """
        self.supabase_client = get_supabase_client()
        self.temp_dir = None
        self.project_root = None
        self.project_name = None
        self.project_id = None
        self.run_id = None
        
        # Set up hash cache path
        if hash_cache_path:
            self.hash_cache_path = Path(hash_cache_path)
        else:
            # Check environment variable
            env_path = os.getenv('CODE_HASH_CACHE_PATH')
            if env_path:
                self.hash_cache_path = Path(env_path)
            else:
                # Default to .code_hashes.json in current directory
                self.hash_cache_path = Path('.code_hashes.json')
        
        # Load existing hash cache
        self.hash_cache = self._load_hash_cache()
        
    def process_folder(self, folder_path: str, duplicate_strategy: str = 'skip', project_description: str = None, clean_import: bool = False) -> Dict[str, Any]:
        """Main processing pipeline."""
        
        print(f"🚀 Starting processing for folder: {folder_path}")
        
        # Set project root to original folder path
        self.project_root = Path(folder_path)
        
        # Extract project name from the folder path
        self.project_name = Path(folder_path).name
        print(f"📂 Project name: {self.project_name}")
        
        # If clean_import (--replace mode), clear the hash cache for this project
        if clean_import:
            self.hash_cache = self._create_empty_cache()
            print(f"🔄 Cleared hash cache for full replacement")
        
        # Create or find project and start a new run
        project_setup = self._setup_project_and_run(folder_path, project_description, clean_import, duplicate_strategy)
        if not project_setup['success']:
            return project_setup
        
        # Step 1: Copy to temp directory
        print("📁 Step 1: Copying folder to temp directory...")
        self.temp_dir = self._copy_to_temp(folder_path)
        print(f"✅ Copied to: {self.temp_dir}")
        
        # Step 2: Detect deletions and moves (only in incremental mode)
        if not clean_import:
            print("🔍 Step 2: Detecting file changes...")
            file_changes = self._detect_deletions_and_moves()
            
            # Handle deletions
            if file_changes['deletions']:
                print(f"🗑️ Detected {len(file_changes['deletions'])} deleted files")
                self._handle_deletions(file_changes['deletions'])
            
            # Handle moves
            if file_changes['moves']:
                print(f"📦 Detected {len(file_changes['moves'])} moved/renamed files")
                self._handle_moves(file_changes['moves'])
        
        # Step 3: Discover and chunk Python files
        print("🔍 Step 3: Discovering and chunking Python files...")
        chunks, files_to_process, files_skipped = self._chunk_python_files()
        print(f"✅ Created {len(chunks)} chunks from {files_to_process} files ({files_skipped} files unchanged)")
        
        if not chunks:
            print("❌ No Python files found or no chunks created")
            return {"success": False, "error": "No chunks created"}
        
        # Step 4: Generate embeddings
        print("🧠 Step 4: Generating embeddings...")
        chunks_with_embeddings = self._generate_embeddings(chunks)
        print(f"✅ Generated embeddings for {len(chunks_with_embeddings)} chunks")
        
        # Step 5: Store in Supabase
        print("💾 Step 5: Storing in Supabase...")
        storage_result = self._store_in_supabase(chunks_with_embeddings, duplicate_strategy=duplicate_strategy)
        print(f"✅ Storage result: {storage_result}")
        
        # Complete the run
        self._complete_run(storage_result)
        
        # Step 6: Ask about AI tagging
        apply_tags = self._ask_for_ai_tagging()
        
        ai_tagging_result = None
        if apply_tags:
            print("🤖 Step 6: Applying AI-driven architectural tags...")
            ai_tagging_result = self._apply_ai_tags(chunks_with_embeddings)
            print(f"✅ AI tagging complete")
        
        # Cleanup
        self._cleanup()
        
        return {
            "success": True,
            "project_id": self.project_id,
            "run_id": self.run_id,
            "total_chunks": len(chunks_with_embeddings),
            "storage_result": storage_result,
            "ai_tagging_applied": apply_tags,
            "ai_tagging_result": ai_tagging_result
        }
    
    def _copy_to_temp(self, folder_path: str) -> str:
        """Copy folder to a controlled location.
        
        This creates a copy in a predictable location while maintaining isolation.
        """
        source_path = Path(folder_path)
        
        if not source_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")
        
        # Check if we should skip copying (USE_ORIGINAL_PATH=true in .env)
        if os.getenv('USE_ORIGINAL_PATH', '').lower() == 'true':
            print(f"⚠️ WARNING: Using original path directly: {folder_path}")
            print(f"   This is less safe but avoids creating a copy.")
            return str(source_path)
            
        # Get custom processing directory from environment or use default
        processing_dir_env = os.getenv('PROCESSING_DIR')
        if processing_dir_env:
            # Use custom directory from environment variable
            processing_base = Path(processing_dir_env)
        else:
            # Default: Create directory next to the original with _processing suffix
            parent_dir = source_path.parent
            processing_base = parent_dir / f"{source_path.name}_processing"
        
        # Create processing directory if it doesn't exist
        processing_base.mkdir(exist_ok=True)
        
        # Create timestamped subfolder to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        processing_dir = processing_base / timestamp
        processing_dir.mkdir(exist_ok=True)
        
        # Path for the copied folder
        dest_path = processing_dir / source_path.name
        
        print(f"📂 Copying to: {dest_path}")
        # Copy the folder
        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        
        return str(dest_path)
    
    def _chunk_python_files(self) -> tuple[List[SimpleCodeChunk], int, int]:
        """Discover and chunk all Python files.
        
        Returns:
            Tuple of (chunks, files_processed, files_skipped)
        """
        chunks = []
        temp_path = Path(self.temp_dir)
        files_processed = 0
        files_skipped = 0
        
        # Find all Python files
        python_files = list(temp_path.rglob("*.py"))
        
        # Filter out common non-source directories
        python_files = [
            f for f in python_files 
            if not any(part in f.parts for part in ['.venv', 'venv', '__pycache__', '.git', 'build', 'dist'])
        ]
        
        print(f"Found {len(python_files)} Python files")
        
        for file_path in python_files:
            try:
                # Calculate file hash
                file_hash = self._calculate_file_hash(file_path)
                
                # Get relative path for display purposes
                try:
                    relative_path = str(file_path.relative_to(self.project_root))
                except ValueError:
                    relative_path = str(file_path.relative_to(temp_path))
                
                # Check if file has changed (now hash-based)
                if self._is_file_unchanged(relative_path, file_hash):
                    files_skipped += 1
                    continue
                
                # Check if this was a previously deleted file being restored
                was_deleted = self._check_and_restore_deleted_file(relative_path, file_hash)
                
                if not was_deleted:
                    # Process the file normally
                    file_chunks = self._process_single_file(file_path, file_hash)
                    chunks.extend(file_chunks)
                    files_processed += 1
                else:
                    # File was restored, no need to re-embed
                    files_skipped += 1
                
                # Update hash cache with current path
                self._update_hash_cache(relative_path, file_hash)
                
            except Exception as e:
                print(f"⚠️ Error processing {file_path}: {e}")
                continue
        
        # Update processed files manifest
        self._update_processed_manifest()
        
        # Save hash cache after processing all files
        self._save_hash_cache()
        
        return chunks, files_processed, files_skipped
    
    def _process_single_file(self, file_path: Path, file_hash: Optional[str] = None) -> List[SimpleCodeChunk]:
        """Process a single Python file into chunks."""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception as e:
            print(f"Cannot read {file_path}: {e}")
            return []
        
        try:
            tree = ast.parse(source_code)
            lines = source_code.split('\n')
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")
            return []
            
        # Get file name and relative path
        file_name = file_path.name
        # Calculate relative path from the project root
        try:
            relative_path = file_path.relative_to(self.project_root)
        except ValueError:
            # If file is not within project root, use the path relative to temp dir
            relative_path = file_path.relative_to(Path(self.temp_dir))
            
        # Detect architectural layer
        arch_layer = self._detect_architectural_layer(file_path)
        
        # Extract functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                chunk = self._create_function_chunk(node, file_path, lines, arch_layer, file_hash)
                if chunk:
                    chunks.append(chunk)
        
        # Extract classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                chunk = self._create_class_chunk(node, file_path, lines, arch_layer, file_hash)
                if chunk:
                    chunks.append(chunk)
        
        # Create module-level chunk for small files
        if len(source_code) < 5000:
            module_chunk = self._create_module_chunk(file_path, source_code, arch_layer, file_hash)
            if module_chunk:
                chunks.append(module_chunk)
        
        return chunks
    
    def _create_function_chunk(self, node: ast.FunctionDef, file_path: Path, 
                              lines: List[str], arch_layer: str, file_hash: Optional[str] = None) -> Optional[SimpleCodeChunk]:
        """Create a chunk for a function."""
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10
        
        # Get file name and relative path
        file_name = file_path.name
        try:
            relative_path = str(file_path.relative_to(self.project_root))
        except ValueError:
            # If file is not within project root, use path relative to temp dir
            try:
                relative_path = str(file_path.relative_to(Path(self.temp_dir)))
            except ValueError:
                # Fallback to just the filename if all else fails
                relative_path = file_name
        
        # Include some context
        context_start = max(0, start_line - 2)
        function_code = '\n'.join(lines[context_start:end_line])
        
        docstring = ast.get_docstring(node)
        
        # Create embedding text
        embedding_text = self._create_embedding_text(
            "function", node.name, function_code, docstring, file_name, relative_path, arch_layer
        )
        
        return SimpleCodeChunk(
            chunk_id=f"{relative_path}:func:{node.name}:{start_line}",
            project_name=self.project_name,
            file_name=file_name,
            relative_path=relative_path,
            chunk_type="function",
            name=node.name,
            code=function_code,
            docstring=docstring,
            architectural_layer=arch_layer,
            embedding_text=embedding_text,
            file_hash=file_hash
        )
        
    def _create_class_chunk(self, node: ast.ClassDef, file_path: Path, 
                            lines: List[str], arch_layer: str, file_hash: Optional[str] = None) -> Optional[SimpleCodeChunk]:
        """Create a chunk for a class."""
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 20
        
        # Get file name and relative path
        file_name = file_path.name
        try:
            relative_path = str(file_path.relative_to(self.project_root))
        except ValueError:
            # If file is not within project root, use path relative to temp dir
            try:
                relative_path = str(file_path.relative_to(Path(self.temp_dir)))
            except ValueError:
                # Fallback to just the filename if all else fails
                relative_path = file_name
        
        # Include some context
        context_start = max(0, start_line - 2)
        class_code = '\n'.join(lines[context_start:end_line])
        
        docstring = ast.get_docstring(node)
        
        # Create embedding text
        embedding_text = self._create_embedding_text(
            "class", node.name, class_code, docstring, file_name, relative_path, arch_layer
        )
        
        return SimpleCodeChunk(
            chunk_id=f"{relative_path}:class:{node.name}:{start_line}",
            project_name=self.project_name,
            file_name=file_name,
            relative_path=relative_path,
            chunk_type="class",
            name=node.name,
            code=class_code,
            docstring=docstring,
            architectural_layer=arch_layer,
            embedding_text=embedding_text,
            file_hash=file_hash
        )
    
    def _create_module_chunk(self, file_path: Path, source_code: str, 
                            arch_layer: str, file_hash: Optional[str] = None) -> Optional[SimpleCodeChunk]:
        """Create a chunk for a small module."""
        docstring = None
        try:
            tree = ast.parse(source_code)
            docstring = ast.get_docstring(tree)
        except:
            pass
        
        # Get file name and relative path
        file_name = file_path.name
        try:
            relative_path = str(file_path.relative_to(self.project_root))
        except ValueError:
            # If file is not within project root, use path relative to temp dir
            try:
                relative_path = str(file_path.relative_to(Path(self.temp_dir)))
            except ValueError:
                # Fallback to just the filename if all else fails
                relative_path = file_name
        
        # Create embedding text
        embedding_text = self._create_embedding_text(
            "module", file_path.stem, source_code, docstring, file_name, relative_path, arch_layer
        )
        
        return SimpleCodeChunk(
            chunk_id=f"{relative_path}:module:0",
            project_name=self.project_name,
            file_name=file_name,
            relative_path=relative_path,
            chunk_type="module",
            name=file_path.stem,
            code=source_code,
            docstring=docstring,
            architectural_layer=arch_layer,
            embedding_text=embedding_text,
            file_hash=file_hash
        )
    
    def _setup_project_and_run(self, folder_path: str, project_description: str = None, clean_import: bool = True, duplicate_strategy: str = 'skip') -> Dict[str, Any]:
        """Create or find project and start a new embedding run."""
        try:
            # First, check if project exists
            result = self.supabase_client.table("projects").select("*").eq("name", self.project_name).execute()
            
            if result.data and len(result.data) > 0:
                # Project exists
                project = result.data[0]
                self.project_id = project['id']
                print(f"📊 Found existing project: {self.project_name} (ID: {self.project_id})")
                print(f"   Total chunks in project: {project.get('total_chunks', 0)}")
            else:
                # Create new project
                new_project = {
                    'name': self.project_name,
                    'description': project_description or f"Code embeddings for {self.project_name}",
                    'root_path': str(folder_path)
                }
                result = self.supabase_client.table("projects").insert(new_project).execute()
                
                if result.data and len(result.data) > 0:
                    project = result.data[0]
                    self.project_id = project['id']
                    print(f"✅ Created new project: {self.project_name} (ID: {self.project_id})")
                else:
                    raise Exception("Failed to create project")
            
            # If clean_import is True, delete all existing chunks for this project
            if clean_import and self.project_id:
                print(f"🧹 Clean import mode: Removing all existing chunks for project {self.project_name}...")
                try:
                    # Delete all chunks for this project
                    delete_result = self.supabase_client.table("python_code_chunks").delete().eq("project_id", self.project_id).execute()
                    deleted_count = len(delete_result.data) if delete_result.data else 0
                    print(f"✅ Deleted {deleted_count} existing chunks")
                except Exception as e:
                    print(f"⚠️ Error deleting existing chunks: {e}")
                    # Continue anyway - we can still insert new chunks
            
            # Create a new embedding run
            new_run = {
                'project_id': self.project_id,
                'run_type': 'full_replace' if clean_import else 'incremental',
                'status': 'in_progress',
                'metadata': {
                    'duplicate_strategy': duplicate_strategy,
                    'source_path': str(folder_path),
                    'clean_import': clean_import
                }
            }
            result = self.supabase_client.table("embedding_runs").insert(new_run).execute()
            
            if result.data and len(result.data) > 0:
                run = result.data[0]
                self.run_id = run['id']
                print(f"🏃 Started embedding run ID: {self.run_id}")
                return {"success": True}
            else:
                raise Exception("Failed to create embedding run")
                
        except Exception as e:
            print(f"❌ Error setting up project and run: {e}")
            return {"success": False, "error": str(e)}
    
    def _complete_run(self, storage_result: Dict[str, Any]) -> None:
        """Complete the embedding run with final statistics."""
        try:
            # Update run with completion stats
            update_data = {
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'chunks_processed': storage_result.get('total_chunks', 0),
                'chunks_inserted': storage_result.get('chunks_inserted', 0),
                'chunks_updated': storage_result.get('chunks_updated', 0),
                'chunks_skipped': storage_result.get('chunks_skipped', 0)
            }
            
            self.supabase_client.table("embedding_runs").update(update_data).eq('id', self.run_id).execute()
            
            # Update project total chunks count
            total_chunks_result = self.supabase_client.table("python_code_chunks").select("id").eq("project_id", self.project_id).execute()
            total_chunks = len(total_chunks_result.data) if total_chunks_result.data else 0
            
            self.supabase_client.table("projects").update({'total_chunks': total_chunks}).eq('id', self.project_id).execute()
            
            print(f"✅ Completed run ID: {self.run_id}")
            print(f"📊 Project now has {total_chunks} total chunks")
            
        except Exception as e:
            print(f"⚠️ Error completing run: {e}")
            # Try to at least mark it as failed
            try:
                self.supabase_client.table("embedding_runs").update({
                    'status': 'failed',
                    'completed_at': datetime.now().isoformat()
                }).eq('id', self.run_id).execute()
            except:
                pass
    
    def _detect_architectural_layer(self, file_path: Path) -> str:
        """Simple architectural layer detection."""
        path_str = str(file_path).lower()
        
        if any(part in path_str for part in ['controller', 'api', 'endpoint', 'view']):
            return "presentation"
        elif any(part in path_str for part in ['service', 'business', 'logic', 'use_case']):
            return "application"
        elif any(part in path_str for part in ['repository', 'dao', 'database', 'storage', 'adapter']):
            return "infrastructure"
        elif any(part in path_str for part in ['model', 'entity', 'domain']):
            return "domain"
        elif any(part in path_str for part in ['config', 'settings']):
            return "configuration"
        elif any(part in path_str for part in ['test', 'spec']):
            return "test"
        else:
            return "unknown"
    
    def _create_embedding_text(self, chunk_type: str, name: str, code: str, docstring: Optional[str], file_name: str, relative_path: str, arch_layer: str) -> str:
        """Create rich text for embedding."""
        parts = []
        parts.append(f"# Project: {self.project_name}")
        parts.append(f"# {arch_layer} layer - {chunk_type}")
        parts.append(f"# File: {file_name}")
        parts.append(f"# Path: {relative_path}")
        parts.append(f"{chunk_type.title()}: {name}")
        
        if docstring:
            parts.append(f"Purpose: {docstring}")
        
        parts.append(f"Architectural Layer: {arch_layer}")
        
        # Add code (truncated if too long)
        parts.append("Code:")
        if len(code) > 2000:
            parts.append(code[:2000] + "... [truncated]")
        else:
            parts.append(code)
        
        return "\n\n".join(parts)
    
    def _generate_embeddings(self, chunks: List[SimpleCodeChunk]) -> List[SimpleCodeChunk]:
        """Generate embeddings for all chunks."""
        batch_size = 20
        successful_batches = 0
        failed_batches = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embedding_texts = [chunk.embedding_text for chunk in batch]
            
            try:
                embeddings = create_embeddings_batch(embedding_texts)
                
                # Check if we got real embeddings or fake ones
                if embeddings and len(embeddings) > 0 and not all(all(val == 0.0 for val in emb) for emb in embeddings):
                    for chunk, embedding in zip(batch, embeddings):
                        chunk.embedding = embedding
                    print(f"✅ Generated REAL embeddings for batch {i//batch_size + 1}")
                    successful_batches += 1
                else:
                    print(f"❌ Got fake/zero embeddings for batch {i//batch_size + 1}")
                    # Assign zero embeddings as fallback
                    for chunk in batch:
                        chunk.embedding = [0.0] * 1536
                    failed_batches += 1
                    
            except Exception as e:
                print(f"❌ Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Assign zero embeddings as fallback
                for chunk in batch:
                    chunk.embedding = [0.0] * 1536
                failed_batches += 1
        
        print(f"📊 Embedding Summary: {successful_batches} successful, {failed_batches} failed")
        if failed_batches > 0:
            print(f"⚠️ WARNING: {failed_batches} batches failed - check OpenAI API key and connectivity!")
        
        return chunks
    
    def _store_in_supabase(self, chunks: List[SimpleCodeChunk], duplicate_strategy: str = 'skip') -> Dict[str, Any]:
        """Store chunks in Supabase.
        
        Args:
            chunks: List of code chunks to store
            duplicate_strategy: How to handle duplicates - 'skip', 'update', or 'fail'
        """
        table_name = "python_code_chunks"
        
        # Prepare data for insertion
        chunk_data = []
        for chunk in chunks:
            chunk_dict = {
                'project_id': self.project_id,  # Use project_id instead of project_name
                'run_id': self.run_id,  # Add run_id
                'chunk_id': chunk.chunk_id,
                'file_name': chunk.file_name,
                'relative_path': chunk.relative_path,
                'chunk_type': chunk.chunk_type,
                'name': chunk.name,
                'code': chunk.code,
                'docstring': chunk.docstring,
                'architectural_layer': chunk.architectural_layer,
                'embedding_text': chunk.embedding_text,
                'embedding': chunk.embedding,
                'file_hash': chunk.file_hash,
                'is_current': True,  # New chunks are always current
                'created_at': datetime.now().isoformat()
            }
            chunk_data.append(chunk_dict)
        
        try:
            # Get all existing chunk IDs to avoid duplicates
            existing_chunks = {}
            if duplicate_strategy in ['skip', 'update']:
                print(f"🔍 Checking for existing chunks in project...")
                # Get all chunk_ids for this project to avoid duplicates
                try:
                    result = self.supabase_client.table(table_name).select("chunk_id").eq("project_id", self.project_id).execute()
                    if result.data:
                        existing_chunks = {item['chunk_id']: True for item in result.data}
                    print(f"✅ Found {len(existing_chunks)} existing chunks in project")
                except Exception as e:
                    print(f"⚠️ Error checking existing chunks: {e}")
                    # Continue anyway - worst case we'll get errors on insert
        
            # Insert in batches
            batch_size = 100
            total_inserted = 0
            total_updated = 0
            total_skipped = 0
            
            for i in range(0, len(chunk_data), batch_size):
                batch = chunk_data[i:i + batch_size]
                
                # Filter out existing chunks or prepare for update
                insert_batch = []
                update_batch = []
                
                for item in batch:
                    chunk_id = item['chunk_id']
                    if chunk_id in existing_chunks:
                        if duplicate_strategy == 'update':
                            update_batch.append(item)
                        else:  # skip
                            total_skipped += 1
                    else:
                        insert_batch.append(item)
                
                # Insert new chunks
                if insert_batch:
                    try:
                        result = self.supabase_client.table(table_name).insert(insert_batch).execute()
                        total_inserted += len(insert_batch)
                        print(f"✅ Inserted batch {i//batch_size + 1}: {len(insert_batch)} new chunks")
                    except Exception as e:
                        print(f"⚠️ Error inserting batch {i//batch_size + 1}: {e}")
                        # Try individual inserts
                        for item in insert_batch:
                            try:
                                self.supabase_client.table(table_name).insert([item]).execute()
                                total_inserted += 1
                            except Exception as individual_error:
                                print(f"⚠️ Failed to insert individual chunk: {individual_error}")
                
                # Update existing chunks if requested
                if update_batch and duplicate_strategy == 'update':
                    for item in update_batch:
                        try:
                            chunk_id = item['chunk_id']
                            # Update based on both project_id and chunk_id
                            self.supabase_client.table(table_name).update(item).match({
                                'project_id': self.project_id,
                                'chunk_id': chunk_id
                            }).execute()
                            total_updated += 1
                        except Exception as update_error:
                            print(f"⚠️ Failed to update chunk {item['chunk_id']}: {update_error}")
            
            return {
                "success": True,
                "total_chunks": len(chunks),
                "chunks_inserted": total_inserted,
                "chunks_updated": total_updated,
                "chunks_skipped": total_skipped,
                "table_name": table_name
            }
            
        except Exception as e:
            print(f"❌ Error storing chunks: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_chunks": len(chunks)
            }
    
    def _ask_for_ai_tagging(self) -> bool:
        """Ask user if they want to apply AI tagging."""
        try:
            while True:
                response = input("\n🤖 Do you want to apply AI-driven architectural tagging? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    return True
                elif response in ['n', 'no']:
                    return False
                else:
                    print("Please enter 'y' or 'n'")
        except EOFError:
            # Running non-interactively, skip AI tagging
            print("\n⏭️ Skipping AI tagging (running non-interactively)")
            return False
    
    def _apply_ai_tags(self, chunks: List[SimpleCodeChunk]) -> Dict[str, Any]:
        """Apply AI-driven architectural tags using Supabase context."""
        print("🔄 Analyzing chunks with AI using full project context from Supabase...")
        
        # First, get project-wide architectural patterns from Supabase
        project_patterns = self._get_project_architectural_patterns()
        
        ai_results = []
        enhanced_chunks = []
        
        # Process each chunk with full context
        for i, chunk in enumerate(chunks):
            print(f"🔍 Analyzing chunk {i+1}/{len(chunks)}: {chunk.name}")
            
            # Get similar chunks from Supabase for context
            similar_chunks = self._get_similar_chunks_from_supabase(chunk)
            
            # Perform context-aware AI analysis
            ai_analysis = self._get_context_aware_ai_analysis(chunk, similar_chunks, project_patterns)
            
            enhanced_chunk_data = {
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.relative_path,
                "name": chunk.name,
                "original_layer": chunk.architectural_layer,
                "ai_analysis": ai_analysis,
                "similar_chunks_found": len(similar_chunks)
            }
            
            enhanced_chunks.append(enhanced_chunk_data)
            
            # Update the chunk in Supabase with enhanced tags if analysis succeeded
            if ai_analysis and ai_analysis.get("success"):
                self._update_chunk_with_ai_tags(chunk, ai_analysis)
        
        # Store AI analysis results
        analysis_file = f"ai_architectural_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump({
                "project_patterns": project_patterns,
                "enhanced_chunks": enhanced_chunks,
                "analysis_timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"✅ Context-aware AI analysis saved to: {analysis_file}")
        
        return {
            "analysis_file": analysis_file,
            "total_chunks_analyzed": len(chunks),
            "chunks_enhanced": len([c for c in enhanced_chunks if c["ai_analysis"].get("success")]),
            "project_patterns_found": len(project_patterns)
        }
    
    def _get_project_architectural_patterns(self) -> Dict[str, Any]:
        """Get architectural patterns from existing Supabase data."""
        try:
            # Query architectural layer distribution
            layer_result = self.supabase_client.table("python_code_chunks").select(
                "architectural_layer"
            ).eq("project_id", self.project_id).eq("is_current", True).eq("is_deleted", False).execute()
            
            layer_counts = {}
            for row in layer_result.data:
                layer = row.get("architectural_layer", "unknown")
                layer_counts[layer] = layer_counts.get(layer, 0) + 1
            
            # Get sample components from each layer
            layer_samples = {}
            for layer in layer_counts.keys():
                if layer != "unknown":
                    sample_result = self.supabase_client.table("python_code_chunks").select(
                        "name, chunk_type, embedding_text"
                    ).eq("project_id", self.project_id).eq("architectural_layer", layer).eq(
                        "is_current", True
                    ).eq("is_deleted", False).limit(3).execute()
                    
                    layer_samples[layer] = [
                        f"{row['chunk_type']}: {row['name']}" 
                        for row in sample_result.data
                    ]
            
            return {
                "layer_distribution": layer_counts,
                "layer_samples": layer_samples,
                "total_components": sum(layer_counts.values())
            }
        except Exception as e:
            print(f"⚠️ Error getting project patterns: {e}")
            return {"layer_distribution": {}, "layer_samples": {}, "total_components": 0}
    
    def _get_similar_chunks_from_supabase(self, chunk: 'SimpleCodeChunk') -> List[Dict[str, Any]]:
        """Get similar chunks from Supabase using vector similarity."""
        try:
            if not chunk.embedding:
                return []
            
            # Use Supabase vector similarity search
            result = self.supabase_client.rpc('match_documents', {
                'query_embedding': chunk.embedding,
                'match_threshold': 0.7,
                'match_count': 5,
                'filter': {
                    'project_id': self.project_id,
                    'is_current': True,
                    'is_deleted': False
                }
            }).execute()
            
            similar_chunks = []
            for row in result.data:
                similar_chunks.append({
                    "name": row.get("name"),
                    "chunk_type": row.get("chunk_type"),
                    "architectural_layer": row.get("architectural_layer"),
                    "similarity": row.get("similarity", 0.0),
                    "embedding_text": row.get("embedding_text", "")[:200]  # Truncate for context
                })
            
            return similar_chunks
        except Exception as e:
            print(f"⚠️ Error finding similar chunks: {e}")
            return []
    
    def _get_context_aware_ai_analysis(self, chunk: 'SimpleCodeChunk', similar_chunks: List[Dict], project_patterns: Dict) -> Dict[str, Any]:
        """Perform AI analysis with full project context."""
        try:
            # Build context-rich prompt
            similar_context = ""
            if similar_chunks:
                similar_context = "\n".join([
                    f"- {sc['chunk_type']}: {sc['name']} (Layer: {sc['architectural_layer']}, Similarity: {sc['similarity']:.2f})"
                    for sc in similar_chunks[:3]
                ])
            
            pattern_context = ""
            if project_patterns.get("layer_distribution"):
                pattern_context = f"Project has {project_patterns['total_components']} components across layers: " + \
                               ", ".join([f"{layer}({count})" for layer, count in project_patterns['layer_distribution'].items()])
            
            analysis_prompt = f"""
You are analyzing a code component in a project with established architectural patterns.

COMPONENT TO ANALYZE:
- File: {chunk.relative_path}
- Name: {chunk.name}
- Type: {chunk.chunk_type}
- Current Classification: {chunk.architectural_layer}
- Code: {chunk.code[:1500]}
- Docstring: {chunk.docstring or 'None'}

PROJECT CONTEXT:
{pattern_context}

SIMILAR COMPONENTS IN PROJECT:
{similar_context or 'No similar components found'}

Please analyze this component and provide consistent classification that aligns with the project's existing patterns.

Respond in JSON format:
{{
    "layer": "presentation|application|infrastructure|domain|configuration|test|unknown",
    "layer_confidence": 0.0-1.0,
    "layer_reasoning": "explanation considering project patterns",
    "responsibility": "data_access|business_logic|external_integration|user_interface|configuration|validation|transformation|coordination",
    "responsibility_confidence": 0.0-1.0, 
    "responsibility_reasoning": "explanation",
    "patterns": ["pattern1", "pattern2"],
    "quality_attributes": ["attribute1", "attribute2"],
    "consistency_notes": "how this aligns with project patterns",
    "evidence": ["evidence1", "evidence2"]
}}
"""
            
            response = openai_client.chat.completions.create(
                model=os.getenv("CHAT_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "You are an expert software architect analyzing code for architectural patterns. Focus on consistency with existing project patterns."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            ai_analysis = json.loads(response.choices[0].message.content)
            ai_analysis["success"] = True
            return ai_analysis
            
        except Exception as e:
            print(f"⚠️ Error in context-aware AI analysis for {chunk.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "layer": chunk.architectural_layer,
                "layer_confidence": 0.3,
                "fallback": True
            }
    
    def _update_chunk_with_ai_tags(self, chunk: 'SimpleCodeChunk', ai_analysis: Dict[str, Any]) -> None:
        """Update chunk in Supabase with enhanced AI tags."""
        try:
            # Create enhanced metadata
            enhanced_metadata = {
                "ai_enhanced": True,
                "ai_layer": ai_analysis.get("layer"),
                "ai_confidence": ai_analysis.get("layer_confidence", 0.0),
                "ai_responsibility": ai_analysis.get("responsibility"),
                "ai_patterns": ai_analysis.get("patterns", []),
                "ai_quality_attributes": ai_analysis.get("quality_attributes", []),
                "ai_reasoning": ai_analysis.get("layer_reasoning", ""),
                "enhancement_timestamp": datetime.now().isoformat()
            }
            
            # Update the chunk in Supabase
            chunk_id = chunk.chunk_id if hasattr(chunk, 'chunk_id') else f"{chunk.file_path}:{chunk.name}"
            
            self.supabase_client.table("python_code_chunks").update({
                "metadata": enhanced_metadata
            }).eq("project_id", self.project_id).eq("chunk_id", chunk_id).execute()
            
        except Exception as e:
            print(f"⚠️ Error updating chunk with AI tags: {e}")
    
    def run_ai_tagging_only(self, project_path: str) -> Dict[str, Any]:
        """Run AI tagging on existing embeddings without reprocessing files."""
        print(f"🔍 Looking for existing project in Supabase for path: {project_path}")
        
        # Initialize project setup
        self.project_name = Path(project_path).name
        self.project_root = Path(project_path)
        
        # Find existing project in Supabase
        project_result = self.supabase_client.table("projects").select("*").eq("name", self.project_name).execute()
        
        if not project_result.data:
            print(f"❌ No existing project found with name: {self.project_name}")
            print("💡 Run normal processing first to create embeddings")
            return {"success": False, "error": "No existing project found"}
        
        self.project_id = project_result.data[0]['id']
        print(f"✅ Found existing project: {self.project_name} (ID: {self.project_id})")
        
        # Get existing chunks from Supabase
        chunks_result = self.supabase_client.table("python_code_chunks").select(
            "chunk_id, file_name, relative_path, chunk_type, name, code, docstring, architectural_layer, embedding_text, embedding"
        ).eq("project_id", self.project_id).eq("is_current", True).eq("is_deleted", False).execute()
        
        if not chunks_result.data:
            print(f"❌ No existing chunks found for project: {self.project_name}")
            return {"success": False, "error": "No existing chunks found"}
        
        print(f"📊 Found {len(chunks_result.data)} existing chunks in Supabase")
        
        # Convert Supabase data to SimpleCodeChunk objects
        existing_chunks = []
        for chunk_data in chunks_result.data:
            chunk = SimpleCodeChunk(
                chunk_id=chunk_data.get('chunk_id', ''),
                project_name=self.project_name,
                file_name=chunk_data.get('file_name', ''),
                relative_path=chunk_data.get('relative_path', ''),
                chunk_type=chunk_data.get('chunk_type', 'unknown'),
                name=chunk_data.get('name', ''),
                code=chunk_data.get('code', ''),
                docstring=chunk_data.get('docstring'),
                architectural_layer=chunk_data.get('architectural_layer', 'unknown'),
                embedding_text=chunk_data.get('embedding_text', ''),
                file_hash=chunk_data.get('file_hash'),
                embedding=chunk_data.get('embedding')
            )
            existing_chunks.append(chunk)
        
        print(f"🔄 Converting {len(existing_chunks)} chunks for AI analysis...")
        
        # Run AI tagging on existing chunks
        ai_tagging_result = self._apply_ai_tags(existing_chunks)
        
        return {
            "success": True,
            "mode": "ai_tagging_only",
            "project_id": self.project_id,
            "project_name": self.project_name,
            "total_chunks": len(existing_chunks),
            "ai_tagging_result": ai_tagging_result
        }
    
    def _create_layer_summary(self, layer: str, chunks: List[SimpleCodeChunk]) -> str:
        """Create a summary of a layer for AI analysis."""
        summary_parts = [f"Architectural Layer: {layer}"]
        summary_parts.append(f"Number of components: {len(chunks)}")
        
        # Group by type
        type_counts = {}
        for chunk in chunks:
            type_counts[chunk.chunk_type] = type_counts.get(chunk.chunk_type, 0) + 1
        
        summary_parts.append(f"Component types: {type_counts}")
        
        # Add sample components
        summary_parts.append("Sample components:")
        for chunk in chunks[:5]:  # First 5 as examples
            summary_parts.append(f"- {chunk.chunk_type}: {chunk.name}")
            if chunk.docstring:
                summary_parts.append(f"  Purpose: {chunk.docstring[:100]}...")
        
        return "\n".join(summary_parts)
    
    def _get_ai_layer_analysis(self, layer: str, layer_summary: str) -> str:
        """Get AI analysis of an architectural layer."""
        prompt = f"""
Analyze this architectural layer for consistency and patterns:

{layer_summary}

Please provide:
1. Assessment of architectural consistency
2. Identification of any patterns or anti-patterns
3. Suggestions for improvement
4. Confidence in the layer classification

Keep the response concise and actionable.
"""
        
        try:
            response = openai_client.chat.completions.create(
                model=os.getenv("MODEL_CHOICE", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are an expert software architect analyzing code architecture."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"AI analysis failed: {str(e)}"
    
    def _cleanup(self):
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temp directory")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file's contents."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _load_hash_cache(self) -> Dict[str, Any]:
        """Load hash cache from JSON file."""
        if self.hash_cache_path.exists():
            try:
                with open(self.hash_cache_path, 'r') as f:
                    cache = json.load(f)
                    # Handle old format (just files dict) vs new format
                    if 'project_metadata' not in cache:
                        # Convert old format to new format
                        return {
                            'project_metadata': {
                                'project_name': self.project_name or 'unknown',
                                'last_scan': datetime.now().isoformat()
                            },
                            'files': cache,
                            'hash_to_paths': {},
                            'processed_files_manifest': []
                        }
                    return cache
            except Exception as e:
                print(f"⚠️ Error loading hash cache: {e}")
                return self._create_empty_cache()
        return self._create_empty_cache()
    
    def _create_empty_cache(self) -> Dict[str, Any]:
        """Create an empty cache structure."""
        return {
            'project_metadata': {
                'project_name': self.project_name or 'unknown',
                'last_scan': datetime.now().isoformat()
            },
            'files': {},
            'hash_to_paths': {},
            'processed_files_manifest': []
        }
    
    def _save_hash_cache(self) -> None:
        """Save hash cache to JSON file."""
        try:
            # Update metadata
            self.hash_cache['project_metadata']['last_scan'] = datetime.now().isoformat()
            if self.project_name:
                self.hash_cache['project_metadata']['project_name'] = self.project_name
            
            # Ensure parent directory exists
            self.hash_cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.hash_cache_path, 'w') as f:
                json.dump(self.hash_cache, f, indent=2)
            print(f"💾 Saved hash cache to: {self.hash_cache_path}")
        except Exception as e:
            print(f"⚠️ Error saving hash cache: {e}")
    
    def _is_file_unchanged(self, file_path: str, current_hash: str) -> bool:
        """Check if a file's hash matches the cached hash."""
        files_by_hash = self.hash_cache.get('files_by_hash', {})
        if current_hash in files_by_hash:
            cached_info = files_by_hash[current_hash]
            # Check if file was previously deleted but now exists with same hash
            if cached_info.get('status') == 'deleted':
                return False  # Force reprocessing to undelete
            return cached_info.get('status') == 'active'
        return False
    
    def _update_hash_cache(self, file_path: str, file_hash: str) -> None:
        """Update the hash cache for a file using hash as primary key."""
        files_by_hash = self.hash_cache.setdefault('files_by_hash', {})
        
        # Use hash as primary key, store path as metadata
        files_by_hash[file_hash] = {
            'current_path': file_path,
            'status': 'active',
            'last_seen': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
    
    def _update_processed_manifest(self) -> None:
        """Update the manifest of processed files in the current run."""
        manifest = self.hash_cache.setdefault('processed_files_manifest', [])
        files_by_hash = self.hash_cache.get('files_by_hash', {})
        
        # Get all active files processed in this run
        current_run_files = []
        for file_hash, file_info in files_by_hash.items():
            if file_info.get('status') == 'active':
                current_run_files.append({
                    'file_path': file_info.get('current_path'),
                    'hash': file_hash,
                    'last_processed': file_info.get('last_seen'),
                    'file_size_bytes': self._get_file_size(file_info.get('current_path')) if self.temp_dir else None
                })
        
        # Update manifest with timestamp
        manifest_entry = {
            'run_timestamp': datetime.now().isoformat(),
            'project_name': self.project_name,
            'total_files_processed': len(current_run_files),
            'files': current_run_files
        }
        
        # Keep only last 10 runs in manifest to avoid bloat
        manifest.append(manifest_entry)
        if len(manifest) > 10:
            manifest.pop(0)
    
    def _get_file_size(self, relative_path: str) -> Optional[int]:
        """Get file size in bytes."""
        try:
            if self.temp_dir:
                full_path = Path(self.temp_dir) / relative_path
                if full_path.exists():
                    return full_path.stat().st_size
        except Exception:
            pass
        return None
    
    def _handle_deletions(self, deletions: List[Dict[str, str]]) -> None:
        """Mark deleted files in Supabase and update cache."""
        if not deletions:
            return
        
        try:
            # Update cache
            files_by_hash = self.hash_cache.get('files_by_hash', {})
            for deletion in deletions:
                file_hash = deletion['hash']
                if file_hash in files_by_hash:
                    files_by_hash[file_hash]['status'] = 'deleted'
                    files_by_hash[file_hash]['deleted_at'] = datetime.now().isoformat()
            
            # Update Supabase - mark chunks as deleted using file_hash
            for deletion in deletions:
                file_hash = deletion['hash']
                self.supabase_client.table("python_code_chunks").update({
                    'is_deleted': True,
                    'is_current': False
                }).eq('project_id', self.project_id).eq('file_hash', file_hash).execute()
            
            print(f"✅ Marked {len(deletions)} files as deleted")
        except Exception as e:
            print(f"⚠️ Error handling deletions: {e}")
    
    def _handle_moves(self, moves: List[Dict[str, str]]) -> None:
        """Handle moved/renamed files - now automatic with hash-based system."""
        # Moves are now handled automatically since we use hash as primary key
        # The _update_hash_cache method updates the current_path automatically
        if moves:
            print(f"ℹ️ Note: File moves are now handled automatically via hash-based tracking")
    
    def _check_and_restore_deleted_file(self, file_path: str, file_hash: str) -> bool:
        """Check if file was previously deleted and restore it if hash matches."""
        files_by_hash = self.hash_cache.get('files_by_hash', {})
        
        if file_hash in files_by_hash:
            cached_info = files_by_hash[file_hash]
            if cached_info.get('status') == 'deleted':
                # File was deleted but now exists with same content
                try:
                    # Restore in Supabase using file_hash
                    self.supabase_client.table("python_code_chunks").update({
                        'is_deleted': False,
                        'is_current': True
                    }).eq('project_id', self.project_id).eq('file_hash', file_hash).execute()
                    
                    print(f"♻️ Restored previously deleted file: {file_path}")
                    return True
                except Exception as e:
                    print(f"⚠️ Error restoring file {file_path}: {e}")
        
        return False
    
    def _complete_run(self, storage_result: Dict[str, Any]) -> None:
        """Complete the embedding run with final statistics."""
        try:
            # Update run with completion stats
            update_data = {
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'chunks_processed': storage_result.get('total_chunks', 0),
                'chunks_inserted': storage_result.get('chunks_inserted', 0),
                'chunks_updated': storage_result.get('chunks_updated', 0),
                'chunks_skipped': storage_result.get('chunks_skipped', 0)
            }
            
            self.supabase_client.table("embedding_runs").update(update_data).eq('id', self.run_id).execute()
            
            # Use COUNT query instead of selecting all rows to avoid 1000 row limit
            count_result = self.supabase_client.table("python_code_chunks").select("id", count="exact").eq("project_id", self.project_id).execute()
            total_chunks = count_result.count if hasattr(count_result, 'count') else 0
            
            # If count is still 0, fall back to length of data (with potential 1000 limit)
            if total_chunks == 0:
                fallback_result = self.supabase_client.table("python_code_chunks").select("id").eq("project_id", self.project_id).limit(10000).execute()
                total_chunks = len(fallback_result.data) if fallback_result.data else 0
            
            self.supabase_client.table("projects").update({'total_chunks': total_chunks}).eq('id', self.project_id).execute()
            
            print(f"✅ Completed run ID: {self.run_id}")
            print(f"📊 Project now has {total_chunks} total chunks")
            
        except Exception as e:
            print(f"⚠️ Error completing run: {e}")
            # Try to at least mark it as failed
            try:
                self.supabase_client.table("embedding_runs").update({
                    'status': 'failed',
                    'completed_at': datetime.now().isoformat()
                }).eq('id', self.run_id).execute()
            except:
                pass
    
    def _detect_deletions_and_moves(self) -> Dict[str, Any]:
        """Detect deleted files using hash-based comparison."""
        files_by_hash = self.hash_cache.get('files_by_hash', {})
        
        # Get all current Python files and their hashes
        temp_path = Path(self.temp_dir)
        python_files = list(temp_path.rglob("*.py"))
        python_files = [
            f for f in python_files 
            if not any(part in f.parts for part in ['.venv', 'venv', '__pycache__', '.git', 'build', 'dist'])
        ]
        
        # Build set of current file hashes
        current_hashes = set()
        for file_path in python_files:
            file_hash = self._calculate_file_hash(file_path)
            current_hashes.add(file_hash)
        
        # Detect deletions: hashes that exist in cache but not in current scan
        deletions = []
        for file_hash, cached_info in files_by_hash.items():
            if cached_info.get('status') == 'active' and file_hash not in current_hashes:
                # File with this content no longer exists
                deletions.append({
                    'hash': file_hash,
                    'last_path': cached_info.get('current_path', 'unknown')
                })
        
        return {
            'deletions': deletions,
            'moves': [],  # Moves are now handled automatically by hash-based lookup
            'current_file_count': len(python_files)
        }

def find_git_repositories(search_path: Path) -> List[Path]:
    """Find all git repositories within the given path."""
    git_repos = []
    
    # Check if the current path is a git repo
    if (search_path / '.git').exists():
        git_repos.append(search_path)
    
    # Search for git repos in subdirectories (max depth 3 to avoid deep scans)
    for depth in range(1, 4):
        pattern = '/'.join(['*'] * depth) + '/.git'
        for git_dir in search_path.glob(pattern):
            repo_path = git_dir.parent
            if repo_path not in git_repos:
                git_repos.append(repo_path)
    
    return sorted(git_repos)

def select_target_directory(provided_path: str, no_git_detection: bool = False) -> str:
    """
    Intelligently select the target directory for processing.
    
    Args:
        provided_path: The path provided by the user
        no_git_detection: If True, skip git detection and use exact path
    
    Returns:
        The final path to process
    """
    provided_path_obj = Path(provided_path)
    
    if not provided_path_obj.exists():
        print(f"❌ Path does not exist: {provided_path}")
        sys.exit(1)
    
    if not provided_path_obj.is_dir():
        print(f"❌ Path is not a directory: {provided_path}")
        sys.exit(1)
    
    # If git detection is disabled, use the exact path
    if no_git_detection:
        return str(provided_path_obj)
    
    # Find git repositories
    print(f"🔍 Searching for git repositories in: {provided_path}")
    git_repos = find_git_repositories(provided_path_obj)
    
    if not git_repos:
        # No git repos found - count files and ask for confirmation
        python_files = list(provided_path_obj.rglob("*.py"))
        python_files = [
            f for f in python_files 
            if not any(part in f.parts for part in ['.venv', 'venv', '__pycache__', '.git', 'build', 'dist', 'node_modules'])
        ]
        
        print(f"⚠️  No git repositories found in {provided_path}")
        print(f"📊 Found {len(python_files)} Python files in the directory")
        
        try:
            response = input(f"\n❓ Do you want to process all {len(python_files)} Python files? (y/n): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ Processing cancelled")
                sys.exit(1)
        except EOFError:
            print("❌ Cannot confirm processing in non-interactive mode")
            sys.exit(1)
        
        return str(provided_path_obj)
    
    elif len(git_repos) == 1:
        # Single git repo found
        repo_path = git_repos[0]
        if repo_path == provided_path_obj:
            print(f"✅ Processing git repository: {repo_path}")
        else:
            print(f"🎯 Found git repository: {repo_path}")
            print(f"📂 Using git repo instead of: {provided_path}")
        return str(repo_path)
    
    else:
        # Multiple git repos found - let user choose
        print(f"📁 Found {len(git_repos)} git repositories:")
        for i, repo in enumerate(git_repos, 1):
            # Count Python files in each repo
            python_files = list(repo.rglob("*.py"))
            python_files = [
                f for f in python_files 
                if not any(part in f.parts for part in ['.venv', 'venv', '__pycache__', '.git', 'build', 'dist'])
            ]
            rel_path = repo.relative_to(provided_path_obj) if repo != provided_path_obj else "."
            print(f"  {i}. {rel_path} ({len(python_files)} Python files)")
        
        print(f"  {len(git_repos) + 1}. Process entire directory ({provided_path})")
        
        try:
            while True:
                choice = input(f"\n❓ Select repository to process (1-{len(git_repos) + 1}): ").strip()
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(git_repos):
                        selected_repo = git_repos[choice_num - 1]
                        print(f"✅ Selected: {selected_repo}")
                        return str(selected_repo)
                    elif choice_num == len(git_repos) + 1:
                        print(f"✅ Processing entire directory: {provided_path}")
                        return str(provided_path_obj)
                    else:
                        print(f"❌ Please enter a number between 1 and {len(git_repos) + 1}")
                except ValueError:
                    print("❌ Please enter a valid number")
        except EOFError:
            # Non-interactive mode - default to first repo
            selected_repo = git_repos[0]
            print(f"🤖 Non-interactive mode: selecting first repository: {selected_repo}")
            return str(selected_repo)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process a folder for embeddings and AI tagging.")
    parser.add_argument("folder_path", help="Path to the folder to process")
    parser.add_argument(
        "--duplicate-strategy", 
        choices=["skip", "update", "fail"],
        default="skip",
        help="How to handle duplicate chunks: skip (default), update existing, or fail with error"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Force full replacement of all chunks (default is incremental update based on file changes)"
    )
    parser.add_argument(
        "--hash-cache",
        type=str,
        help="Path to the hash cache JSON file (defaults to CODE_HASH_CACHE_PATH env var or .code_hashes.json)"
    )
    parser.add_argument(
        "--no-git-detection",
        action="store_true",
        help="Disable automatic git repository detection and process the exact path provided"
    )
    parser.add_argument(
        "--ai-tagging-only",
        action="store_true",
        help="Skip file processing and only run AI tagging on existing embeddings in Supabase"
    )
    
    args = parser.parse_args()
    
    # Process the folder
    processor = SimpleFolderProcessor(hash_cache_path=args.hash_cache)
    
    try:
        # Handle AI tagging only mode
        if args.ai_tagging_only:
            print("🤖 AI TAGGING ONLY MODE")
            print("📋 Running AI tagging on existing embeddings in Supabase...")
            result = processor.run_ai_tagging_only(args.folder_path)
        else:
            # Normal processing mode
            # Intelligently select the target directory
            folder_path = select_target_directory(args.folder_path, args.no_git_detection)
            
            # Check for Python files in the selected directory
            python_files = list(Path(folder_path).rglob("*.py"))
            # Filter out common non-source directories
            python_files = [
                f for f in python_files 
                if not any(part in f.parts for part in ['.venv', 'venv', '__pycache__', '.git', 'build', 'dist', 'node_modules'])
            ]
            
            if not python_files:
                print(f"❌ No Python files found in: {folder_path}")
                sys.exit(1)
            
            print(f"✅ Found {len(python_files)} Python files")
            
            # Incremental by default, clean import only if --replace is specified
            clean_import = args.replace
            
            if clean_import:
                print(f"🧹 Running in REPLACE mode - all existing chunks will be replaced")
                print(f"⚠️  Hash cache will be ignored for this run")
            else:
                print(f"📝 Running in INCREMENTAL mode - only changed files will be processed")
                
            result = processor.process_folder(
                folder_path, 
                duplicate_strategy=args.duplicate_strategy,
                clean_import=clean_import
            )
        
        if result["success"]:
            print("\n" + "="*50)
            print("🎉 PROCESSING COMPLETE!")
            print("="*50)
            print(f"📊 Total chunks processed: {result['total_chunks']}")
            print(f"💾 Storage successful: {result['storage_result']['success']}")
            
            # Print additional details about chunk processing
            if 'chunks_inserted' in result['storage_result']:
                print(f"📥 New chunks inserted: {result['storage_result']['chunks_inserted']}")
            if 'chunks_updated' in result['storage_result']:
                print(f"🔄 Existing chunks updated: {result['storage_result']['chunks_updated']}")
            if 'chunks_skipped' in result['storage_result']:
                print(f"⏭️ Duplicate chunks skipped: {result['storage_result']['chunks_skipped']}")
                
            if result['ai_tagging_applied']:
                print(f"🤖 AI tagging applied: {result['ai_tagging_result']['analysis_file']}")
            print("\n✅ Your code is now embedded and searchable in Supabase!")
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
