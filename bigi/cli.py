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


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate sub-command."""
    parser = argparse.ArgumentParser(
        description=(
            "BiGI: BDB-Genomics Impact Graph — trace downstream impact across "
            "Snakemake pipelines and R code."
        )
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command to run")

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
    if not args_list:
        args_list = ["analyze", ".", "--html", "visualization.html"]
        print("No command specified. Defaulting to: bigi analyze . --html visualization.html")

    args = parser.parse_args(args_list)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    dispatch = {"analyze": _cmd_analyze, "impact": _cmd_impact}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
