"""Python Abstract Syntax Tree (AST) parser for BiGI.

Extracts Python function definitions (with line numbers and source code) and
function call traces from python files in a directory.
"""

import os
import ast

def parse_python_file(file_path: str, base_dir: str) -> dict:
    """Parse a single Python file to extract function definitions and calls."""
    rel_path = os.path.relpath(file_path, base_dir)
    definitions = []
    calls = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except Exception as e:
        print(f"Warning: Failed to read {file_path}: {e}")
        return {"definitions": [], "calls": []}
        
    try:
        tree = ast.parse(source, filename=file_path)
    except Exception as e:
        print(f"Warning: Failed to parse Python AST for {file_path}: {e}")
        return {"definitions": [], "calls": []}
        
    lines = source.splitlines()
    
    def get_source_slice(node):
        try:
            return "\n".join(lines[node.lineno - 1:node.end_lineno])
        except Exception:
            return ""

    class DefVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            code_content = get_source_slice(node)
            definitions.append({
                "name": node.name,
                "file": rel_path,
                "line1": node.lineno,
                "line2": node.end_lineno if hasattr(node, "end_lineno") else node.lineno,
                "code": code_content
            })
            self.generic_visit(node)
            
        visit_AsyncFunctionDef = visit_FunctionDef
            
    DefVisitor().visit(tree)

    class CallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_function = None
            
        def visit_FunctionDef(self, node):
            old_func = self.current_function
            self.current_function = node.name
            self.generic_visit(node)
            self.current_function = old_func
            
        visit_AsyncFunctionDef = visit_FunctionDef
            
        def visit_Call(self, node):
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                parts = []
                curr = node.func
                while isinstance(curr, ast.Attribute):
                    parts.append(curr.attr)
                    curr = curr.value
                if isinstance(curr, ast.Name):
                    parts.append(curr.id)
                parts.reverse()
                func_name = ".".join(parts)
            
            if func_name:
                calls.append({
                    "name": func_name,
                    "file": rel_path,
                    "line1": node.lineno,
                    "col1": node.col_offset + 1,
                    "line2": node.end_lineno if hasattr(node, "end_lineno") else node.lineno,
                    "col2": (node.end_col_offset + 1) if hasattr(node, "end_col_offset") else (node.col_offset + len(func_name) + 1),
                    "caller": self.current_function if self.current_function else ""
                })
            self.generic_visit(node)
            
    CallVisitor().visit(tree)
    
    return {"definitions": definitions, "calls": calls}

def parse_python_directory(directory_path: str) -> dict:
    """Recursively parses all Python files under directory_path, skipping non-source directories."""
    directory_path = os.path.abspath(directory_path)
    all_defs = []
    all_calls = []
    
    exclude_dirs = {"data", "results", "output", "out", "envs", "conda", "venv", "node_modules", "build", "dist", "logs", "benchmarks", "assets"}
    
    for root, dirs, files in os.walk(directory_path):
        # Exclude hidden and non-source directories in-place
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in exclude_dirs]
        
        for f in files:
            if f.endswith(".py"):
                file_path = os.path.join(root, f)
                res = parse_python_file(file_path, directory_path)
                all_defs.extend(res["definitions"])
                all_calls.extend(res["calls"])
                
    return {"definitions": all_defs, "calls": all_calls}
