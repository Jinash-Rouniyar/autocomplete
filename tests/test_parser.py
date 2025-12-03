"""Tests for AST parser."""

import unittest
from src.parser.ast_parser import ASTParser


class TestASTParser(unittest.TestCase):
    """Test cases for ASTParser."""
    
    def test_python_parsing(self):
        """Test Python code parsing."""
        parser = ASTParser("python")
        code = """
def hello():
    x = 10
    return x

class MyClass:
    def method(self):
        pass
"""
        symbols = parser.extract_symbols(code)
        
        # Should extract function, class, and variable
        names = [s["name"] for s in symbols]
        self.assertIn("hello", names)
        self.assertIn("MyClass", names)
        self.assertIn("x", names)
    
    def test_symbol_types(self):
        """Test that symbols have correct types."""
        parser = ASTParser("python")
        code = """
def func():
    pass

class MyClass:
    pass

x = 10
"""
        symbols = parser.extract_symbols(code)
        
        types = {s["name"]: s["type"] for s in symbols}
        self.assertEqual(types.get("func"), "function")
        self.assertEqual(types.get("MyClass"), "class")
        self.assertEqual(types.get("x"), "variable")
    
    def test_get_identifiers(self):
        """Test getting all identifiers."""
        parser = ASTParser("python")
        code = "x = 10\ny = 20"
        identifiers = parser.get_identifiers(code)
        self.assertIn("x", identifiers)
        self.assertIn("y", identifiers)


if __name__ == "__main__":
    unittest.main()

