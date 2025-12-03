"""Index entire codebase and populate trie with symbols."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..parser.ast_parser import ASTParser
from ..parser.language_support import LanguageSupport
from ..trie.prefix_trie import PrefixTrie
from .symbol_store import SymbolStore


class CodebaseIndexer:
    """Indexes a codebase and builds autocomplete trie."""
    
    def __init__(self, case_sensitive: bool = True, max_workers: int = 4):
        self.trie = PrefixTrie(case_sensitive=case_sensitive)
        self.symbol_store = SymbolStore()
        self.language_support = LanguageSupport()
        self.indexed_files: Set[str] = set()
        self.file_languages: Dict[str, str] = {}
        self.max_workers = max_workers
        self._seed_default_symbols()

    def _seed_default_symbols(self) -> None:
        """Seed trie with a small set of built-in symbols for each language."""
        # Python builtins and common keywords
        python_builtins = [
            ("print", "builtin"),
            ("len", "builtin"),
            ("range", "builtin"),
            ("str", "builtin"),
            ("int", "builtin"),
            ("float", "builtin"),
            ("list", "builtin"),
            ("dict", "builtin"),
            ("set", "builtin"),
            ("tuple", "builtin"),
        ]
        python_keywords = [
            "def", "class", "return", "if", "elif", "else",
            "for", "while", "try", "except", "finally",
            "with", "as", "import", "from", "pass",
            "break", "continue", "yield", "lambda",
        ]

        for name, sym_type in python_builtins:
            metadata = {
                "type": sym_type,
                "file": "builtin",
                "line": None,
                "scope": "builtin",
                "language": "python",
            }
            self.trie.insert(name, metadata)
            self.symbol_store.add_symbol(
                {
                    "name": name,
                    "type": sym_type,
                    "scope": "builtin",
                    "file": "builtin",
                    "line": None,
                    "language": "python",
                }
            )

        for kw in python_keywords:
            metadata = {
                "type": "keyword",
                "file": "builtin",
                "line": None,
                "scope": "builtin",
                "language": "python",
            }
            self.trie.insert(kw, metadata)
            self.symbol_store.add_symbol(
                {
                    "name": kw,
                    "type": "keyword",
                    "scope": "builtin",
                    "file": "builtin",
                    "line": None,
                    "language": "python",
                }
            )

        # TypeScript / JavaScript common globals and keywords (minimal set)
        ts_js_builtins = [
            ("console", "builtin"),
            ("Array", "builtin"),
            ("Object", "builtin"),
            ("String", "builtin"),
            ("Number", "builtin"),
            ("Boolean", "builtin"),
            ("Promise", "builtin"),
        ]
        ts_js_keywords = [
            "function", "class", "return", "if", "else",
            "for", "while", "try", "catch", "finally",
            "import", "from", "export", "const", "let", "var",
            "async", "await",
        ]

        for name, sym_type in ts_js_builtins:
            metadata = {
                "type": sym_type,
                "file": "builtin",
                "line": None,
                "scope": "builtin",
                "language": "typescript",
            }
            self.trie.insert(name, metadata)
            self.symbol_store.add_symbol(
                {
                    "name": name,
                    "type": sym_type,
                    "scope": "builtin",
                    "file": "builtin",
                    "line": None,
                    "language": "typescript",
                }
            )

        for kw in ts_js_keywords:
            metadata = {
                "type": "keyword",
                "file": "builtin",
                "line": None,
                "scope": "builtin",
                "language": "typescript",
            }
            self.trie.insert(kw, metadata)
            self.symbol_store.add_symbol(
                {
                    "name": kw,
                    "type": "keyword",
                    "scope": "builtin",
                    "file": "builtin",
                    "line": None,
                    "language": "typescript",
                }
            )
    
    def index_file(
        self,
        file_path: str,
        language: Optional[str] = None
    ) -> int:
        """
        Index a single file and add its symbols to the trie.
        
        Args:
            file_path: Path to the file to index
            language: Optional language override
            
        Returns:
            Number of symbols indexed
        """
        try:
            # Detect language if not provided
            if not language:
                language = self.language_support.detect_language(file_path)
                if not language:
                    return 0
            
            # Read file
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()
            
            # Skip very large files (performance optimization)
            if len(source_code) > 1_000_000:  # 1MB limit
                print(f"Skipping large file: {file_path} ({len(source_code)} bytes)")
                return 0
            
            # Parse and extract symbols
            parser = ASTParser(language)
            symbols = parser.extract_symbols(source_code)
            
            # Add symbols to trie and store
            count = 0
            for symbol in symbols:
                # Add metadata
                symbol["file"] = file_path
                symbol["language"] = language
                
                # Add to symbol store
                self.symbol_store.add_symbol(symbol)
                
                # Add to trie with metadata
                metadata = {
                    "type": symbol.get("type", "identifier"),
                    "file": file_path,
                    "line": symbol.get("line"),
                    "scope": symbol.get("scope", "module"),
                    "language": language,
                }
                self.trie.insert(symbol["name"], metadata)
                count += 1
            
            self.indexed_files.add(file_path)
            self.file_languages[file_path] = language
            return count
            
        except Exception as e:
            print(f"Error indexing file {file_path}: {e}")
            return 0
    
    def index_directory(
        self,
        directory: str,
        languages: Optional[List[str]] = None,
        max_workers: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Index all supported files in a directory recursively.
        
        Args:
            directory: Root directory to index
            languages: Optional list of languages to index (default: all)
            max_workers: Number of parallel workers (default: self.max_workers)
            
        Returns:
            Dictionary with statistics (files_indexed, symbols_indexed, etc.)
        """
        if languages is None:
            languages = list(self.language_support.SUPPORTED_LANGUAGES.keys())
        
        if max_workers is None:
            max_workers = self.max_workers
        
        # Collect all files to index
        files_to_index: List[tuple] = []
        
        for root, dirs, files in os.walk(directory):
            # Skip common directories (performance optimization)
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".") and
                d not in ["node_modules", "__pycache__", ".git", "venv", "env", "dist", "build"]
            ]
            
            for file in files:
                file_path = os.path.join(root, file)
                language = self.language_support.detect_language(file_path)
                
                if language and language in languages:
                    files_to_index.append((file_path, language))
        
        # Index files in parallel
        total_symbols = 0
        indexed_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.index_file, file_path, lang): file_path
                for file_path, lang in files_to_index
            }
            
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    count = future.result()
                    if count > 0:
                        indexed_count += 1
                        total_symbols += count
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        
        # Clear trie cache after indexing (fresh start)
        self.trie.clear_cache()
        
        return {
            "files_indexed": indexed_count,
            "total_files": len(files_to_index),
            "symbols_indexed": total_symbols,
            "unique_symbols": self.trie.size()
        }
    
    def get_completions(
        self,
        prefix: str,
        max_results: int = 50,
        context: Optional[dict] = None
    ) -> List[dict]:
        """
        Get autocomplete suggestions for a prefix.
        
        Args:
            prefix: The prefix to complete
            max_results: Maximum number of results
            context: Optional context (scope, file, etc.) for filtering
            
        Returns:
            List of completion dictionaries
        """
        completions = self.trie.get_completions(prefix, max_results=max_results)
        
        # Apply context filtering if provided
        if context:
            scope = context.get("scope")
            if scope:
                # Filter by scope relevance
                scope_symbols = set(self.symbol_store.get_symbols_in_scope(scope))
                for completion in completions:
                    if completion.get("text") in scope_symbols:
                        completion["score"] = completion.get("score", 0.5) + 0.3
        
        return completions
    
    def clear(self) -> None:
        """Clear all indexed data."""
        self.trie.clear()
        self.symbol_store.clear()
        self.indexed_files.clear()
        self.file_languages.clear()
    
    def get_stats(self) -> dict:
        """Get indexing statistics."""
        return {
            "files_indexed": len(self.indexed_files),
            "unique_symbols": self.trie.size(),
            "total_symbols": self.symbol_store.size(),
            "languages": list(set(self.file_languages.values()))
        }
