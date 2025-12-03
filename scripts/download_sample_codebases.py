"""Script to download sample codebases for testing."""

import os
import subprocess
import sys
from pathlib import Path


def download_repo(url: str, target_dir: str, branch: str = "main") -> bool:
    """Download a git repository."""
    try:
        if os.path.exists(target_dir):
            print(f"Directory {target_dir} already exists. Skipping...")
            return True
        
        print(f"Cloning {url} to {target_dir}...")
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, url, target_dir],
            check=True,
            capture_output=True
        )
        print(f"Successfully cloned {url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error cloning {url}: {e}")
        return False
    except FileNotFoundError:
        print("Git not found. Please install git to download repositories.")
        return False


def main():
    """Download sample codebases."""
    base_dir = Path(__file__).parent.parent / "data" / "sample_codebases"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample codebases to download
    codebases = [
        {
            "name": "django",
            "url": "https://github.com/django/django.git",
            "branch": "main",
            "description": "Django framework (Python)"
        },
        {
            "name": "typescript",
            "url": "https://github.com/microsoft/TypeScript.git",
            "branch": "main",
            "description": "TypeScript compiler (TypeScript/JavaScript)"
        }
    ]
    
    print("Downloading sample codebases for autocomplete testing...")
    print("=" * 60)
    
    for codebase in codebases:
        target_dir = base_dir / codebase["name"]
        print(f"\n{codebase['description']}")
        print(f"URL: {codebase['url']}")
        success = download_repo(codebase["url"], str(target_dir), codebase["branch"])
        if success:
            print(f"✓ Downloaded to {target_dir}")
        else:
            print(f"✗ Failed to download {codebase['name']}")
    
    print("\n" + "=" * 60)
    print("Download complete!")
    print(f"\nCodebases are available at: {base_dir}")
    print("\nTo index a codebase, use:")
    print("  python -c \"from src.indexer.codebase_indexer import CodebaseIndexer; idx = CodebaseIndexer(); idx.index_directory('data/sample_codebases/django')\"")


if __name__ == "__main__":
    main()

