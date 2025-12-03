"""Script to index a codebase for autocomplete."""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.indexer.codebase_indexer import CodebaseIndexer


def main():
    parser = argparse.ArgumentParser(description="Index a codebase for autocomplete")
    parser.add_argument("directory", help="Directory to index")
    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help="Languages to index (default: all supported)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory {args.directory} does not exist")
        sys.exit(1)
    
    print(f"Indexing codebase at: {args.directory}")
    print(f"Languages: {args.languages or 'all supported'}")
    print(f"Workers: {args.workers}")
    print("=" * 60)
    
    indexer = CodebaseIndexer(max_workers=args.workers)
    stats = indexer.index_directory(args.directory, languages=args.languages)
    
    print("\n" + "=" * 60)
    print("Indexing complete!")
    print(f"Files indexed: {stats['files_indexed']}/{stats['total_files']}")
    print(f"Symbols indexed: {stats['symbols_indexed']}")
    print(f"Unique symbols: {stats['unique_symbols']}")
    
    # Save indexer state (in a real implementation, you'd serialize this)
    print("\nIndexer ready for use!")


if __name__ == "__main__":
    main()

