"""Example usage of the autocomplete engine."""

from src.indexer.codebase_indexer import CodebaseIndexer
from src.context.context_analyzer import ContextAnalyzer
from src.context.suggestion_ranker import SuggestionRanker


def example_basic_usage():
    """Basic example of using the autocomplete engine."""
    print("=" * 60)
    print("Basic Autocomplete Engine Example")
    print("=" * 60)
    
    # Create indexer
    indexer = CodebaseIndexer()
    
    # Index some sample code (in-memory)
    sample_code = """
def hello_world():
    print("Hello, World!")
    x = 10
    return x

class MyClass:
    def __init__(self):
        self.value = 0
    
    def method(self):
        return self.value

def calculate(a, b):
    result = a + b
    return result
"""
    
    # For demo, we'll manually add some symbols
    indexer.trie.insert("print", {"type": "builtin", "scope": "builtin"})
    indexer.trie.insert("hello_world", {"type": "function", "scope": "module"})
    indexer.trie.insert("MyClass", {"type": "class", "scope": "module"})
    indexer.trie.insert("calculate", {"type": "function", "scope": "module"})
    indexer.trie.insert("result", {"type": "variable", "scope": "function"})
    
    # Test autocomplete
    print("\n1. Testing prefix 'pri':")
    completions = indexer.get_completions("pri", max_results=5)
    for comp in completions:
        print(f"   - {comp.get('text')} ({comp.get('type')})")
    
    print("\n2. Testing prefix 'calc':")
    completions = indexer.get_completions("calc", max_results=5)
    for comp in completions:
        print(f"   - {comp.get('text')} ({comp.get('type')})")
    
    # Test context analysis
    print("\n3. Testing context analysis:")
    analyzer = ContextAnalyzer("python")
    context = analyzer.analyze_context(sample_code, cursor_line=3, cursor_column=5)
    print(f"   Scope: {context['scope']}")
    print(f"   Available symbols: {context['available_symbols'][:5]}")
    
    # Test ranking
    print("\n4. Testing suggestion ranking:")
    ranker = SuggestionRanker()
    ranked = ranker.rank(completions, context=context)
    for comp in ranked[:3]:
        print(f"   - {comp.get('text')} (score: {comp.get('score', 0):.2f})")
    
    print("\n" + "=" * 60)
    print("Example complete!")


if __name__ == "__main__":
    example_basic_usage()

