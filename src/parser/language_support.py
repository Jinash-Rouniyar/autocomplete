"""Language support configuration for tree-sitter parsers."""

from typing import Dict, Optional
from tree_sitter import Language, Parser

# Import language modules with error handling
try:
    import tree_sitter_python as tspython
    PYTHON_AVAILABLE = True
except ImportError:
    PYTHON_AVAILABLE = False
    tspython = None

try:
    import tree_sitter_typescript as tstypescript
    TYPESCRIPT_AVAILABLE = True
except ImportError:
    TYPESCRIPT_AVAILABLE = False
    tstypescript = None

try:
    import tree_sitter_javascript as tsjavascript
    JAVASCRIPT_AVAILABLE = True
except ImportError:
    JAVASCRIPT_AVAILABLE = False
    tsjavascript = None


class LanguageSupport:
    """Manages tree-sitter language parsers."""
    
    SUPPORTED_LANGUAGES = {}
    
    # Build supported languages dict based on available modules
    if PYTHON_AVAILABLE:
        SUPPORTED_LANGUAGES["python"] = {
            "name": "python",
            "module": tspython,
            "extensions": [".py"]
        }
    
    if TYPESCRIPT_AVAILABLE:
        SUPPORTED_LANGUAGES["typescript"] = {
            "name": "typescript",
            "module": tstypescript,
            "extensions": [".ts", ".tsx"]
        }
    
    if JAVASCRIPT_AVAILABLE:
        SUPPORTED_LANGUAGES["javascript"] = {
            "name": "javascript",
            "module": tsjavascript,
            "extensions": [".js", ".jsx"]
        }
    
    def __init__(self):
        self._parsers: Dict[str, Parser] = {}
        self._languages: Dict[str, Language] = {}
        self._initialize_languages()
    
    def _initialize_languages(self) -> None:
        """Initialize all supported language parsers."""
        for lang_key, lang_info in self.SUPPORTED_LANGUAGES.items():
            try:
                module = lang_info["module"]
                if module is None:
                    continue
                
                lang_obj = None
                
                # Handle TypeScript specially - it uses language_typescript() function
                if lang_key == "typescript":
                    if hasattr(module, 'language_typescript'):
                        try:
                            lang_obj = module.language_typescript()
                        except Exception as e:
                            print(f"Warning: Failed to call language_typescript(): {e}")
                            continue
                    else:
                        print(f"Warning: tree_sitter_typescript module missing language_typescript attribute")
                        continue
                
                # Handle JavaScript - uses language() function
                elif lang_key == "javascript":
                    if hasattr(module, 'language'):
                        try:
                            lang_obj = module.language()
                        except Exception as e:
                            print(f"Warning: Failed to call language(): {e}")
                            continue
                    else:
                        print(f"Warning: tree_sitter_javascript module missing language attribute")
                        continue
                
                # Handle Python - uses language() function
                elif lang_key == "python":
                    if hasattr(module, 'language'):
                        try:
                            lang_obj = module.language()
                        except Exception as e:
                            print(f"Warning: Failed to call language(): {e}")
                            continue
                    else:
                        print(f"Warning: tree_sitter_python module missing language attribute")
                        continue
                
                # Generic fallback for other languages
                else:
                    # Try standard patterns
                    if hasattr(module, 'language'):
                        try:
                            lang_obj = module.language()
                        except (AttributeError, TypeError):
                            pass
                    
                    if lang_obj is None and callable(module):
                        try:
                            lang_obj = module()
                        except Exception:
                            pass
                
                if lang_obj is None:
                    raise AttributeError(f"Could not find language object in {module.__name__}")
                
                # Create Language and Parser
                language = Language(lang_obj)
                parser = Parser(language)
                self._languages[lang_key] = language
                self._parsers[lang_key] = parser
                print(f"✓ Initialized {lang_key} parser")
            except Exception as e:
                print(f"Warning: Failed to initialize {lang_key} parser: {e}")
                # Continue with other languages
    
    def get_parser(self, language: str) -> Optional[Parser]:
        """Get parser for a specific language."""
        lang_key = language.lower()
        if lang_key not in self._parsers:
            # Try to find by extension
            for key, info in self.SUPPORTED_LANGUAGES.items():
                if language.lower() in info["extensions"] or language.lower() == key:
                    lang_key = key
                    break
        
        return self._parsers.get(lang_key)
    
    def get_language(self, language: str) -> Optional[Language]:
        """Get language object for a specific language."""
        lang_key = language.lower()
        return self._languages.get(lang_key)
    
    def is_supported(self, language: str) -> bool:
        """Check if a language is supported."""
        lang_key = language.lower()
        if lang_key in self.SUPPORTED_LANGUAGES:
            return True
        # Check by extension
        for info in self.SUPPORTED_LANGUAGES.values():
            if language.lower() in info["extensions"]:
                return True
        return False
    
    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file path."""
        for lang_key, info in self.SUPPORTED_LANGUAGES.items():
            for ext in info["extensions"]:
                if file_path.endswith(ext):
                    return lang_key
        return None


SUPPORTED_LANGUAGES = list(LanguageSupport.SUPPORTED_LANGUAGES.keys())

