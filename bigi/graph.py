"""Graph construction, serialization, and impact tracing for BiGI.

This module is responsible for:
- Parsing the Snakemake pipeline and R code into a unified dependency graph.
- Saving/loading the graph index to/from disk.
- Tracing downstream impact from a given rule or R function.
"""

import os
import json
import subprocess
import re
from typing import Optional

from .parser_pipeline import parse_pipeline
from .parser_nextflow import parse_nextflow_pipeline
from .parser_python import parse_python_directory
from .parser_generic import parse_generic_directory
from .constants import R_BUILTINS


# ---------------------------------------------------------------------------
# Path / wildcard helpers
# ---------------------------------------------------------------------------

def normalize_wildcards(path: str) -> str:
    """Replace all ``{wildcard_name}`` placeholders with the literal ``{WILDCARD}``."""
    return re.sub(r"\{[a-zA-Z0-9_]+\}", "{WILDCARD}", path)


def wildcard_to_regex(path: str) -> re.Pattern:
    """Compile a Snakemake wildcard path pattern into a regex that matches concrete paths."""
    escaped = re.escape(path)
    regex_str = re.sub(r"\\\{[a-zA-Z0-9_]+\\\}", r"([^/]+)", escaped)
    return re.compile("^" + regex_str + "$")


def check_match(input_path: str, output_path: str) -> tuple[bool, Optional[str]]:
    """Return ``(matched, confidence)`` for an input/output path pair.

    Handles exact matches, wildcard-normalized matches, and one-sided wildcard
    expansion.  Returns ``(False, None)`` when no match is found.
    """
    if input_path == output_path:
        return True, "HIGH"
    norm_in = normalize_wildcards(input_path)
    norm_out = normalize_wildcards(output_path)
    if norm_in == norm_out:
        return True, "HIGH"
    if "{" in output_path and "{" not in input_path:
        if wildcard_to_regex(output_path).match(input_path):
            return True, "HIGH"
    if "{" in input_path and "{" not in output_path:
        if wildcard_to_regex(input_path).match(output_path):
            return True, "HIGH"
    return False, None


# ---------------------------------------------------------------------------
# Graph-node helper
# ---------------------------------------------------------------------------

def _add_node(nodes: dict, node_id: str, **kwargs) -> None:
    """Insert *node_id* with *kwargs* into *nodes* if not already present."""
    if node_id not in nodes:
        nodes[node_id] = {"id": node_id, **kwargs}


# ---------------------------------------------------------------------------
# DFS traversal helpers (used by trace_impact)
# ---------------------------------------------------------------------------

def _dfs_downstream(
    current_id: str,
    depth: int,
    visited: set[str],
    nodes: dict,
    adj: dict[str, list],
    results: list[str],
) -> None:
    """Recursively collect downstream-impact lines from *current_id*."""
    for tgt_id, conf, _etype, detail in sorted(
        adj.get(current_id, []),
        key=lambda x: (nodes.get(x[0], {}).get("type", ""), nodes.get(x[0], {}).get("name", "")),
    ):
        tgt = nodes.get(tgt_id)
        if not tgt:
            continue

        indent = "  " * depth
        if tgt["type"] == "rule":
            desc = f"rule: {tgt['name']}"
        elif tgt["type"] == "unresolved":
            desc = f"function: {tgt['name']} (UNRESOLVED definition)"
        else:
            desc = f"function: {tgt['name']} (in {tgt['file']})"

        conf_str = f"Confidence: {conf}"
        if detail:
            conf_str += f" - {detail}"
        results.append(f"{indent}[Depth {depth}] {desc} ({conf_str})")

        if tgt_id in visited:
            results.append(f"{indent}  [Circular dependency, already visited: {tgt_id}]")
            continue

        visited.add(tgt_id)
        _dfs_downstream(tgt_id, depth + 1, visited, nodes, adj, results)


def _dfs_upstream_r(
    current_id: str,
    depth: int,
    visited: set[str],
    nodes: dict,
    rev_adj: dict[str, list],
    results: list[str],
) -> None:
    """Recursively collect R function nodes that feed into *current_id* via ``r_call`` edges."""
    r_upstream = [u for u in rev_adj.get(current_id, []) if u[2] == "r_call"]
    for src_id, conf, _etype, detail in sorted(
        r_upstream,
        key=lambda x: (nodes.get(x[0], {}).get("type", ""), nodes.get(x[0], {}).get("name", "")),
    ):
        src = nodes.get(src_id)
        if not src:
            continue

        indent = "  " * depth
        if src["type"] == "unresolved":
            desc = f"function: {src['name']} (UNRESOLVED definition)"
        else:
            desc = f"function: {src['name']} (in {src['file']})"

        conf_str = f"Confidence: {conf}"
        if detail:
            conf_str += f" - {detail}"
        results.append(f"{indent}[Depth {depth}] {desc} ({conf_str})")

        if src_id in visited:
            results.append(f"{indent}  [Circular dependency, already visited: {src_id}]")
            continue

        visited.add(src_id)
        _dfs_upstream_r(src_id, depth + 1, visited, nodes, rev_adj, results)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_graph(pipeline_dir: str) -> dict:
    """Build a unified dependency graph for the pipeline rooted at *pipeline_dir*.

    Returns a dict with:
    - ``nodes``: mapping of node_id → node attribute dict
    - ``edges``: list of edge dicts (source, target, type, confidence, …)
    """
    pipeline_dir = os.path.abspath(pipeline_dir)
    
    # 1. Parse rules from Snakemake and processes from Nextflow
    rules = parse_pipeline(pipeline_dir)
    nf_processes = parse_nextflow_pipeline(pipeline_dir)
    
    # Integrate Nextflow processes as rule-equivalent nodes
    for name, proc in nf_processes.items():
        rules[f"nf:{name}"] = {
            "name": f"nf:{name}",
            "file": proc["file"],
            "input": proc["input"],
            "output": proc["output"],
            "r_script": proc.get("r_script"),
            "py_script": proc.get("py_script"),
            "script": proc.get("r_script") or proc.get("py_script"),
            "shell": proc.get("raw_script")
        }

    # 2. Parse R scripts (definitions and calls)
    parser_r_path = os.path.join(os.path.dirname(__file__), "parser_r.R")
    r_data: dict = {"definitions": [], "calls": []}
    
    # Fast Python-based directory walk for R scripts with folder pruning
    r_files = []
    exclude_dirs = {"data", "results", "output", "out", "envs", "conda", "venv", "node_modules", "build", "dist", "logs", "benchmarks", "assets"}
    for root, dirs, files in os.walk(pipeline_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in exclude_dirs]
        for f in files:
            if f.lower().endswith((".r", ".rscript")):
                r_files.append(os.path.join(root, f))
                
    if r_files:
        import tempfile
        temp_json_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as tf:
                json.dump(r_files, tf)
                temp_json_path = tf.name
        except Exception as exc:
            print(f"Warning: Could not create temporary JSON file for R script list: {exc}")
            
        if temp_json_path:
            try:
                result = subprocess.run(
                    ["Rscript", parser_r_path, temp_json_path, pipeline_dir],
                    capture_output=True, text=True, check=True,
                )
                r_data = json.loads(result.stdout)
            except subprocess.CalledProcessError as exc:
                print(f"Warning: R parsing failed: {exc.stderr}")
            except Exception as exc:
                print(f"Warning: Could not parse R files: {exc}")
            finally:
                try:
                    os.remove(temp_json_path)
                except Exception:
                    pass

    # 3. Parse Python scripts (definitions and calls)
    py_data: dict = {"definitions": [], "calls": []}
    try:
        py_data = parse_python_directory(pipeline_dir)
    except Exception as exc:
        print(f"Warning: Could not parse Python files: {exc}")

    # 4. Parse other script files (Bash, Perl, Julia, MATLAB, Rust, Go, JS/TS, C/C++, etc.)
    generic_data: dict = {"definitions": [], "calls": []}
    try:
        generic_data = parse_generic_directory(pipeline_dir)
    except Exception as exc:
        print(f"Warning: Could not parse generic files: {exc}")

    # Merge definitions and calls from R, Python, and other languages
    merged_definitions = r_data["definitions"] + py_data["definitions"] + generic_data["definitions"]
    merged_calls = r_data["calls"] + py_data["calls"] + generic_data["calls"]

    nodes: dict = {}
    edges: list[dict] = []

    # --- Nodes ---
    for name, r in rules.items():
        node_type = "rule"
        display_name = name
        if name.startswith("nf:"):
            display_name = name.split(":", 1)[1]
        _add_node(nodes, f"rule:{name}", type="rule", name=display_name,
                  file=r["file"], inputs=r["input"], outputs=r["output"])

    for d in merged_definitions:
        code_content = ""
        full_file_path = os.path.join(pipeline_dir, d["file"])
        if os.path.exists(full_file_path):
            try:
                with open(full_file_path, "r", encoding="utf-8") as rf:
                    lines = rf.readlines()
                    l1, l2 = d["line1"], d["line2"]
                    if 1 <= l1 <= len(lines) and 1 <= l2 <= len(lines):
                        code_content = "".join(lines[l1-1:l2])
            except Exception as ex:
                code_content = f"Error reading code: {ex}"

        _add_node(nodes, f"function:{d['name']}@{d['file']}",
                  type="function", name=d["name"], file=d["file"],
                  line_range=[d["line1"], d["line2"]], code=code_content)

    defs_by_name: dict[str, list] = {}
    for d in merged_definitions:
        defs_by_name.setdefault(d["name"], []).append(d)

    # --- Rule → Rule edges (pipeline layer) ---
    for name_b, rule_b in rules.items():
        id_b = f"rule:{name_b}"
        for inp in rule_b["input"]:
            matched_rules = [
                name_a for name_a, rule_a in rules.items()
                if name_a != name_b
                and any(check_match(inp, out)[0] for out in rule_a["output"])
            ]
            if matched_rules:
                confidence = "HIGH" if len(matched_rules) == 1 else "AMBIGUOUS"
                for name_a in matched_rules:
                    edges.append({
                        "source": f"rule:{name_a}",
                        "target": id_b,
                        "type": "pipeline_dep",
                        "confidence": confidence,
                        "detail": "Input matched output",
                        "label": os.path.basename(inp),
                    })

    # --- Script call edges (cross-layer) ---
    script_to_rules: dict[str, list[str]] = {}
    for name, r in rules.items():
        scripts = []
        if r.get("r_script"):
            scripts.append(r["r_script"])
        if r.get("py_script"):
            scripts.append(r["py_script"])
        if r.get("script") and r["script"] not in scripts:
            scripts.append(r["script"])
            
        if r.get("shell"):
            shell_scripts = re.findall(
                r"\b([a-zA-Z0-9_\-\./]+\.(?:r|py|sh|bash|pl|pm|jl|m|rb|js|ts|rs|go|c|cpp|cc|cxx|h|hpp))\b",
                r["shell"],
                re.IGNORECASE
            )
            for s in shell_scripts:
                if s not in scripts:
                    scripts.append(s)

        for script in scripts:
            script_to_rules.setdefault(os.path.normpath(script), []).append(name)

    for c in merged_calls:
        call_name: str = c["name"]
        if call_name in R_BUILTINS:
            continue

        file_path: str = c["file"]
        caller_name: Optional[str] = c["caller"]

        if not caller_name:  # global scope — attribute to rules that run this script
            caller_ids = [
                f"rule:{r}"
                for r in script_to_rules.get(os.path.normpath(file_path), [])
            ]
        else:
            caller_ids = [f"function:{caller_name}@{file_path}"]

        if not caller_ids:
            continue

        target_defs = defs_by_name.get(call_name, [])
        if not target_defs and "::" in call_name:
            target_defs = defs_by_name.get(call_name.split("::")[-1], [])
        if not target_defs and "." in call_name:
            target_defs = defs_by_name.get(call_name.split(".")[-1], [])

        if len(target_defs) == 1:
            d = target_defs[0]
            target_id = f"function:{d['name']}@{d['file']}"
            for cid in caller_ids:
                is_rule = cid.startswith("rule:")
                label = f"{'executed' if is_rule else 'called'} on L{c.get('line1', '?')}"
                detail = f"Invoked at line {c.get('line1', '?')} in {c['file']}"
                edges.append({"source": target_id, "target": cid,
                               "type": "r_call", "confidence": "HIGH", "label": label, "detail": detail})
        elif len(target_defs) > 1:
            for d in target_defs:
                target_id = f"function:{d['name']}@{d['file']}"
                for cid in caller_ids:
                    is_rule = cid.startswith("rule:")
                    label = f"{'executed' if is_rule else 'called'} on L{c.get('line1', '?')}"
                    detail = f"Multiple definitions exist for '{call_name}'. One is invoked at line {c.get('line1', '?')} in {c['file']}."
                    edges.append({"source": target_id, "target": cid,
                                   "type": "r_call", "confidence": "AMBIGUOUS",
                                   "detail": detail,
                                   "label": label})
        else:
            unresolved_id = f"function:{call_name}@UNRESOLVED"
            _add_node(nodes, unresolved_id, type="unresolved", name=call_name, file="UNRESOLVED")
            for cid in caller_ids:
                is_rule = cid.startswith("rule:")
                label = f"{'executed' if is_rule else 'called'} on L{c.get('line1', '?')}"
                detail = f"Missing definition for '{call_name}', which is invoked at line {c.get('line1', '?')} in {c['file']}."
                edges.append({"source": unresolved_id, "target": cid,
                               "type": "r_call", "confidence": "UNRESOLVED", "label": label, "detail": detail})

    # Extract Git modified status to flag modified nodes in the visualization
    modified_files = set()
    try:
        if os.environ.get("GITHUB_BASE_REF"):
            # In a GitHub PR, compare against the base branch
            base_ref = os.environ.get("GITHUB_BASE_REF")
            res_git = subprocess.run(
                ["git", "diff", "--name-only", f"origin/{base_ref}"],
                cwd=pipeline_dir,
                capture_output=True, text=True, check=True
            )
            for line in res_git.stdout.splitlines():
                if line.strip():
                    modified_files.add(os.path.normpath(line.strip()))
        else:
            # Local working directory: check uncommitted changes
            res_git = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=pipeline_dir,
                capture_output=True, text=True, check=True
            )
            for line in res_git.stdout.splitlines():
                if len(line) > 3:
                    fpath = line[3:].strip()
                    if " -> " in fpath:
                        fpath = fpath.split(" -> ")[-1]
                    modified_files.add(os.path.normpath(fpath))
    except Exception:
        pass

    if modified_files:
        for node in nodes.values():
            if node.get("file") and os.path.normpath(node["file"]) in modified_files:
                node["git_modified"] = True

    return {"nodes": nodes, "edges": edges, "pipeline_dir": pipeline_dir}


def save_index(graph: dict, pipeline_dir: str) -> str:
    """Serialize *graph* to ``<pipeline_dir>/.bigi_index.json`` and return the path."""
    index_path = os.path.join(pipeline_dir, ".bigi_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    return index_path


def load_index(pipeline_dir: str) -> Optional[dict]:
    """Load and return the graph index from *pipeline_dir*, or ``None`` if absent."""
    index_path = os.path.join(pipeline_dir, ".bigi_index.json")
    if not os.path.exists(index_path):
        return None
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def trace_impact(graph: dict, name: str) -> Optional[list[str]]:
    """Return a list of human-readable lines describing the downstream impact of *name*.

    *name* may be a Snakemake rule name or an R function name.  Returns ``None``
    when *name* is not found in the index.
    """
    nodes = graph["nodes"]
    edges = graph["edges"]

    start_nodes = []
    rule_id = f"rule:{name}"
    if rule_id in nodes:
        start_nodes.append(nodes[rule_id])

    func_prefix = f"function:{name}@"
    for node_id, node in nodes.items():
        if node_id.startswith(func_prefix):
            start_nodes.append(node)

    if not start_nodes:
        return None

    # Build adjacency lists
    adj: dict[str, list] = {}
    rev_adj: dict[str, list] = {}
    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        adj.setdefault(src, []).append((tgt, edge["confidence"], edge.get("type"), edge.get("detail")))
        rev_adj.setdefault(tgt, []).append((src, edge["confidence"], edge.get("type"), edge.get("detail")))

    results: list[str] = []

    for start_node in start_nodes:
        start_desc = f"{start_node['type']}: {start_node['name']}"
        if start_node.get("file") and start_node["file"] != "UNRESOLVED":
            if start_node["type"] == "function":
                start_desc += f" (in {start_node['file']}, lines {start_node['line_range'][0]}-{start_node['line_range'][1]})"
            else:
                start_desc += f" (in {start_node['file']})"
        results.append(f"Symbol: {start_desc}")

        results.append("Downstream Impact (what breaks if changed):")
        visited_down: set[str] = {start_node["id"]}
        before = len(results)
        _dfs_downstream(start_node["id"], 1, visited_down, nodes, adj, results)
        if len(results) == before:
            results.append("  (No downstream impact found)")

        if start_node["type"] == "rule":
            results.append("R Functions Touched by Script (direct and transitive calls):")
            visited_up: set[str] = {start_node["id"]}
            before = len(results)
            _dfs_upstream_r(start_node["id"], 1, visited_up, nodes, rev_adj, results)
            if len(results) == before:
                results.append("  (No R functions touched)")

        results.append("")

    return results
