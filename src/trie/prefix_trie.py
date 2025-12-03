"""Prefix-based trie with DFS traversal for autocomplete."""

from typing import Dict, List, Optional, Set
from functools import lru_cache
from .trie_node import TrieNode


class PrefixTrie:
    """Prefix-based trie data structure with DFS for efficient autocomplete."""
    
    def __init__(self, case_sensitive: bool = True):
        self.root = TrieNode()
        self.case_sensitive = case_sensitive
        self._size = 0
        # Cache for frequent prefix lookups
        self._prefix_cache: Dict[str, List[dict]] = {}
        self._cache_max_size = 100
        
    def _normalize(self, text: str) -> str:
        """Normalize text based on case sensitivity."""
        return text if self.case_sensitive else text.lower()
    
    def insert(self, word: str, metadata: Optional[dict] = None) -> None:
        """
        Insert a word into the trie.
        
        Args:
            word: The word/identifier to insert
            metadata: Optional metadata (type, file, line, scope, etc.)
        """
        if not word:
            return
            
        word = self._normalize(word)
        node = self.root
        
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode(char)
            node = node.children[char]
        
        # Mark as end of word and store metadata
        if not node.is_end:
            self._size += 1
        node.is_end = True
        node.frequency += 1
        
        if metadata:
            # Update or add metadata
            completion_data = {
                "text": word,
                "frequency": node.frequency,
                **(metadata or {})
            }
            # Check if this exact completion already exists
            existing = next(
                (c for c in node.completions if c.get("text") == word),
                None
            )
            if existing:
                existing["frequency"] = node.frequency
                if metadata:
                    existing.update(metadata)
            else:
                node.completions.append(completion_data)
        else:
            # Add basic completion if no metadata provided
            if not any(c.get("text") == word for c in node.completions):
                node.completions.append({
                    "text": word,
                    "frequency": node.frequency
                })
        
        # Invalidate cache for prefixes of this word
        self._invalidate_cache_for_prefix(word)
    
    def _invalidate_cache_for_prefix(self, word: str) -> None:
        """Invalidate cache entries for all prefixes of a word."""
        prefixes_to_remove = []
        for cached_prefix in self._prefix_cache.keys():
            if word.startswith(cached_prefix) or cached_prefix.startswith(word):
                prefixes_to_remove.append(cached_prefix)
        for prefix in prefixes_to_remove:
            self._prefix_cache.pop(prefix, None)
    
    def search(self, prefix: str) -> bool:
        """Check if a prefix exists in the trie."""
        prefix = self._normalize(prefix)
        node = self._find_node(prefix)
        return node is not None
    
    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """Find the node corresponding to the given prefix."""
        prefix = self._normalize(prefix)
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        
        return node
    
    def get_completions(
        self,
        prefix: str,
        max_results: int = 50,
        min_score: float = 0.0
    ) -> List[dict]:
        """
        Get all completions for a given prefix using DFS.
        
        Args:
            prefix: The prefix to search for
            max_results: Maximum number of results to return
            min_score: Minimum score threshold for results
            
        Returns:
            List of completion dictionaries with metadata
        """
        prefix = self._normalize(prefix)
        
        # Check cache first
        cache_key = f"{prefix}:{max_results}:{min_score}"
        if cache_key in self._prefix_cache:
            return self._prefix_cache[cache_key]
        
        node = self._find_node(prefix)
        
        if node is None:
            return []
        
        completions: List[dict] = []
        self._dfs_collect(node, prefix, completions, max_results, min_score)
        
        # Sort by frequency/score (higher is better)
        completions.sort(key=lambda x: x.get("frequency", 0), reverse=True)
        
        result = completions[:max_results]
        
        # Cache result (with size limit)
        if len(self._prefix_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._prefix_cache))
            self._prefix_cache.pop(oldest_key)
        self._prefix_cache[cache_key] = result
        
        return result
    
    def _dfs_collect(
        self,
        node: TrieNode,
        current_prefix: str,
        completions: List[dict],
        max_results: int,
        min_score: float
    ) -> None:
        """
        Perform DFS to collect all completions from a given node.
        
        Args:
            node: Current trie node
            current_prefix: Current prefix string
            completions: List to collect completions into
            max_results: Maximum results to collect
            min_score: Minimum score threshold
        """
        if len(completions) >= max_results:
            return
        
        # If this node marks the end of a word, add it
        if node.is_end:
            for completion in node.completions:
                if len(completions) >= max_results:
                    return
                
                # Calculate score based on frequency
                score = min(1.0, completion.get("frequency", 0) / 100.0)
                if score >= min_score:
                    completion_copy = completion.copy()
                    completion_copy["score"] = score
                    completions.append(completion_copy)
        
        # Recursively traverse all children
        # Sort children for consistent ordering
        for char, child_node in sorted(node.children.items()):
            if len(completions) >= max_results:
                return
            self._dfs_collect(
                child_node,
                current_prefix + char,
                completions,
                max_results,
                min_score
            )
    
    def get_all_with_prefix(self, prefix: str) -> List[str]:
        """Get all words that start with the given prefix (simple version)."""
        completions = self.get_completions(prefix)
        return [c.get("text", "") for c in completions if c.get("text")]
    
    def size(self) -> int:
        """Get the number of unique words in the trie."""
        return self._size
    
    def clear(self) -> None:
        """Clear all entries from the trie."""
        self.root = TrieNode()
        self._size = 0
        self._prefix_cache.clear()
    
    def clear_cache(self) -> None:
        """Clear the prefix cache."""
        self._prefix_cache.clear()
