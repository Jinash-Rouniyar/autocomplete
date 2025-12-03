"""Extract symbols (identifiers, functions, classes) from AST."""

from typing import Dict, List, Optional, Set
from tree_sitter import Node, Tree


class SymbolExtractor:
    """Extracts symbols and identifiers from parsed AST."""
    
    # Node types that represent identifiers
    IDENTIFIER_TYPES = {
        "python": {
            "identifier": "identifier",
            "function": "function_definition",
            "class": "class_definition",
            "variable": "identifier",
            "import": "import_statement",
            "import_from": "import_from_statement"
        },
        "typescript": {
            "identifier": "identifier",
            "function": "function_declaration",
            "class": "class_declaration",
            "variable": "variable_declaration",
            "import": "import_statement"
        },
        "javascript": {
            "identifier": "identifier",
            "function": "function_declaration",
            "class": "class_declaration",
            "variable": "variable_declaration",
            "import": "import_statement"
        }
    }
    
    def __init__(self, language: str):
        self.language = language.lower()
        self.node_types = self.IDENTIFIER_TYPES.get(self.language, {})
    
    def extract_symbols(self, tree: Tree, source: bytes) -> List[dict]:
        """
        Extract all symbols from the AST.
        
        Returns:
            List of symbol dictionaries with type, name, and metadata
        """
        symbols: List[dict] = []
        root = tree.root_node
        
        if self.language == "python":
            self._extract_python_symbols(root, source, symbols)
        elif self.language in ["typescript", "javascript"]:
            self._extract_js_ts_symbols(root, source, symbols)
        
        return symbols
    
    def _extract_python_symbols(
        self,
        node: Node,
        source: bytes,
        symbols: List[dict],
        scope: List[str] = None
    ) -> None:
        """Extract symbols from Python AST."""
        if scope is None:
            scope = []
        
        node_type = node.type
        
        # Extract function definitions
        if node_type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                symbols.append({
                    "name": name,
                    "type": "function",
                    "scope": ".".join(scope) if scope else "module",
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
                # Recurse into function body with new scope
                body = node.child_by_field_name("body")
                if body:
                    new_scope = scope + [name]
                    for child in body.children:
                        self._extract_python_symbols(child, source, symbols, new_scope)
                return
        
        # Extract class definitions
        if node_type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                symbols.append({
                    "name": name,
                    "type": "class",
                    "scope": ".".join(scope) if scope else "module",
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
                # Recurse into class body
                body = node.child_by_field_name("body")
                if body:
                    new_scope = scope + [name]
                    for child in body.children:
                        self._extract_python_symbols(child, source, symbols, new_scope)
                return
        
        # Extract variable assignments
        if node_type == "assignment":
            left = node.child_by_field_name("left")
            if left and left.type == "identifier":
                name = left.text.decode("utf-8")
                symbols.append({
                    "name": name,
                    "type": "variable",
                    "scope": ".".join(scope) if scope else "module",
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Extract imports
        if node_type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name" or child.type == "aliased_import":
                    # Extract module or alias name
                    name_node = child.child_by_field_name("name") or child.children[0]
                    if name_node:
                        name = name_node.text.decode("utf-8")
                        symbols.append({
                            "name": name,
                            "type": "import",
                            "scope": "module",
                            "line": node.start_point[0] + 1,
                            "column": node.start_point[1]
                        })
        
        if node_type == "import_from_statement":
            # Extract imported names
            import_list = node.child_by_field_name("module_name")
            if import_list:
                module_name = import_list.text.decode("utf-8")
                symbols.append({
                    "name": module_name,
                    "type": "import",
                    "scope": "module",
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Extract standalone identifiers (keywords, builtins)
        if node_type == "identifier":
            name = node.text.decode("utf-8")
            # Only add if not already added as part of a definition
            # This is a simple heuristic - could be improved
            if name not in [s["name"] for s in symbols if s.get("line") == node.start_point[0] + 1]:
                # Check if it's a Python keyword or builtin
                if self._is_python_builtin(name):
                    symbols.append({
                        "name": name,
                        "type": "builtin",
                        "scope": "builtin",
                        "line": node.start_point[0] + 1,
                        "column": node.start_point[1]
                    })
        
        # Recurse into children
        for child in node.children:
            self._extract_python_symbols(child, source, symbols, scope)
    
    def _extract_js_ts_symbols(
        self,
        node: Node,
        source: bytes,
        symbols: List[dict],
        scope: List[str] = None
    ) -> None:
        """Extract symbols from JavaScript/TypeScript AST."""
        if scope is None:
            scope = []
        
        node_type = node.type
        
        # Extract function declarations
        if node_type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                symbols.append({
                    "name": name,
                    "type": "function",
                    "scope": ".".join(scope) if scope else "module",
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
                # Recurse into function body
                body = node.child_by_field_name("body")
                if body:
                    new_scope = scope + [name]
                    for child in body.children:
                        self._extract_js_ts_symbols(child, source, symbols, new_scope)
                return
        
        # Extract class declarations
        if node_type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                symbols.append({
                    "name": name,
                    "type": "class",
                    "scope": ".".join(scope) if scope else "module",
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
                # Recurse into class body
                body = node.child_by_field_name("body")
                if body:
                    new_scope = scope + [name]
                    for child in body.children:
                        self._extract_js_ts_symbols(child, source, symbols, new_scope)
                return
        
        # Extract variable declarations
        if node_type == "variable_declaration":
            for child in node.children:
                if child.type == "variable_declarator":
                    name_node = child.child_by_field_name("name")
                    if name_node and name_node.type == "identifier":
                        name = name_node.text.decode("utf-8")
                        symbols.append({
                            "name": name,
                            "type": "variable",
                            "scope": ".".join(scope) if scope else "module",
                            "line": node.start_point[0] + 1,
                            "column": node.start_point[1]
                        })
        
        # Extract imports
        if node_type == "import_statement":
            # Extract default import or named imports
            for child in node.children:
                if child.type == "identifier":
                    name = child.text.decode("utf-8")
                    symbols.append({
                        "name": name,
                        "type": "import",
                        "scope": "module",
                        "line": node.start_point[0] + 1,
                        "column": node.start_point[1]
                    })
        
        # Extract identifiers
        if node_type == "identifier":
            name = node.text.decode("utf-8")
            # Check if it's a builtin
            if self._is_js_builtin(name):
                symbols.append({
                    "name": name,
                    "type": "builtin",
                    "scope": "builtin",
                    "line": node.start_point[0] + 1,
                    "column": node.start_point[1]
                })
        
        # Recurse into children
        for child in node.children:
            self._extract_js_ts_symbols(child, source, symbols, scope)
    
    def _is_python_builtin(self, name: str) -> bool:
        """Check if a name is a Python builtin."""
        python_builtins = {
            "print", "len", "str", "int", "float", "list", "dict", "set",
            "tuple", "range", "enumerate", "zip", "map", "filter", "sorted",
            "max", "min", "sum", "abs", "round", "type", "isinstance",
            "hasattr", "getattr", "setattr", "delattr", "dir", "vars",
            "open", "file", "input", "eval", "exec", "compile", "repr",
            "format", "chr", "ord", "hex", "oct", "bin", "bool", "bytes",
            "bytearray", "memoryview", "slice", "property", "staticmethod",
            "classmethod", "super", "object", "Exception", "BaseException"
        }
        return name in python_builtins
    
    def _is_js_builtin(self, name: str) -> bool:
        """Check if a name is a JavaScript builtin."""
        js_builtins = {
            "console", "window", "document", "Array", "Object", "String",
            "Number", "Boolean", "Date", "Math", "JSON", "Promise",
            "Set", "Map", "WeakSet", "WeakMap", "Symbol", "Proxy",
            "Reflect", "Error", "TypeError", "ReferenceError", "parseInt",
            "parseFloat", "isNaN", "isFinite", "encodeURI", "decodeURI",
            "encodeURIComponent", "decodeURIComponent", "eval", "Function"
        }
        return name in js_builtins

