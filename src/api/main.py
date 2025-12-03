"""FastAPI application main file."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routes import router, initialize_engine
from ..indexer.codebase_indexer import CodebaseIndexer

app = FastAPI(
    title="State-of-the-Art Autocomplete Engine",
    description="High-performance autocomplete using trie and AST analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api", tags=["autocomplete"])

# Serve static files (HTML UI)
static_dir = os.path.join(os.path.dirname(__file__), "../../static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/ui")
async def serve_ui():
    """Serve the HTML UI."""
    ui_path = os.path.join(os.path.dirname(__file__), "../../static/index.html")
    if os.path.exists(ui_path):
        return FileResponse(ui_path)
    return {"message": "UI not found. Please ensure static/index.html exists."}


@app.on_event("startup")
async def startup_event():
    """Initialize the autocomplete engine on startup."""
    # Create indexer instance
    indexer = CodebaseIndexer()
    
    # Check if there's a pre-indexed codebase
    sample_codebase_path = os.path.join(os.path.dirname(__file__), "../../data/sample_codebases")
    
    # Initialize engine
    initialize_engine(indexer)
    
    # Optionally auto-index if codebase exists
    # This can be disabled and done manually via /api/index endpoint
    # if os.path.exists(sample_codebase_path):
    #     print(f"Auto-indexing codebase at {sample_codebase_path}")
    #     indexer.index_directory(sample_codebase_path)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "State-of-the-Art Autocomplete Engine",
        "version": "1.0.0",
        "endpoints": {
            "autocomplete": "/api/autocomplete",
            "autocomplete_stream": "/api/autocomplete_stream",
            "index": "/api/index",
            "stats": "/api/stats"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

