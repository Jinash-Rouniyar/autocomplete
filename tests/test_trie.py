"""Tests for trie data structure."""

import unittest
from src.trie.prefix_trie import PrefixTrie


class TestPrefixTrie(unittest.TestCase):
    """Test cases for PrefixTrie."""
    
    def setUp(self):
        self.trie = PrefixTrie()
    
    def test_insert_and_search(self):
        """Test basic insert and search."""
        self.trie.insert("hello")
        self.trie.insert("world")
        
        self.assertTrue(self.trie.search("hello"))
        self.assertTrue(self.trie.search("world"))
        self.assertFalse(self.trie.search("foo"))
    
    def test_get_completions(self):
        """Test getting completions."""
        self.trie.insert("print")
        self.trie.insert("private")
        self.trie.insert("public")
        self.trie.insert("python")
        
        completions = self.trie.get_completions("pri")
        self.assertGreater(len(completions), 0)
        
        # Check that we get print and private
        texts = [c.get("text") for c in completions]
        self.assertIn("print", texts)
        self.assertIn("private", texts)
    
    def test_case_sensitive(self):
        """Test case sensitivity."""
        trie = PrefixTrie(case_sensitive=True)
        trie.insert("Hello")
        trie.insert("hello")
        
        self.assertTrue(trie.search("Hello"))
        self.assertTrue(trie.search("hello"))
        
        completions = trie.get_completions("H")
        texts = [c.get("text") for c in completions]
        self.assertIn("Hello", texts)
        self.assertNotIn("hello", texts)
    
    def test_metadata(self):
        """Test inserting with metadata."""
        metadata = {"type": "function", "file": "test.py", "line": 10}
        self.trie.insert("test_func", metadata)
        
        completions = self.trie.get_completions("test")
        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0].get("type"), "function")
        self.assertEqual(completions[0].get("file"), "test.py")
    
    def test_empty_prefix(self):
        """Test empty prefix returns all."""
        self.trie.insert("a")
        self.trie.insert("b")
        self.trie.insert("c")
        
        completions = self.trie.get_completions("", max_results=10)
        self.assertGreaterEqual(len(completions), 3)
    
    def test_max_results(self):
        """Test max_results limiting."""
        for i in range(20):
            self.trie.insert(f"word{i}")
        
        completions = self.trie.get_completions("word", max_results=5)
        self.assertLessEqual(len(completions), 5)


if __name__ == "__main__":
    unittest.main()

