"""
Tree-sitter multi-language AST parser for code intelligence.

Uses tree-sitter-language-pack to parse Python, TypeScript, JavaScript, and more
into structured AST data for indexing into the knowledge base.

Usage:
    from Engine8_Knowledge.scripts.treesitter_parser import TreeSitterParser
    parser = TreeSitterParser()
    result = parser.parse_file("path/to/file.py")
    functions = parser.extract_functions("path/to/file.py")

Install:
    pip install tree-sitter-language-pack
"""

import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    from tree_sitter_language_pack import get_parser
    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False
    logger.warning("tree-sitter-language-pack not installed. Install with: pip install tree-sitter-language-pack")


# Map file extensions to tree-sitter language names
EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "c_sharp",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".json": "json",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
}


@dataclass
class FunctionDef:
    """Extracted function/method definition."""
    name: str
    start_line: int
    end_line: int
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)


@dataclass
class ClassDef:
    """Extracted class definition."""
    name: str
    start_line: int
    end_line: int
    bases: List[str] = field(default_factory=list)
    methods: List[FunctionDef] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class ImportDef:
    """Extracted import statement."""
    module: str
    names: List[str] = field(default_factory=list)
    is_from: bool = False
    alias: Optional[str] = None


@dataclass
class ParseResult:
    """Complete parse result for a file."""
    file_path: str
    language: str
    functions: List[FunctionDef] = field(default_factory=list)
    classes: List[ClassDef] = field(default_factory=list)
    imports: List[ImportDef] = field(default_factory=list)
    line_count: int = 0
    errors: List[str] = field(default_factory=list)


class TreeSitterParser:
    """Multi-language AST parser using tree-sitter."""

    def __init__(self):
        if not TREESITTER_AVAILABLE:
            raise ImportError("tree-sitter-language-pack is required. Install with: pip install tree-sitter-language-pack")
        self._parsers = {}

    def _get_parser(self, language: str):
        """Get or create parser for a language."""
        if language not in self._parsers:
            try:
                self._parsers[language] = get_parser(language)
            except Exception as e:
                logger.warning("treesitter_language_not_found", language=language, error=str(e))
                return None
        return self._parsers[language]

    def detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension."""
        ext = Path(file_path).suffix.lower()
        return EXTENSION_MAP.get(ext)

    def parse_file(self, file_path: str, language: str = None) -> ParseResult:
        """
        Parse a source file into structured AST data.

        Args:
            file_path: Path to source file
            language: Override language detection

        Returns:
            ParseResult with functions, classes, imports
        """
        path = Path(file_path)
        if not path.exists():
            return ParseResult(file_path=str(path), language="unknown", errors=[f"File not found: {path}"])

        lang = language or self.detect_language(str(path))
        if not lang:
            return ParseResult(file_path=str(path), language="unknown", errors=[f"Unsupported file type: {path.suffix}"])

        parser = self._get_parser(lang)
        if not parser:
            return ParseResult(file_path=str(path), language=lang, errors=[f"No parser for language: {lang}"])

        try:
            source = path.read_bytes()
            tree = parser.parse(source)
        except Exception as e:
            return ParseResult(file_path=str(path), language=lang, errors=[f"Parse error: {e}"])

        result = ParseResult(
            file_path=str(path),
            language=lang,
            line_count=source.count(b"\n") + 1,
        )

        # Extract based on language
        if lang == "python":
            self._extract_python(tree.root_node, source, result)
        elif lang in ("javascript", "typescript", "tsx"):
            self._extract_js_ts(tree.root_node, source, result)
        else:
            self._extract_generic(tree.root_node, source, result)

        return result

    def extract_functions(self, file_path: str) -> List[FunctionDef]:
        """Extract just function definitions from a file."""
        result = self.parse_file(file_path)
        return result.functions

    def extract_classes(self, file_path: str) -> List[ClassDef]:
        """Extract just class definitions from a file."""
        result = self.parse_file(file_path)
        return result.classes

    def _node_text(self, node, source: bytes) -> str:
        """Get text content of a node."""
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

    def _extract_python(self, root, source: bytes, result: ParseResult):
        """Extract Python-specific structures."""
        for node in root.children:
            if node.type == "function_definition":
                result.functions.append(self._parse_python_function(node, source))
            elif node.type == "decorated_definition":
                # Decorated function or class
                decorators = []
                inner = None
                for child in node.children:
                    if child.type == "decorator":
                        decorators.append(self._node_text(child, source).strip())
                    elif child.type == "function_definition":
                        inner = self._parse_python_function(child, source)
                        inner.decorators = decorators
                    elif child.type == "class_definition":
                        inner = self._parse_python_class(child, source)
                if inner and isinstance(inner, FunctionDef):
                    result.functions.append(inner)
                elif inner and isinstance(inner, ClassDef):
                    result.classes.append(inner)
            elif node.type == "class_definition":
                result.classes.append(self._parse_python_class(node, source))
            elif node.type in ("import_statement", "import_from_statement"):
                imp = self._parse_python_import(node, source)
                if imp:
                    result.imports.append(imp)

    def _parse_python_function(self, node, source: bytes) -> FunctionDef:
        """Parse a Python function definition node."""
        name = ""
        params = []
        return_type = None
        is_async = False
        docstring = None

        for child in node.children:
            if child.type == "identifier":
                name = self._node_text(child, source)
            elif child.type == "parameters":
                for param in child.children:
                    if param.type in ("identifier", "typed_parameter", "default_parameter", "typed_default_parameter"):
                        params.append(self._node_text(param, source))
            elif child.type == "type":
                return_type = self._node_text(child, source)
            elif child.type == "block":
                # Check for docstring
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for expr in stmt.children:
                            if expr.type == "string":
                                docstring = self._node_text(expr, source).strip("\"'")
                        break

        # Check parent for async
        if node.parent and node.parent.type == "decorated_definition":
            pass  # already handled
        text = self._node_text(node, source)
        is_async = text.startswith("async ")

        return FunctionDef(
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            parameters=params,
            return_type=return_type,
            docstring=docstring,
            is_async=is_async,
        )

    def _parse_python_class(self, node, source: bytes) -> ClassDef:
        """Parse a Python class definition node."""
        name = ""
        bases = []
        methods = []
        docstring = None

        for child in node.children:
            if child.type == "identifier":
                name = self._node_text(child, source)
            elif child.type == "argument_list":
                for arg in child.children:
                    if arg.type == "identifier":
                        bases.append(self._node_text(arg, source))
            elif child.type == "block":
                for stmt in child.children:
                    if stmt.type == "function_definition":
                        methods.append(self._parse_python_function(stmt, source))
                    elif stmt.type == "decorated_definition":
                        for sub in stmt.children:
                            if sub.type == "function_definition":
                                fn = self._parse_python_function(sub, source)
                                fn.decorators = [
                                    self._node_text(d, source).strip()
                                    for d in stmt.children if d.type == "decorator"
                                ]
                                methods.append(fn)
                    elif stmt.type == "expression_statement" and docstring is None:
                        for expr in stmt.children:
                            if expr.type == "string":
                                docstring = self._node_text(expr, source).strip("\"'")

        return ClassDef(
            name=name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            bases=bases,
            methods=methods,
            docstring=docstring,
        )

    def _parse_python_import(self, node, source: bytes) -> Optional[ImportDef]:
        """Parse a Python import statement."""
        text = self._node_text(node, source).strip()
        if text.startswith("from "):
            parts = text.split(" import ", 1)
            module = parts[0].replace("from ", "").strip()
            names = [n.strip() for n in parts[1].split(",")] if len(parts) > 1 else []
            return ImportDef(module=module, names=names, is_from=True)
        elif text.startswith("import "):
            module = text.replace("import ", "").strip()
            return ImportDef(module=module, names=[], is_from=False)
        return None

    def _extract_js_ts(self, root, source: bytes, result: ParseResult):
        """Extract JavaScript/TypeScript structures."""
        self._walk_js_ts(root, source, result)

    def _walk_js_ts(self, node, source: bytes, result: ParseResult):
        """Recursively walk JS/TS AST."""
        if node.type in ("function_declaration", "method_definition"):
            fn = FunctionDef(
                name="",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
            for child in node.children:
                if child.type in ("identifier", "property_identifier"):
                    fn.name = self._node_text(child, source)
                elif child.type == "formal_parameters":
                    fn.parameters = [
                        self._node_text(p, source) for p in child.children
                        if p.type in ("identifier", "required_parameter", "optional_parameter")
                    ]
            if fn.name:
                result.functions.append(fn)
        elif node.type == "class_declaration":
            cls = ClassDef(
                name="",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
            for child in node.children:
                if child.type == "type_identifier":
                    cls.name = self._node_text(child, source)
                elif child.type == "identifier":
                    cls.name = self._node_text(child, source)
            if cls.name:
                result.classes.append(cls)
        elif node.type in ("import_statement", "import_declaration"):
            text = self._node_text(node, source).strip()
            result.imports.append(ImportDef(module=text, is_from=True))

        for child in node.children:
            self._walk_js_ts(child, source, result)

    def _extract_generic(self, root, source: bytes, result: ParseResult):
        """Generic extraction for any language - find function-like nodes."""
        self._walk_generic(root, source, result)

    def _walk_generic(self, node, source: bytes, result: ParseResult):
        """Recursively find function/class-like nodes in any language."""
        if "function" in node.type.lower() and "definition" in node.type.lower():
            fn = FunctionDef(
                name=self._node_text(node.children[1], source) if len(node.children) > 1 else "unknown",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
            result.functions.append(fn)
        elif "class" in node.type.lower() and "definition" in node.type.lower():
            cls = ClassDef(
                name=self._node_text(node.children[1], source) if len(node.children) > 1 else "unknown",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            )
            result.classes.append(cls)

        for child in node.children:
            self._walk_generic(child, source, result)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python treesitter_parser.py <file_path>")
        sys.exit(1)

    parser = TreeSitterParser()
    result = parser.parse_file(sys.argv[1])

    print(f"File: {result.file_path}")
    print(f"Language: {result.language}")
    print(f"Lines: {result.line_count}")
    print(f"Functions: {len(result.functions)}")
    for fn in result.functions:
        async_tag = "async " if fn.is_async else ""
        print(f"  {async_tag}{fn.name}({', '.join(fn.parameters)}) L{fn.start_line}-{fn.end_line}")
    print(f"Classes: {len(result.classes)}")
    for cls in result.classes:
        print(f"  {cls.name}({', '.join(cls.bases)}) L{cls.start_line}-{cls.end_line} [{len(cls.methods)} methods]")
    print(f"Imports: {len(result.imports)}")
    for imp in result.imports:
        print(f"  {'from ' if imp.is_from else 'import '}{imp.module}")
    if result.errors:
        print(f"Errors: {result.errors}")
