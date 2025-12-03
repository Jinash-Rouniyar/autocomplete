"""Store and manage symbol metadata."""

from typing import Dict, List, Optional, Set
from collections import defaultdict


class SymbolStore:
    """Stores symbol metadata for fast lookup."""
    
    def __init__(self):
        # Map from symbol name to list of occurrences
        self.symbols: Dict[str, List[dict]] = defaultdict(list)
        # Map from file path to symbols in that file
        self.file_symbols: Dict[str, List[str]] = defaultdict(list)
        # Map from scope to symbols in that scope
        self.scope_symbols: Dict[str, List[str]] = defaultdict(list)
        # Total symbol count
        self.total_count = 0
    
    def add_symbol(self, symbol: dict) -> None:
        """
        Add a symbol to the store.
        
        Args:
            symbol: Symbol dictionary with name, type, scope, file, etc.
        """
        name = symbol.get("name")
        if not name:
            return
        
        file_path = symbol.get("file", "unknown")
        scope = symbol.get("scope", "module")
        
        # Add to main symbol index
        self.symbols[name].append(symbol)
        
        # Add to file index
        if name not in self.file_symbols[file_path]:
            self.file_symbols[file_path].append(name)
        
        # Add to scope index
        if name not in self.scope_symbols[scope]:
            self.scope_symbols[scope].append(name)
        
        self.total_count += 1
    
    def get_symbols(self, name: str) -> List[dict]:
        """Get all occurrences of a symbol by name."""
        return self.symbols.get(name, [])
    
    def get_symbols_in_scope(self, scope: str) -> List[str]:
        """Get all symbol names in a given scope."""
        return self.scope_symbols.get(scope, [])
    
    def get_symbols_in_file(self, file_path: str) -> List[str]:
        """Get all symbol names in a given file."""
        return self.file_symbols.get(file_path, [])
    
    def search_by_prefix(self, prefix: str) -> List[str]:
        """Get all symbol names that start with a prefix."""
        prefix_lower = prefix.lower()
        return [
            name for name in self.symbols.keys()
            if name.lower().startswith(prefix_lower)
        ]
    
    def get_all_symbols(self) -> Set[str]:
        """Get all unique symbol names."""
        return set(self.symbols.keys())
    
    def clear(self) -> None:
        """Clear all stored symbols."""
        self.symbols.clear()
        self.file_symbols.clear()
        self.scope_symbols.clear()
        self.total_count = 0
    
    def size(self) -> int:
        """Get total number of symbol occurrences."""
        return self.total_count
    
    def unique_count(self) -> int:
        """Get number of unique symbol names."""
        return len(self.symbols)

