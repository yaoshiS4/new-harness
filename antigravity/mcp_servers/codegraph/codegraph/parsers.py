from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

# Reserved keywords to filter out from function calls
COMMON_KEYWORDS = {
    "if", "for", "while", "switch", "catch", "import", "export", "function", "return", "typeof",
    "sizeof", "case", "default", "else", "new", "throw", "try", "finally", "with", "yield",
    "await", "match", "let", "const", "var", "print", "echo", "assert", "class", "def",
    "interface", "type", "enum", "package", "from", "as", "is", "in", "not", "and", "or",
    "super", "this", "self", "true", "false", "null", "undefined", "void", "None", "True", "False",
    "break", "continue", "pass", "lambda", "struct", "trait", "impl", "fn", "pub", "use",
    "func", "val", "fun", "object", "sealed", "open", "data", "override"
}


def _clean_sig(sig: str) -> str:
    sig = sig.strip()
    if sig.endswith("{"):
        sig = sig[:-1].strip()
    if sig.endswith(":"):
        sig = sig[:-1].strip()
    return sig[:200]


# --- Python Parser ---
class _PyVisitor(ast.NodeVisitor):
    def __init__(self, workspace: str, rel_path: str, lines: list[str]) -> None:
        self.workspace = workspace
        self.rel_path = rel_path
        self.lines = lines
        self.symbols: list[dict[str, Any]] = []
        self.edges: list[tuple[str, str, str | None, str, str, int]] = []
        self.scope_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases_str = ""
        if node.bases:
            try:
                bases_str = f"({', '.join(ast.unparse(b) for b in node.bases)})"
            except Exception:
                bases_str = "(...)"
        sig = f"class {node.name}{bases_str}"
        self.symbols.append({
            "workspace": self.workspace,
            "path": self.rel_path,
            "name": node.name,
            "kind": "class",
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "signature": sig,
            "exported": 1 if not node.name.startswith("_") else 0,
        })
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._handle_fn(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._handle_fn(node)

    def _handle_fn(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        scope = self.scope_stack[-1] if self.scope_stack else None
        kind = "method" if scope else "function"
        # Extract signature line from text if possible
        sig = f"def {node.name}(...)"
        if 1 <= node.lineno <= len(self.lines):
            line_str = self.lines[node.lineno - 1].strip()
            if line_str.startswith("def ") or line_str.startswith("async def "):
                sig = _clean_sig(line_str)
        self.symbols.append({
            "workspace": self.workspace,
            "path": self.rel_path,
            "name": node.name,
            "kind": kind,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "signature": sig,
            "exported": 1 if not node.name.startswith("_") else 0,
        })
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.edges.append((self.workspace, self.rel_path, None, "IMPORTS", alias.name, node.lineno))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        for alias in node.names:
            tgt = f"{mod}.{alias.name}" if alias.name != "*" else mod
            self.edges.append((self.workspace, self.rel_path, None, "IMPORTS", tgt, node.lineno))

    def visit_Call(self, node: ast.Call) -> None:
        scope = self.scope_stack[-1] if self.scope_stack else None
        if isinstance(node.func, ast.Name):
            if node.func.id not in COMMON_KEYWORDS:
                self.edges.append((self.workspace, self.rel_path, scope, "CALLS", node.func.id, node.lineno))
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr not in COMMON_KEYWORDS:
                self.edges.append((self.workspace, self.rel_path, scope, "CALLS", node.func.attr, node.lineno))
        self.generic_visit(node)


def _parse_python(text: str, workspace: str, rel_path: str) -> tuple[list[dict[str, Any]], list[tuple[str, str, str | None, str, str, int]]]:
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _parse_generic_regex(text, workspace, rel_path)
    visitor = _PyVisitor(workspace, rel_path, lines)
    visitor.visit(tree)
    return visitor.symbols, visitor.edges


# --- TypeScript / JavaScript Parser ---
TS_TYPE_RE = re.compile(r"(?:^|;)\s*(export\s+)?(interface|type|enum)\s+([A-Za-z_$][\w$]*)", re.M)
TS_CLASS_RE = re.compile(r"(?:^|;)\s*(export\s+(?:default\s+)?)?class\s+([A-Za-z_$][\w$]*)", re.M)
TS_FN_RE = re.compile(r"(?:^|;)\s*(export\s+(?:default\s+)?)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", re.M)
TS_CONST_FN_RE = re.compile(
    r"(?:^|;)\s*(export\s+)?(?:const|let)\s+([A-Za-z_$][\w$]*)(?:\s*:\s*[^=]+)?\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>",
    re.M,
)
TS_IMPORT_RE = re.compile(r"""(?:import\s+(?:\{([^}]+)\}|\*\s+as\s+(\w+)|([A-Za-z_$][\w$]*))\s+from\s+['"]([^'"]+)['"]|import\s+['"]([^'"]+)['"]|require\(['"]([^'"]+)['"]\))""")
CALL_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")


def _parse_typescript_javascript(text: str, workspace: str, rel_path: str) -> tuple[list[dict[str, Any]], list[tuple[str, str, str | None, str, str, int]]]:
    symbols: list[dict[str, Any]] = []
    edges: list[tuple[str, str, str | None, str, str, int]] = []
    lines = text.splitlines()

    # Extract symbols
    for match in TS_CLASS_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        exported = 1 if match.group(1) else 0
        name = match.group(2)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"class {name}"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": "class", "line": line_no, "end_line": line_no,
            "signature": sig, "exported": exported
        })

    for match in TS_TYPE_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        exported = 1 if match.group(1) else 0
        kind = match.group(2)
        name = match.group(3)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"{kind} {name}"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": kind, "line": line_no, "end_line": line_no,
            "signature": sig, "exported": exported
        })

    for match in TS_FN_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        exported = 1 if match.group(1) else 0
        name = match.group(2)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"function {name}(...)"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": "function", "line": line_no, "end_line": line_no,
            "signature": sig, "exported": exported
        })

    for match in TS_CONST_FN_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        exported = 1 if match.group(1) else 0
        name = match.group(2)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"const {name} = (...) =>"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": "function", "line": line_no, "end_line": line_no,
            "signature": sig, "exported": exported
        })

    # Sort symbols by line
    symbols.sort(key=lambda s: s["line"])

    # Extract imports and calls line-by-line
    current_sym: str | None = None
    sym_idx = 0
    for idx, line in enumerate(lines, 1):
        # Update current enclosing symbol
        while sym_idx < len(symbols) and symbols[sym_idx]["line"] <= idx:
            current_sym = symbols[sym_idx]["name"]
            sym_idx += 1

        # Check imports
        for imp in TS_IMPORT_RE.finditer(line):
            named, star, def_name, src1, src2, src3 = imp.groups()
            mod = src1 or src2 or src3
            if mod:
                edges.append((workspace, rel_path, None, "IMPORTS", mod, idx))
                if named:
                    for s in named.split(","):
                        clean_s = s.strip().split(" as ")[0].strip()
                        if clean_s:
                            edges.append((workspace, rel_path, None, "IMPORTS", f"{mod}.{clean_s}", idx))
                if def_name:
                    edges.append((workspace, rel_path, None, "IMPORTS", f"{mod}.{def_name}", idx))
                if star:
                    edges.append((workspace, rel_path, None, "IMPORTS", f"{mod}.*", idx))

        # Check function calls
        for call_m in CALL_RE.finditer(line):
            c_name = call_m.group(1)
            if c_name not in COMMON_KEYWORDS and len(c_name) > 1:
                edges.append((workspace, rel_path, current_sym, "CALLS", c_name, idx))

    return symbols, edges


# --- Kotlin Parser ---
KT_CLASS_RE = re.compile(r"^\s*(?:(?:public|private|internal|protected|open|abstract|sealed|data)\s+)*(class|interface|object|enum\s+class)\s+([A-Za-z_][\w]*)", re.M)
KT_FUN_RE = re.compile(r"^\s*(?:(?:public|private|internal|protected|suspend|override|inline)\s+)*fun\s+(?:<[^>]+>\s*)?([A-Za-z_][\w]*)\s*(\([^\)]*\))?", re.M)
KT_IMPORT_RE = re.compile(r"^\s*import\s+([\w.]+)", re.M)


def _parse_kotlin(text: str, workspace: str, rel_path: str) -> tuple[list[dict[str, Any]], list[tuple[str, str, str | None, str, str, int]]]:
    symbols: list[dict[str, Any]] = []
    edges: list[tuple[str, str, str | None, str, str, int]] = []
    lines = text.splitlines()

    for match in KT_CLASS_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        kind = match.group(1).split()[-1]
        name = match.group(2)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"{kind} {name}"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": kind, "line": line_no, "end_line": line_no,
            "signature": sig, "exported": 1
        })

    for match in KT_FUN_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        name = match.group(1)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"fun {name}(...)"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": "function", "line": line_no, "end_line": line_no,
            "signature": sig, "exported": 1
        })

    for match in KT_IMPORT_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        edges.append((workspace, rel_path, None, "IMPORTS", match.group(1), line_no))

    for idx, line in enumerate(lines, 1):
        for call_m in CALL_RE.finditer(line):
            c_name = call_m.group(1)
            if c_name not in COMMON_KEYWORDS and len(c_name) > 1:
                edges.append((workspace, rel_path, None, "CALLS", c_name, idx))

    return symbols, edges


# --- Go Parser ---
GO_FUNC_RE = re.compile(r"^\s*func\s+(?:\([^\)]+\)\s+)?([A-Za-z_][\w]*)\s*(\([^\)]*\))?", re.M)
GO_TYPE_RE = re.compile(r"^\s*type\s+([A-Za-z_][\w]*)\s+(struct|interface|\w+)", re.M)
GO_IMPORT_RE = re.compile(r"""import\s+(?:\(\s*([^)]+)\s*\)|['"]([^'"]+)['"])""")


def _parse_go(text: str, workspace: str, rel_path: str) -> tuple[list[dict[str, Any]], list[tuple[str, str, str | None, str, str, int]]]:
    symbols: list[dict[str, Any]] = []
    edges: list[tuple[str, str, str | None, str, str, int]] = []
    lines = text.splitlines()

    for match in GO_TYPE_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        name = match.group(1)
        kind = match.group(2)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"type {name} {kind}"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": "type", "line": line_no, "end_line": line_no,
            "signature": sig, "exported": 1 if name[0].isupper() else 0
        })

    for match in GO_FUNC_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        name = match.group(1)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"func {name}(...)"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": "function", "line": line_no, "end_line": line_no,
            "signature": sig, "exported": 1 if name[0].isupper() else 0
        })

    for idx, line in enumerate(lines, 1):
        m_imp = re.search(r'import\s+["\']([^"\']+)["\']', line)
        if m_imp:
            edges.append((workspace, rel_path, None, "IMPORTS", m_imp.group(1), idx))
        for call_m in CALL_RE.finditer(line):
            c_name = call_m.group(1)
            if c_name not in COMMON_KEYWORDS and len(c_name) > 1:
                edges.append((workspace, rel_path, None, "CALLS", c_name, idx))

    return symbols, edges


# --- Rust Parser ---
RS_FN_RE = re.compile(r"^\s*(pub(?:\([^\)]+\))?\s+)?(?:async\s+)?fn\s+([A-Za-z_][\w]*)\s*(?:<[^>]+>)?\s*(\([^\)]*\))?", re.M)
RS_STRUCT_RE = re.compile(r"^\s*(pub(?:\([^\)]+\))?\s+)?(struct|enum|trait)\s+([A-Za-z_][\w]*)", re.M)
RS_USE_RE = re.compile(r"^\s*use\s+([^;]+);", re.M)


def _parse_rust(text: str, workspace: str, rel_path: str) -> tuple[list[dict[str, Any]], list[tuple[str, str, str | None, str, str, int]]]:
    symbols: list[dict[str, Any]] = []
    edges: list[tuple[str, str, str | None, str, str, int]] = []
    lines = text.splitlines()

    for match in RS_STRUCT_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        exported = 1 if match.group(1) else 0
        kind = match.group(2)
        name = match.group(3)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"{kind} {name}"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": kind, "line": line_no, "end_line": line_no,
            "signature": sig, "exported": exported
        })

    for match in RS_FN_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        exported = 1 if match.group(1) else 0
        name = match.group(2)
        sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else f"fn {name}(...)"
        symbols.append({
            "workspace": workspace, "path": rel_path, "name": name,
            "kind": "function", "line": line_no, "end_line": line_no,
            "signature": sig, "exported": exported
        })

    for match in RS_USE_RE.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        edges.append((workspace, rel_path, None, "IMPORTS", match.group(1).strip(), line_no))

    for idx, line in enumerate(lines, 1):
        for call_m in CALL_RE.finditer(line):
            c_name = call_m.group(1)
            if c_name not in COMMON_KEYWORDS and len(c_name) > 1:
                edges.append((workspace, rel_path, None, "CALLS", c_name, idx))

    return symbols, edges


# --- Markdown & Generic Parser ---
def _parse_markdown(text: str, workspace: str, rel_path: str) -> tuple[list[dict[str, Any]], list[tuple[str, str, str | None, str, str, int]]]:
    symbols: list[dict[str, Any]] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, 1):
        m = re.match(r"^\s*(#+)\s+(.+)$", line)
        if m:
            heading = m.group(2).strip()
            symbols.append({
                "workspace": workspace, "path": rel_path, "name": heading,
                "kind": "heading", "line": idx, "end_line": idx,
                "signature": f"{m.group(1)} {heading}", "exported": 1
            })
    return symbols, []


def _parse_generic_regex(text: str, workspace: str, rel_path: str) -> tuple[list[dict[str, Any]], list[tuple[str, str, str | None, str, str, int]]]:
    symbols: list[dict[str, Any]] = []
    edges: list[tuple[str, str, str | None, str, str, int]] = []
    patterns = [
        (r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", "function"),
        (r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)", "class"),
        (r"^\s*(?:export\s+)?(?:interface|type|enum)\s+([A-Za-z_$][\w$]*)", "type"),
        (r"^\s*(?:def|fun|fn)\s+([A-Za-z_$][\w$]*)", "function"),
        (r"^\s*#+\s+(.+)$", "heading"),
    ]
    lines = text.splitlines()
    for pattern, kind in patterns:
        for match in re.finditer(pattern, text, flags=re.M):
            name = match.group(1).strip()
            line_no = text.count("\n", 0, match.start()) + 1
            sig = _clean_sig(lines[line_no - 1]) if line_no <= len(lines) else name
            symbols.append({
                "workspace": workspace, "path": rel_path, "name": name,
                "kind": kind, "line": line_no, "end_line": line_no,
                "signature": sig, "exported": 1
            })
    return symbols, edges


def parse_file(file_path: Path, workspace: str, rel_path: str) -> tuple[list[dict[str, Any]], list[tuple[str, str, str | None, str, str, int]]]:
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return [], []

    suffix = file_path.suffix.lower()
    if suffix == ".py":
        return _parse_python(text, workspace, rel_path)
    elif suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
        return _parse_typescript_javascript(text, workspace, rel_path)
    elif suffix in {".kt", ".kts"}:
        return _parse_kotlin(text, workspace, rel_path)
    elif suffix == ".go":
        return _parse_go(text, workspace, rel_path)
    elif suffix == ".rs":
        return _parse_rust(text, workspace, rel_path)
    elif suffix == ".md":
        return _parse_markdown(text, workspace, rel_path)
    else:
        return _parse_generic_regex(text, workspace, rel_path)
