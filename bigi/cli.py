"""Command-line interface for BiGI.

Entry point: ``bigi`` (installed via ``console_scripts`` in pyproject.toml).

Sub-commands:
- ``analyze <pipeline_dir>`` — index a pipeline directory.
- ``impact <symbol>``        — trace downstream impact of a rule or R function.
"""

import copy
import json
import os
import sys
import argparse
import tempfile
import subprocess
import urllib.request
import zipfile
from typing import Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .graph import build_graph, save_index, load_index, trace_impact
from .html_template import HTML_TEMPLATE


def export_html(graph_data: dict, output_path: str, selected_node_id: Optional[str] = None) -> None:
    """Write an interactive HTML visualization of *graph_data* to *output_path*.

    If *selected_node_id* is given, that node is pre-highlighted in the UI.
    """
    data = copy.deepcopy(graph_data)
    data["selected_node_id"] = selected_node_id

    html_content = HTML_TEMPLATE.replace(
        "const graphData = // __DATA__;",
        f"const graphData = {json.dumps(data, indent=2)};",
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def export_graphml(graph_data: dict, output_path: str) -> None:
    """Export the graph to GraphML format."""
    root = ET.Element("graphml", xmlns="http://graphml.graphdrawing.org/xmlns")
    
    # Define keys for node attributes
    for key_id, key_type in [("type", "string"), ("name", "string"), ("file", "string")]:
        ET.SubElement(root, "key", id=key_id, **{"for": "node", "attr.name": key_id, "attr.type": key_type})
        
    # Define keys for edge attributes
    for key_id, key_type in [("type", "string"), ("confidence", "string"), ("label", "string")]:
        ET.SubElement(root, "key", id=f"e_{key_id}", **{"for": "edge", "attr.name": key_id, "attr.type": key_type})
        
    graph_elem = ET.SubElement(root, "graph", id="G", edgedefault="directed")
    
    for node_id, node in graph_data.get("nodes", {}).items():
        n = ET.SubElement(graph_elem, "node", id=node_id)
        ET.SubElement(n, "data", key="type").text = node.get("type", "")
        ET.SubElement(n, "data", key="name").text = node.get("name", "")
        if "file" in node:
            ET.SubElement(n, "data", key="file").text = node.get("file", "")
            
    for i, edge in enumerate(graph_data.get("edges", [])):
        e = ET.SubElement(graph_elem, "edge", id=f"e{i}", source=edge["source"], target=edge["target"])
        ET.SubElement(e, "data", key="e_type").text = edge.get("type", "")
        ET.SubElement(e, "data", key="e_confidence").text = edge.get("confidence", "")
        if "label" in edge:
            ET.SubElement(e, "data", key="e_label").text = edge.get("label", "")
            
    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xmlstr)


def _cmd_analyze(args: argparse.Namespace) -> int:
    """Execute the ``analyze`` sub-command. Returns an exit code."""
    pipeline_dir: str = args.pipeline_dir
    is_url = pipeline_dir.startswith(("http://", "https://", "git@", "git://"))
    temp_dir_obj = None

    if is_url:
        print(f"Detected remote URL: {pipeline_dir}")
        temp_dir_obj = tempfile.TemporaryDirectory()
        target_dir = temp_dir_obj.name

        try:
            if pipeline_dir.endswith(".zip"):
                print(f"Downloading zip archive from {pipeline_dir}...")
                zip_path = os.path.join(target_dir, "archive.zip")
                urllib.request.urlretrieve(pipeline_dir, zip_path)
                print("Extracting archive...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)

                # Check if single folder nested inside zip
                contents = os.listdir(target_dir)
                if len(contents) == 1 and os.path.isdir(os.path.join(target_dir, contents[0])):
                    target_dir = os.path.join(target_dir, contents[0])
            else:
                clone_url = pipeline_dir
                if "github.com" in clone_url and "/tree/" in clone_url:
                    parts = clone_url.split("/tree/")
                    clone_url = parts[0] + ".git"
                    print(f"Translating GitHub branch URL to repository clone URL: {clone_url}")

                print(f"Cloning git repository {clone_url}...")
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", clone_url, target_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode != 0:
                    print(f"Error cloning repository: {result.stderr}", file=sys.stderr)
                    temp_dir_obj.cleanup()
                    return 1

            pipeline_dir = target_dir
        except Exception as e:
            print(f"Error fetching remote URL: {e}", file=sys.stderr)
            if temp_dir_obj:
                temp_dir_obj.cleanup()
            return 1
    else:
        if not os.path.exists(pipeline_dir):
            print(f"Error: Pipeline directory '{pipeline_dir}' does not exist.", file=sys.stderr)
            return 1

    print(f"Analyzing genomics pipeline at '{pipeline_dir}'...")
    graph = build_graph(pipeline_dir)

    # Save index in current directory if remote URL was indexed
    index_dir = os.getcwd() if is_url else pipeline_dir
    index_path = save_index(graph, index_dir)
    print(f"Analysis complete. Index saved to '{index_path}'.")
    print(f"Indexed {len(graph['nodes'])} nodes and {len(graph['edges'])} edges.")

    if args.html:
        export_html(graph, args.html)
        print(f"Interactive graph visualization exported to '{args.html}'.")

    if temp_dir_obj:
        temp_dir_obj.cleanup()

    return 0


def _cmd_impact(args: argparse.Namespace) -> int:
    """Execute the ``impact`` sub-command. Returns an exit code."""
    pipeline_dir: str = args.pipeline_dir
    symbol: str = args.symbol_or_rule_name

    graph = load_index(pipeline_dir)
    if graph is None:
        index_path = os.path.join(pipeline_dir, ".bigi_index.json")
        print(f"Error: Index not found at '{index_path}'.", file=sys.stderr)
        print("Please run 'bigi analyze <pipeline_dir>' first to build the index.", file=sys.stderr)
        return 1

    results = trace_impact(graph, symbol)
    if results is None:
        print(f"Error: Symbol or rule '{symbol}' not found in the index.", file=sys.stderr)
        return 1

    print("\n".join(results))

    if args.html:
        selected_node_id: Optional[str] = None
        rule_id = f"rule:{symbol}"
        if rule_id in graph["nodes"]:
            selected_node_id = rule_id
        else:
            func_prefix = f"function:{symbol}@"
            for node_id in graph["nodes"]:
                if node_id.startswith(func_prefix):
                    selected_node_id = node_id
                    break

        export_html(graph, args.html, selected_node_id=selected_node_id)
        print(f"Interactive graph visualization with '{symbol}' highlighted exported to '{args.html}'.")

    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    """Execute the ``export`` sub-command. Returns an exit code."""
    pipeline_dir: str = args.pipeline_dir
    output_path: str = args.output

    graph = load_index(pipeline_dir)
    if graph is None:
        index_path = os.path.join(pipeline_dir, ".bigi_index.json")
        print(f"Error: Index not found at '{index_path}'.", file=sys.stderr)
        print("Please run 'bigi analyze <pipeline_dir>' first to build the index.", file=sys.stderr)
        return 1

    if output_path.endswith(".graphml"):
        export_graphml(graph, output_path)
        print(f"GraphML exported to '{output_path}'.")
    else:
        print("Error: Unsupported export format. Please use a file with .graphml extension.", file=sys.stderr)
        return 1

    return 0

def _cmd_pr_report(args: argparse.Namespace) -> int:
    """Execute the ``pr-report`` sub-command."""
    pipeline_dir: str = args.pipeline_dir
    output_path: str = args.output

    graph = load_index(pipeline_dir)
    if graph is None:
        index_path = os.path.join(pipeline_dir, ".bigi_index.json")
        print(f"Error: Index not found at '{index_path}'.", file=sys.stderr)
        return 1

    modified_nodes = [node for node in graph.get("nodes", {}).values() if node.get("git_modified")]
    
    if not modified_nodes:
        report = "✅ **BiGI Blast Radius Report**: No modified rules or functions detected in the pipeline."
    else:
        report = "💥 **BiGI Blast Radius Report** 💥\n\n"
        report += "The following rules/functions were modified in this PR. Here is the downstream impact:\n\n"
        
        # Deduplicate by name
        seen_names = set()
        for node in modified_nodes:
            name = node["name"]
            if name in seen_names:
                continue
            seen_names.add(name)
            
            results = trace_impact(graph, name)
            if results:
                # Format as markdown block
                report += f"**Impact of `{name}`**:\n```text\n"
                report += "\n".join(results) + "\n```\n\n"

        report += "*Please ensure all impacted downstream rules have been re-tested before merging.*"

    print(report)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to '{output_path}'.", file=sys.stderr)

    return 0

def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate sub-command."""
    parser = argparse.ArgumentParser(
        description=(
            "BiGI: BDB-Genomics Impact Graph — trace downstream impact across "
            "Snakemake pipelines and R code."
        )
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command to run")

    export_parser = subparsers.add_parser(
        "export",
        help="Export the analyzed index to other graph formats (e.g. GraphML).",
    )
    export_parser.add_argument(
        "output",
        help="Path to export the graph (must end in .graphml).",
    )
    export_parser.add_argument(
        "--pipeline-dir",
        default=".",
        help="Path to the pipeline directory containing the built index (default: current directory).",
    )

    pr_report_parser = subparsers.add_parser(
        "pr-report",
        help="Generate a markdown report of downstream impacts for all git-modified files (useful for CI/CD).",
    )
    pr_report_parser.add_argument(
        "--pipeline-dir",
        default=".",
        help="Path to the pipeline directory containing the built index (default: current directory).",
    )
    pr_report_parser.add_argument(
        "--output",
        help="Path to save the generated markdown report.",
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Index the pipeline directory and build the combined graph.",
    )
    analyze_parser.add_argument(
        "pipeline_dir",
        help="Path to the pipeline directory containing Snakefile and R files.",
    )
    analyze_parser.add_argument(
        "--html",
        help="Path to export the interactive HTML visualization.",
    )

    impact_parser = subparsers.add_parser(
        "impact",
        help="Trace the downstream impact of changing a rule or R function.",
    )
    impact_parser.add_argument(
        "symbol_or_rule_name",
        help="Name of the Snakemake rule or R function to query.",
    )
    impact_parser.add_argument(
        "--pipeline-dir",
        default=".",
        help="Path to the pipeline directory containing the built index (default: current directory).",
    )
    impact_parser.add_argument(
        "--html",
        help="Path to export the interactive HTML visualization of the impact.",
    )


    args_list = sys.argv[1:]
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    # Automatically clone remote git repositories
    if hasattr(args, "pipeline_dir"):
        pdir = args.pipeline_dir
        if pdir.startswith("http://") or pdir.startswith("https://") or pdir.startswith("git@"):
            import subprocess
            import tempfile
            import atexit
            import shutil
            
            temp_dir = tempfile.mkdtemp(prefix="bigi_clone_")
            atexit.register(shutil.rmtree, temp_dir, ignore_errors=True)
            
            print(f"Cloning remote repository '{pdir}' into temporary workspace...")
            try:
                subprocess.run(["git", "clone", pdir, temp_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print(f"Error: Failed to clone repository '{pdir}'.", file=sys.stderr)
                sys.exit(1)
            
            args.pipeline_dir = temp_dir

    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        "analyze": _cmd_analyze,
        "impact": _cmd_impact,
        "export": _cmd_export,
        "pr-report": _cmd_pr_report,
    }
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
