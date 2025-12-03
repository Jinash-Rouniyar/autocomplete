"""AST parser using tree-sitter."""

from typing import List, Optional
from tree_sitter import Parser, Tree
from .language_support import LanguageSupport
from .symbol_extractor import SymbolExtractor


class ASTParser:
    """Parser for extracting AST and symbols from source code."""
    
    def __init__(self, language: str = "python"):
        self.language_support = LanguageSupport()
        self.language = language.lower()
        self.parser = self.language_support.get_parser(self.language)
        if not self.parser:
            raise ValueError(f"Unsupported language: {language}")
        self.symbol_extractor = SymbolExtractor(self.language)
    
    def parse(self, source_code: str) -> Optional[Tree]:
        """
        Parse source code into an AST.
        
        Args:
            source_code: Source code as string
            
        Returns:
            Tree-sitter Tree object or None if parsing fails
        """
        if not self.parser:
            return None
        
        try:
            tree = self.parser.parse(source_code.encode("utf-8"))
            return tree
        except Exception as e:
            print(f"Error parsing code: {e}")
            return None
    
    def extract_symbols(self, source_code: str) -> List[dict]:
        """
        Extract symbols from source code.
        
        Args:
            source_code: Source code as string
            
        Returns:
            List of symbol dictionaries
        """
        tree = self.parse(source_code)
        if not tree:
            return []
        
        return self.symbol_extractor.extract_symbols(tree, source_code.encode("utf-8"))
    
    def get_identifiers(self, source_code: str) -> List[str]:
        """
        Get all identifiers from source code.
        
        Args:
            source_code: Source code as string
            
        Returns:
            List of identifier names
        """
        symbols = self.extract_symbols(source_code)
        return [s["name"] for s in symbols]
    
    def set_language(self, language: str) -> None:
        """Change the language parser."""
        self.language = language.lower()
        self.parser = self.language_support.get_parser(self.language)
        if not self.parser:
            raise ValueError(f"Unsupported language: {language}")
        self.symbol_extractor = SymbolExtractor(self.language)

