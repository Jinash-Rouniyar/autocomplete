"""API routes for autocomplete endpoints."""

import json
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..indexer.codebase_indexer import CodebaseIndexer
from ..context.context_analyzer import ContextAnalyzer
from ..context.suggestion_ranker import SuggestionRanker
from .models import (
    AutocompleteRequest,
    AutocompleteResponse,
    Suggestion,
    ContextInfo,
    AutocompleteStreamChunk,
    AutocompleteStreamMeta,
    IndexRequest
)

router = APIRouter()

# Global indexer instance (initialized on startup)
indexer: Optional[CodebaseIndexer] = None
context_analyzer: Optional[ContextAnalyzer] = None
suggestion_ranker: Optional[SuggestionRanker] = None


def initialize_engine(indexer_instance: CodebaseIndexer):
    """Initialize the autocomplete engine with an indexer."""
    global indexer, context_analyzer, suggestion_ranker
    indexer = indexer_instance
    context_analyzer = ContextAnalyzer()
    suggestion_ranker = SuggestionRanker()


def _sse(event: str, data: dict) -> str:
    """Format Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(request: AutocompleteRequest):
    """
    Get autocomplete suggestions for a given prefix and context.
    """
    if indexer is None:
        raise HTTPException(status_code=503, detail="Indexer not initialized. Please index a codebase first.")
    
    start_time = time.perf_counter()
    
    # Detect prefix if not provided
    prefix = request.prefix
    if not prefix:
        analyzer = ContextAnalyzer(request.language)
        prefix = analyzer.get_prefix_from_code(
            request.code,
            request.cursor_line,
            request.cursor_column
        )
    
    if not prefix:
        return AutocompleteResponse(
            suggestions=[],
            context=None,
            prefix=""
        )
    
    # Analyze context
    analyzer = ContextAnalyzer(request.language)
    try:
        context_data = analyzer.analyze_context(
            request.code,
            request.cursor_line,
            request.cursor_column
        )
    except Exception as e:
        # Fallback to basic context if analysis fails
        context_data = {
            "scope": "module",
            "scope_path": [],
            "available_symbols": [],
            "current_line": request.code.split("\n")[request.cursor_line - 1] if request.cursor_line <= len(request.code.split("\n")) else "",
        }
    # Attach language to context for ranking
    context_data["language"] = request.language
    context_data["prefix"] = prefix
    
    # Get completions from indexer
    completions = indexer.get_completions(
        prefix,
        max_results=request.max_results * 2,  # Get more for ranking
        context=context_data
    )
    
    # Rank suggestions
    if suggestion_ranker:
        ranked = suggestion_ranker.rank(completions, context=context_data)
        ranked = suggestion_ranker.limit_results(ranked, max_results=request.max_results)
    else:
        ranked = completions[:request.max_results]
    
    # Convert to response format
    suggestions = []
    for comp in ranked:
        suggestions.append(Suggestion(
            text=comp.get("text", ""),
            type=comp.get("type", "identifier"),
            score=comp.get("score", 0.5),
            metadata={
                "file": comp.get("file"),
                "line": comp.get("line"),
                "scope": comp.get("scope"),
                "frequency": comp.get("frequency", 0)
            }
        ))
    
    # Build context info
    context_info = None
    if request.include_context:
        context_info = ContextInfo(
            scope=context_data.get("scope", "module"),
            scope_path=context_data.get("scope_path", []),
            available_symbols=context_data.get("available_symbols", []),
            current_line=context_data.get("current_line", "")
        )
    
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    
    return AutocompleteResponse(
        suggestions=suggestions,
        context=context_info,
        prefix=prefix
    )


@router.post("/autocomplete_stream")
async def autocomplete_stream(request: AutocompleteRequest):
    """
    Stream autocomplete suggestions in real-time.
    """
    if indexer is None:
        raise HTTPException(status_code=503, detail="Indexer not initialized. Please index a codebase first.")
    
    async def generate():
        t0 = time.perf_counter()
        
        # Detect prefix if not provided
        prefix = request.prefix
        if not prefix:
            analyzer = ContextAnalyzer(request.language)
            prefix = analyzer.get_prefix_from_code(
                request.code,
                request.cursor_line,
                request.cursor_column
            )
        
        if not prefix:
            yield _sse("done", {"error": "No prefix found"})
            return
        
        # Send metadata
        yield _sse("meta", {
            "language": request.language,
            "prefix": prefix
        })
        
        # Analyze context
        analyzer = ContextAnalyzer(request.language)
        try:
            context_data = analyzer.analyze_context(
                request.code,
                request.cursor_line,
                request.cursor_column
            )
        except Exception:
            # Fallback to basic context if analysis fails
            context_data = {
                "scope": "module",
                "scope_path": [],
                "available_symbols": [],
                "current_line": request.code.split("\n")[request.cursor_line - 1] if request.cursor_line <= len(request.code.split("\n")) else "",
            }
        # Attach language and prefix to context for ranking
        context_data["language"] = request.language
        context_data["prefix"] = prefix

        # Get completions
        completions = indexer.get_completions(
            prefix,
            max_results=request.max_results * 2,
            context=context_data
        )
        
        # Rank suggestions
        if suggestion_ranker:
            ranked = suggestion_ranker.rank(completions, context=context_data)
            ranked = suggestion_ranker.limit_results(ranked, max_results=request.max_results)
        else:
            ranked = completions[:request.max_results]
        
        # Send TTFB
        ttfb_ms = int((time.perf_counter() - t0) * 1000)
        yield _sse("ttfb", {"ms": ttfb_ms})
        
        # Stream suggestions
        for comp in ranked:
            chunk = AutocompleteStreamChunk(
                text=comp.get("text", ""),
                type=comp.get("type", "identifier"),
                score=comp.get("score", 0.5),
                metadata={
                    "file": comp.get("file"),
                    "line": comp.get("line"),
                    "scope": comp.get("scope"),
                    "frequency": comp.get("frequency", 0)
                }
            )
            yield _sse("chunk", chunk.model_dump())
        
        # Send completion
        total_ms = int((time.perf_counter() - t0) * 1000)
        yield _sse("done", {
            "total_suggestions": len(ranked),
            "ms_total": total_ms
        })
    
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(generate(), media_type="text/event-stream", headers=headers)


@router.get("/stats")
async def get_stats():
    """Get indexing statistics."""
    if indexer is None:
        raise HTTPException(status_code=503, detail="Indexer not initialized")
    
    return indexer.get_stats()


@router.post("/index")
async def index_codebase(request: IndexRequest):
    """Index a codebase directory."""
    global indexer
    
    if indexer is None:
        indexer = CodebaseIndexer()
        initialize_engine(indexer)
    
    stats = indexer.index_directory(request.directory, languages=request.languages)
    return stats

