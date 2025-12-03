"""Request and response models for the autocomplete API."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AutocompleteRequest(BaseModel):
    """Request model for autocomplete endpoint."""
    code: str = Field(..., description="Full source code")
    prefix: Optional[str] = Field(None, description="Prefix to complete (auto-detected if not provided)")
    language: str = Field("python", description="Programming language")
    cursor_line: int = Field(1, ge=1, description="Cursor line number (1-indexed)")
    cursor_column: int = Field(1, ge=1, description="Cursor column number (1-indexed)")
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of suggestions")
    include_context: bool = Field(True, description="Include context information in response")


class Suggestion(BaseModel):
    """Individual autocomplete suggestion."""
    text: str = Field(..., description="Completion text")
    type: str = Field(..., description="Symbol type (function, class, variable, etc.)")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    metadata: Optional[dict] = Field(None, description="Additional metadata (file, line, scope, etc.)")


class ContextInfo(BaseModel):
    """Context information for the current code position."""
    scope: str = Field(..., description="Current scope (module, function, class)")
    scope_path: List[str] = Field(default_factory=list, description="Scope path hierarchy")
    available_symbols: List[str] = Field(default_factory=list, description="Symbols available in current scope")
    current_line: str = Field("", description="Current line of code")


class AutocompleteResponse(BaseModel):
    """Response model for autocomplete endpoint."""
    suggestions: List[Suggestion] = Field(default_factory=list, description="List of autocomplete suggestions")
    context: Optional[ContextInfo] = Field(None, description="Context information")
    prefix: str = Field(..., description="The prefix that was completed")


class AutocompleteStreamChunk(BaseModel):
    """Streaming chunk for autocomplete suggestions."""
    text: str = Field(..., description="Suggestion text")
    type: Optional[str] = Field(None, description="Symbol type")
    score: Optional[float] = Field(None, description="Relevance score")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class AutocompleteStreamMeta(BaseModel):
    """Metadata for streaming response."""
    language: str
    prefix: str
    total_suggestions: int = 0


class IndexRequest(BaseModel):
    """Request model for indexing endpoint."""
    directory: str = Field(..., description="Directory path to index")
    languages: Optional[List[str]] = Field(None, description="Languages to index (default: all)")

