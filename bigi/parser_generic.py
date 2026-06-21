"""Generic regex-based parser for language-agnostic dependency indexing in BiGI.

Extracts function definitions and calls/script references from code files of
various languages (Bash, Perl, Julia, MATLAB, Rust, Go, C/C++, JS/TS, WDL, etc.).
"""

import os
import re
from typing import Optional

LANGUAGE_SPECS = {
    "bash": {
        "extensions": [".sh", ".bash"],
        "comments": [r"#.*"],
        "definition_regexes": [
            r"(?:^|\s)function\s+([a-zA-Z_][a-zA-Z0-9_-]*)\s*(?:\(\))?\s*\{",
            r"(?:^|\s)([a-zA-Z_][a-zA-Z0-9_-]*)\s*\(\s*\)\s*\{",
        ],
        "block_type": "braces"
    },
    "perl": {
        "extensions": [".pl", ".pm"],
        "comments": [r"#.*"],
        "definition_regexes": [
            r"\bsub\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
        ],
        "block_type": "braces"
    },
    "julia": {
        "extensions": [".jl"],
        "comments": [r"#.*"],
        "definition_regexes": [
            r"\bfunction\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
        ],
        "block_type": "end"
    },
    "matlab": {
        "extensions": [".m"],
        "comments": [r"%.*"],
        "definition_regexes": [
            r"\bfunction\s+(?:\[?[a-zA-Z0-9_,\s]*\]?\s*=\s*)?([a-zA-Z_][a-zA-Z0-9_]*)\b",
        ],
        "block_type": "end"
    },
    "javascript": {
        "extensions": [".js", ".ts", ".jsx", ".tsx"],
        "comments": [r"//.*", r"/\*[\s\S]*?\*/"],
        "definition_regexes": [
            r"\bfunction\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
            r"\b(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:\([^)]*\)|[a-zA-Z_][a-zA-Z0-9_]*)\s*=>",
        ],
        "block_type": "braces"
    },
    "rust": {
        "extensions": [".rs"],
        "comments": [r"//.*", r"/\*[\s\S]*?\*/"],
        "definition_regexes": [
            r"\bfn\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
        ],
        "block_type": "braces"
    },
    "go": {
        "extensions": [".go"],
        "comments": [r"//.*", r"/\*[\s\S]*?\*/"],
        "definition_regexes": [
            r"\bfunc\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
        ],
        "block_type": "braces"
    },
    "cpp": {
        "extensions": [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"],
        "comments": [r"//.*", r"/\*[\s\S]*?\*/"],
        "definition_regexes": [
            r"\b[a-zA-Z_][a-zA-Z0-9_]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{",
        ],
        "block_type": "braces"
    }
}

DEFAULT_SPEC = {
    "comments": [r"#.*", r"//.*"],
    "definition_regexes": [
        r"\b(?:def|function|func|fn|sub)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
    ],
    "block_type": "braces"
}

KEYWORDS_TO_IGNORE = {
    "if", "for", "while", "switch", "catch", "elseif", "else", "function",
    "def", "func", "fn", "sub", "return", "import", "require", "echo", "exit"
}


def char_idx_to_pos(source: str, idx: int) -> tuple[int, int]:
    """Convert character offset to 1-based (line, col) coordinates."""
    chunk = source[:idx]
    line = chunk.count("\n") + 1
    last_nl = chunk.rfind("\n")
    if last_nl == -1:
        col = idx + 1
    else:
        col = idx - last_nl
    return line, col


def find_braces_block(source: str, start_char_idx: int) -> int:
    """Find the character index of the matching closing brace '}' starting from start_char_idx."""
    brace_count = 0
    in_double_quote = False
    in_single_quote = False
    escape = False
    
    first_brace = source.find("{", start_char_idx)
    if first_brace == -1:
        return -1
        
    idx = first_brace
    while idx < len(source):
        char = source[idx]
        if escape:
            escape = False
            idx += 1
            continue
        if char == "\\":
            escape = True
            idx += 1
            continue
            
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            
        if not in_double_quote and not in_single_quote:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count <= 0:
                    return idx
        idx += 1
    return -1


def find_end_block(source: str, start_char_idx: int) -> int:
    """Find the index of the matching 'end' keyword starting from start_char_idx."""
    lines = source[start_char_idx:].splitlines()
    block_count = 1
    char_offset = start_char_idx
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i == 0:
            openers = len(re.findall(r"\b(if|for|while|try|let|struct)\b", stripped))
        else:
            openers = len(re.findall(r"\b(function|if|for|while|try|let|struct)\b", stripped))
        closers = len(re.findall(r"\b(end)\b", stripped))
        block_count += openers - closers
        char_offset += len(line) + 1
        if block_count <= 0:
            return char_offset
    return -1


def get_language_spec(file_path: str, source: str) -> Optional[dict]:
    """Determine the language spec to use based on file extension or shebang."""
    ext = os.path.splitext(file_path)[1].lower()
    
    # Check by extension first
    for spec in LANGUAGE_SPECS.values():
        if ext in spec["extensions"]:
            return spec
            
    # Check shebang
    first_line = source.splitlines()[0] if source else ""
    if first_line.startswith("#!"):
        for name, spec in LANGUAGE_SPECS.items():
            if name in first_line:
                return spec
                
    # Fallback to default if it looks like a script/source code file
    if ext in (".sh", ".pl", ".pm", ".jl", ".m", ".js", ".ts", ".rs", ".go", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".nf", ".smk", ".wdl", ".cwl", ".rb"):
        return DEFAULT_SPEC
        
    return None


def parse_generic_file(file_path: str, base_dir: str) -> dict:
    """Parse a single source code file of any language."""
    rel_path = os.path.relpath(file_path, base_dir)
    definitions = []
    calls = []
    
    ext = os.path.splitext(file_path)[1].lower()
    supported_extensions = {
        ".sh", ".bash", ".pl", ".pm", ".jl", ".m", ".js", ".ts", ".jsx", ".tsx",
        ".rs", ".go", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".nf", ".smk",
        ".wdl", ".cwl", ".rb"
    }
    
    # Skip checking if it has a non-supported extension (files without extensions are kept for shebang check)
    if ext and ext not in supported_extensions:
        return {"definitions": [], "calls": []}
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return {"definitions": [], "calls": []}
        
    spec = get_language_spec(file_path, source)
    if not spec:
        return {"definitions": [], "calls": []}
        
    lines = source.splitlines()
    
    # Remove comments for matching (but preserve offsets by replacing comment chars with spaces)
    source_clean_list = list(source)
    for comm_pat in spec["comments"]:
        for m in re.finditer(comm_pat, source):
            start, end = m.span()
            for k in range(start, end):
                if source_clean_list[k] != "\n":
                    source_clean_list[k] = " "
    source_clean = "".join(source_clean_list)
    
    # 1. Find function definitions
    for def_pat in spec["definition_regexes"]:
        for match in re.finditer(def_pat, source_clean, re.MULTILINE):
            func_name = match.group(1)
            if func_name in KEYWORDS_TO_IGNORE:
                continue
                
            start_idx = match.start()
            end_idx = -1
            
            # Find function block boundary
            if spec["block_type"] == "braces":
                end_idx = find_braces_block(source_clean, match.end())
            elif spec["block_type"] == "end":
                end_idx = find_end_block(source_clean, match.end())
                
            if end_idx == -1:
                # Fallback: take next 50 lines or end of file
                line_num = source_clean[:start_idx].count("\n") + 1
                end_line = min(line_num + 50, len(lines))
                # compute approximate end character index
                end_idx = len("\n".join(lines[:end_line]))
                
            l1, _ = char_idx_to_pos(source, start_idx)
            l2, _ = char_idx_to_pos(source, end_idx)
            
            code_content = "\n".join(lines[l1-1:l2])
            definitions.append({
                "name": func_name,
                "file": rel_path,
                "line1": l1,
                "line2": l2,
                "code": code_content
            })
            
    # 2. Find function calls & script references
    # Pattern 1: standard parenthesized function calls
    for match in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", source_clean):
        call_name = match.group(1)
        if call_name in KEYWORDS_TO_IGNORE:
            continue
            
        l1, c1 = char_idx_to_pos(source, match.start())
        l2, c2 = char_idx_to_pos(source, match.end())
        
        # Determine caller (parent function definition wrapping this call)
        caller_name = ""
        best_span = float("inf")
        for d in definitions:
            if d["line1"] <= l1 <= d["line2"]:
                span = d["line2"] - d["line1"]
                if span < best_span:
                    best_span = span
                    caller_name = d["name"]
                    
        calls.append({
            "name": call_name,
            "file": rel_path,
            "line1": l1,
            "col1": c1,
            "line2": l2,
            "col2": c2,
            "caller": caller_name
        })
        
    # Pattern 2: Script or file references within the code (e.g. executing files or sourcing them)
    # Match any word token ending with python/r/sh/perl/julia script extension
    script_regex = r"\b([a-zA-Z0-9_\-\./]+\.(?:r|py|sh|bash|pl|pm|jl|m|rb|js|ts|rs|go|c|cpp|cc|cxx|h|hpp))\b"
    for match in re.finditer(script_regex, source_clean, re.IGNORECASE):
        script_ref = match.group(1)
        l1, c1 = char_idx_to_pos(source, match.start())
        l2, c2 = char_idx_to_pos(source, match.end())
        
        caller_name = ""
        best_span = float("inf")
        for d in definitions:
            if d["line1"] <= l1 <= d["line2"]:
                span = d["line2"] - d["line1"]
                if span < best_span:
                    best_span = span
                    caller_name = d["name"]
                    
        calls.append({
            "name": script_ref,
            "file": rel_path,
            "line1": l1,
            "col1": c1,
            "line2": l2,
            "col2": c2,
            "caller": caller_name
        })
        
    return {"definitions": definitions, "calls": calls}


def parse_generic_directory(directory_path: str) -> dict:
    """Recursively parse all code files of supported generic languages in directory_path."""
    directory_path = os.path.abspath(directory_path)
    all_defs = []
    all_calls = []
    
    exclude_dirs = {"data", "results", "output", "out", "envs", "conda", "venv", "node_modules", "build", "dist", "logs", "benchmarks", "assets"}
    
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in exclude_dirs]
        
        for f in files:
            # Skip python/R since they are parsed by higher precision specialized parsers
            if f.lower().endswith((".py", ".r", ".rscript")):
                continue
                
            file_path = os.path.join(root, f)
            res = parse_generic_file(file_path, directory_path)
            all_defs.extend(res["definitions"])
            all_calls.extend(res["calls"])
            
    return {"definitions": all_defs, "calls": all_calls}
