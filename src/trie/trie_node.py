"""Trie node implementation for prefix-based autocomplete."""

from typing import Dict, List, Optional, Set


class TrieNode:
    """Node in a prefix trie data structure."""
    
    def __init__(self, char: str = ""):
        self.char = char
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_end = False
        self.completions: List[dict] = []  # Store completion metadata
        self.frequency = 0  # Frequency count for ranking
        
    def __repr__(self) -> str:
        return f"TrieNode(char='{self.char}', is_end={self.is_end}, children={len(self.children)})"

