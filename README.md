# Autocomplete Engine

A high-performance autocomplete engine using prefix-based trie with DFS algorithms and AST analysis, similar to VSCode IntelliSense. Supports multiple languages (Python, TypeScript, JavaScript) with context-aware suggestions.

## 🎥 Demo

Watch a demo of the autocomplete engine in action: [Loom Video](https://www.loom.com/share/f4c52fbf6b344b818e33f81bf28e599f)

## Features

- **Prefix-based Trie**: Efficient prefix matching with DFS traversal
- **AST Analysis**: Uses tree-sitter for parsing and context understanding
- **Multi-language Support**: Python, TypeScript, and JavaScript
- **Context-Aware**: Analyzes code context to provide relevant suggestions
- **Fast Performance**: Optimized with parallel processing and caching
- **Streaming API**: Real-time streaming support for autocomplete suggestions
- **Symbol Extraction**: Extracts functions, classes, variables, imports, and keywords

## Architecture

### Core Components

1. **Trie Module** (`src/trie/`): Prefix-based trie with DFS for fast completion lookup
2. **Parser Module** (`src/parser/`): AST parsing using tree-sitter
3. **Indexer Module** (`src/indexer/`): Codebase indexing and symbol storage
4. **Context Module** (`src/context/`): Context analysis and suggestion ranking
5. **API Module** (`src/api/`): FastAPI backend with REST endpoints

## Installation

1. **Clone and install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Index a codebase** (optional, can be done via API):
```python
from src.indexer.codebase_indexer import CodebaseIndexer

indexer = CodebaseIndexer()
stats = indexer.index_directory("/path/to/codebase")
print(stats)
```

## Usage

### Start the Server

```bash
python -m src.api.main
# or
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### API Endpoints

#### POST `/api/autocomplete`

Get autocomplete suggestions:

```json
{
  "code": "def hello():\n    pri",
  "prefix": "pri",
  "language": "python",
  "cursor_line": 2,
  "cursor_column": 7,
  "max_results": 10
}
```

Response:
```json
{
  "suggestions": [
    {
      "text": "print",
      "type": "builtin",
      "score": 0.95,
      "metadata": {
        "file": "builtin",
        "scope": "builtin"
      }
    }
  ],
  "context": {
    "scope": "function",
    "scope_path": ["hello"],
    "available_symbols": ["hello"]
  },
  "prefix": "pri"
}
```

#### POST `/api/autocomplete_stream`

Stream autocomplete suggestions in real-time (Server-Sent Events).

#### POST `/api/index`

Index a codebase directory:
```json
{
  "directory": "/path/to/codebase",
  "languages": ["python", "typescript"]
}
```

#### GET `/api/stats`

Get indexing statistics.

## Sample Codebases

To test with real codebases, you can download:

- **Python**: Django framework
- **TypeScript/JavaScript**: TypeScript compiler source

Place them in `data/sample_codebases/` and index via the API.

## Performance Optimizations

- Parallel file processing during indexing
- Trie node caching for frequent prefixes
- Early termination in DFS traversal
- Result limiting and ranking
- Incremental indexing support

## Scoring and Ranking

Each suggestion gets a **score** in two stages:

1. **Base score from frequency (trie)**  
   - Every time a word is inserted, its `frequency` counter increases.  
   - Base score is computed as:
     - \\( \text{base\_score} = \min(1.0, \text{frequency} / 100) \\)
   - This favors symbols that appear more often in the indexed codebase.

2. **Context-aware reranking** (in `SuggestionRanker`)  
   The base score is then adjusted by:
   - **Type weight** (keywords and builtins are weighted above functions, classes, variables, generic identifiers)
   - **Prefix match**:
     - Exact keyword match is boosted to the top
     - Keywords starting with the prefix are preferred over other symbols
   - **Scope match** (symbols in the current scope or its parents get a boost)
   - **Availability** (symbols in the `available_symbols` list from the context analyzer get a boost)
   - **Language match** (symbols from the active language are preferred; other languages are heavily downweighted)
   - **Frequency boost** (a small extra boost proportional to frequency, capped)

## Development

Project structure:
```
autocomplete/
├── src/
│   ├── parser/      # AST parsing
│   ├── trie/         # Trie data structure
│   ├── indexer/      # Codebase indexing
│   ├── context/      # Context analysis
│   └── api/          # FastAPI backend
├── data/             # Sample codebases
├── tests/            # Unit tests
└── requirements.txt
```

## License

MIT

