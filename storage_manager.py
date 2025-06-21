"""
Storage Manager
===============

Handles automatic creation and management of the storage directory structure.
Ensures all required directories exist with proper permissions before services start.
"""

import os
from pathlib import Path
from typing import Dict

from human_logging import log_service_status


class StorageManager:
    """Manages storage directory structure and initialization."""

    STORAGE_ROOT = "./storage"

    # Define the complete storage structure
    STORAGE_STRUCTURE = {
        "redis": {
            "path": "redis",
            "description": "Redis persistence data (RDB snapshots, AOF logs)",
            "permissions": 0o777,  # Redis container needs full access
            "files": ["dump.rdb"],  # Files that might be created
        },
        "chroma": {
            "path": "chroma",
            "description": "ChromaDB vector database storage",
            "permissions": 0o777,  # ChromaDB container needs full access
            "subdirs": ["onnx_cache"],
            "files": [],
        },
        "chroma_onnx": {
            "path": "chroma/onnx_cache",
            "description": "ChromaDB ONNX model optimization cache",
            "permissions": 0o777,
            "files": [],
        },
        "ollama": {
            "path": "ollama",
            "description": "Ollama LLM model storage (can be several GB)",
            "permissions": 0o777,  # Ollama container needs full access
            "files": [],
        },
        "backend": {
            "path": "backend",
            "description": "Application data, logs, temporary files",
            "permissions": 0o755,
            "files": [],
        },
        "models": {
            "path": "models",
            "description": "Sentence transformer and embedding model cache",
            "permissions": 0o755,
            "files": [],
        },
        "openwebui": {
            "path": "openwebui",
            "description": "OpenWebUI user data, chat history, settings",
            "permissions": 0o755,
            "files": [],
        },
    }

    @classmethod
    def ensure_storage_structure(cls) -> Dict[str, bool]:
        """
        Ensure complete storage directory structure exists.

        Returns:
            Dict mapping directory names to creation success status
        """
        results = {}
        base_path = Path(cls.STORAGE_ROOT)        # Create base storage directory
        if not base_path.exists():
            log_service_status(
                "STORAGE", "starting", f"Creating base storage directory: {base_path.absolute()}"
            )
            base_path.mkdir(parents=True, exist_ok=True)
            os.chmod(base_path, 0o755)        # Create each storage component
        for name, config in cls.STORAGE_STRUCTURE.items():
            dir_path = base_path / config["path"]

            try:
                # Create directory if it doesn't exist
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    log_service_status(
                        "STORAGE", "ready", f"Created {name}: {config['description']}"
                    )

                # Set permissions
                if os.name != "nt":  # Skip permission setting on Windows
                    os.chmod(dir_path, config["permissions"])

                # Create any required subdirectories
                if "subdirs" in config:
                    for subdir in config["subdirs"]:
                        subdir_path = dir_path / subdir
                        if not subdir_path.exists():
                            subdir_path.mkdir(parents=True, exist_ok=True)
                            if os.name != "nt":
                                os.chmod(subdir_path, config["permissions"])

                results[name] = True

            except Exception as e:
                log_service_status("STORAGE", "error", f"Failed to create {name}: {str(e)}")
                results[name] = False

        return results

    @classmethod
    def get_storage_info(cls) -> Dict[str, Dict]:
        """
        Get information about the current storage structure.

        Returns:
            Dict with storage directory information
        """
        base_path = Path(cls.STORAGE_ROOT)
        info = {
            "base_path": str(base_path.absolute()),
            "exists": base_path.exists(),
            "directories": {},
        }

        for name, config in cls.STORAGE_STRUCTURE.items():
            dir_path = base_path / config["path"]

            dir_info = {
                "path": str(dir_path),
                "exists": dir_path.exists(),
                "description": config["description"],
                "size_mb": 0,
                "file_count": 0,
            }

            if dir_path.exists():
                try:
                    # Calculate directory size and file count
                    total_size = 0
                    file_count = 0
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.exists(file_path):
                                total_size += os.path.getsize(file_path)
                                file_count += 1

                    dir_info["size_mb"] = round(total_size / (1024 * 1024), 2)
                    dir_info["file_count"] = file_count

                except Exception as e:
                    dir_info["error"] = str(e)

            info["directories"][name] = dir_info

        return info

    @classmethod
    def validate_permissions(cls) -> Dict[str, bool]:
        """
        Validate that all storage directories have correct permissions.

        Returns:
            Dict mapping directory names to permission validation status
        """
        results = {}
        base_path = Path(cls.STORAGE_ROOT)

        if not base_path.exists():
            log_service_status("STORAGE", "error", "Base storage directory does not exist")
            return {"base": False}

        for name, config in cls.STORAGE_STRUCTURE.items():
            dir_path = base_path / config["path"]

            if not dir_path.exists():
                results[name] = False
                continue

            try:                # Test write access
                test_file = dir_path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                results[name] = True

            except Exception as e:
                log_service_status(
                    "STORAGE", "degraded", f"Write permission issue in {name}: {str(e)}"
                )
                results[name] = False

        return results


def initialize_storage() -> bool:
    """
    Initialize storage structure at application startup.

    Returns:
        True if storage initialization was successful
    """
    try:
        log_service_status("STORAGE", "starting", "Initializing storage structure...")

        # Ensure storage structure exists
        results = StorageManager.ensure_storage_structure()        # Check results
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        if success_count == total_count:
            log_service_status(
                "STORAGE", "ready", f"All {total_count} storage directories initialized successfully"            )
            return True
        else:
            log_service_status(
                "STORAGE",
                "degraded",
                f"Storage partially initialized: {success_count}/{total_count} directories created",
            )
            return False

    except Exception as e:
        log_service_status("STORAGE", "error", f"Storage initialization failed: {str(e)}")
        return False


if __name__ == "__main__":
    # CLI mode for testing storage setup
    print("=== Storage Manager Test ===")

    # Initialize storage
    success = initialize_storage()
    print(f"Storage initialization: {'SUCCESS' if success else 'FAILED'}")

    # Show storage info
    info = StorageManager.get_storage_info()
    print(f"\nBase storage path: {info['base_path']}")
    print(f"Base directory exists: {info['exists']}")

    print("\nStorage directories:")
    for name, dir_info in info["directories"].items():
        status = "✅" if dir_info["exists"] else "❌"
        size_info = (
            f" ({dir_info['size_mb']} MB, {dir_info['file_count']} files)"
            if dir_info["exists"]
            else ""
        )
        print(f"{status} {name}: {dir_info['description']}{size_info}")

    # Validate permissions
    permissions = StorageManager.validate_permissions()
    print("\nPermission validation:")
    for name, valid in permissions.items():
        status = "✅" if valid else "❌"
        print(f"{status} {name}: {'Write access OK' if valid else 'Write access FAILED'}")
