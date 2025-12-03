"""Rank autocomplete suggestions by relevance."""

from typing import Dict, List, Optional


class SuggestionRanker:
    """Ranks autocomplete suggestions by relevance."""
    
    def __init__(self):
        self.type_weights = {
            "keyword": 1.4,
            "builtin": 1.2,
            "function": 1.0,
            "class": 0.95,
            "variable": 0.7,
            "import": 0.7,
            "identifier": 0.6,
        }
    
    def rank(
        self,
        suggestions: List[dict],
        context: Optional[dict] = None
    ) -> List[dict]:
        """
        Rank suggestions by relevance.
        
        Args:
            suggestions: List of suggestion dictionaries
            context: Optional context information
            
        Returns:
            Ranked list of suggestions
        """
        if not suggestions:
            return []
        
        # Calculate scores for each suggestion
        scored_suggestions = []
        available_symbols = set(context.get("available_symbols", [])) if context else set()
        scope = context.get("scope", "") if context else ""
        context_language = context.get("language") if context else None
        prefix = context.get("prefix", "") if context else ""
        
        for suggestion in suggestions:
            score = suggestion.get("score", 0.5)
            
            # Boost score based on type
            symbol_type = suggestion.get("type", "identifier")
            type_weight = self.type_weights.get(symbol_type, 0.5)
            score *= type_weight
            
            # Boost if in current scope
            suggestion_scope = suggestion.get("scope", "")
            if suggestion_scope == scope:
                score *= 1.2
            elif scope and suggestion_scope and scope.startswith(suggestion_scope + "."):
                score *= 1.1
            
            # Boost if in available symbols
            text = suggestion.get("text", "")
            if text in available_symbols:
                score *= 1.15

            # Strongly prefer language keywords that match the current prefix
            if prefix and text:
                if text == prefix and symbol_type == "keyword":
                    # Exact keyword match -> top priority
                    score *= 3.0
                elif text.startswith(prefix) and symbol_type == "keyword":
                    # Keyword starting with the prefix
                    score *= 2.0
                elif text.startswith(prefix):
                    # Non-keyword starting with the prefix still gets a small bump
                    score *= 1.2
            
            # Penalize suggestions from a different language, if language info is available
            suggestion_language = suggestion.get("language")
            if context_language and suggestion_language:
                if suggestion_language == context_language:
                    # Prefer same-language symbols
                    score *= 1.3
                else:
                    # Heavily downweight other languages
                    score *= 0.1
            
            # Boost based on frequency
            frequency = suggestion.get("frequency", 0)
            if frequency > 0:
                frequency_boost = min(1.2, 1.0 + (frequency / 100.0))
                score *= frequency_boost
            
            # Normalize score to 0-1 range
            score = min(1.0, score)
            
            suggestion_copy = suggestion.copy()
            suggestion_copy["score"] = score
            scored_suggestions.append(suggestion_copy)
        
        # Sort by score (descending)
        scored_suggestions.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return scored_suggestions
    
    def filter_by_type(
        self,
        suggestions: List[dict],
        allowed_types: Optional[List[str]] = None
    ) -> List[dict]:
        """Filter suggestions by type."""
        if not allowed_types:
            return suggestions
        
        return [
            s for s in suggestions
            if s.get("type") in allowed_types
        ]
    
    def limit_results(
        self,
        suggestions: List[dict],
        max_results: int = 10
    ) -> List[dict]:
        """Limit the number of results."""
        return suggestions[:max_results]

