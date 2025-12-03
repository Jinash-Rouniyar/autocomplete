"""Analyze code context to improve autocomplete suggestions."""

from typing import Dict, List, Optional, Set
from ..parser.ast_parser import ASTParser
from ..parser.symbol_extractor import SymbolExtractor


class ContextAnalyzer:
    """Analyzes code context to determine scope and available symbols."""
    
    def __init__(self, language: str = "python"):
        self.language = language.lower()
        self.parser = ASTParser(language)
    
    def analyze_context(
        self,
        code: str,
        cursor_line: int,
        cursor_column: int
    ) -> dict:
        """
        Analyze the context at a given cursor position.
        
        Args:
            code: Full source code
            cursor_line: Line number (1-indexed)
            cursor_column: Column number (1-indexed)
            
        Returns:
            Context dictionary with scope, available symbols, etc.
        """
        tree = self.parser.parse(code)
        if not tree:
            return {
                "scope": "module",
                "scope_path": [],
                "available_symbols": [],
                "current_line": code.split("\n")[cursor_line - 1] if cursor_line <= len(code.split("\n")) else ""
            }
        
        # Find the node at cursor position
        # Convert to 0-indexed for tree-sitter
        point = (cursor_line - 1, cursor_column - 1)
        node = tree.root_node.descendant_for_point_range(point, point)
        
        # Determine scope by walking up the tree
        scope_path = []
        current_node = node
        
        while current_node:
            node_type = current_node.type
            
            if self.language == "python":
                if node_type == "function_definition":
                    name_node = current_node.child_by_field_name("name")
                    if name_node:
                        scope_path.insert(0, name_node.text.decode("utf-8"))
                elif node_type == "class_definition":
                    name_node = current_node.child_by_field_name("name")
                    if name_node:
                        scope_path.insert(0, name_node.text.decode("utf-8"))
            elif self.language in ["typescript", "javascript"]:
                if node_type == "function_declaration":
                    name_node = current_node.child_by_field_name("name")
                    if name_node:
                        scope_path.insert(0, name_node.text.decode("utf-8"))
                elif node_type == "class_declaration":
                    name_node = current_node.child_by_field_name("name")
                    if name_node:
                        scope_path.insert(0, name_node.text.decode("utf-8"))
            
            current_node = current_node.parent
        
        # Extract available symbols in current context
        available_symbols = self._extract_context_symbols(tree, node, code)
        
        # Determine scope string
        scope = ".".join(scope_path) if scope_path else "module"
        
        # Get current line
        lines = code.split("\n")
        current_line = lines[cursor_line - 1] if 0 < cursor_line <= len(lines) else ""
        
        return {
            "scope": scope,
            "scope_path": scope_path,
            "available_symbols": available_symbols,
            "current_line": current_line,
            "node_type": node.type if node else None
        }
    
    def _extract_context_symbols(
        self,
        tree,
        cursor_node,
        source_code: str
    ) -> List[str]:
        """Extract symbols available in the current context."""
        symbols: List[str] = []
        
        # Extract all symbols from the file
        all_symbols = self.parser.extract_symbols(source_code)
        
        # Find the scope we're in
        current_scope_path = []
        node = cursor_node
        
        while node:
            node_type = node.type
            if self.language == "python":
                if node_type == "function_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        current_scope_path.insert(0, name_node.text.decode("utf-8"))
                elif node_type == "class_definition":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        current_scope_path.insert(0, name_node.text.decode("utf-8"))
            elif self.language in ["typescript", "javascript"]:
                if node_type == "function_declaration":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        current_scope_path.insert(0, name_node.text.decode("utf-8"))
                elif node_type == "class_declaration":
                    name_node = node.child_by_field_name("name")
                    if name_node:
                        current_scope_path.insert(0, name_node.text.decode("utf-8"))
            node = node.parent
        
        current_scope = ".".join(current_scope_path) if current_scope_path else "module"
        
        # Collect symbols in current scope and parent scopes
        for symbol in all_symbols:
            symbol_scope = symbol.get("scope", "module")
            # Include if in same scope, parent scope, or module level
            if (symbol_scope == current_scope or
                current_scope.startswith(symbol_scope + ".") or
                symbol_scope == "module" or
                symbol_scope == "builtin"):
                symbols.append(symbol["name"])
        
        return list(set(symbols))  # Remove duplicates
    
    def get_prefix_from_code(
        self,
        code: str,
        cursor_line: int,
        cursor_column: int
    ) -> str:
        """
        Extract the prefix being typed from code and cursor position.
        
        Args:
            code: Full source code
            cursor_line: Line number (1-indexed)
            cursor_column: Column number (1-indexed)
            
        Returns:
            The prefix string being typed
        """
        lines = code.split("\n")
        if cursor_line < 1 or cursor_line > len(lines):
            return ""
        
        current_line = lines[cursor_line - 1]
        if cursor_column < 1 or cursor_column > len(current_line) + 1:
            return ""
        
        # Find the start of the current identifier
        line_prefix = current_line[:cursor_column - 1]
        
        # Find the start of the word (backwards from cursor)
        start = cursor_column - 1
        while start > 0 and (current_line[start - 1].isalnum() or current_line[start - 1] in ["_", "."]):
            start -= 1
        
        prefix = current_line[start:cursor_column - 1]
        return prefix

