<div align="center">

# BiGI

**Blast-radius Impact Graph Indexer**

BiGI shows what breaks before you change the code in any codebase.

[![CI](https://github.com/AtlasMindAI/bigi/actions/workflows/ci.yml/badge.svg)](https://github.com/AtlasMindAI/bigi/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![npm](https://img.shields.io/badge/npx-bigi-CB3837.svg)](https://www.npmjs.com/)

<figure>
<img src="assets/hero.jpg" width="800" alt="BiGI blast radius graph preview" style="border-radius:16px; box-shadow:0 20px 60px rgba(0,0,0,0.25);">
<figcaption style="margin-top:12px; color:#6b7280; font-size:0.95rem;">Visualize downstream impact across any codebase.</figcaption>
</figure>

</div>

## What BiGI does

BiGI scans a repository, builds a dependency graph, and traces downstream impact across:

- Python, R, and shell code
- automation, build, and workflow files
- scripts, modules, and source files
- local folders, GitHub URLs, or multiple repositories

Use it to answer questions like:

- What breaks if I change this function, file, or script?
- Which nodes depend on this one?
- Which files were modified in this repo?
- How do I export the graph for review or tooling?

## Install

### pip

```bash
pip install git+https://github.com/AtlasMindAI/bigi.git
```

### From source

```bash
git clone https://github.com/AtlasMindAI/bigi.git
cd BiGI
pip install -e .
```

### npx

```bash
npx bigi --help
```

## Usage

### Build a graph

```bash
bigi analyze path/to/codebase --html graph.html
```

Open `graph.html` in a browser to inspect the graph.

### Trace impact

```bash
bigi impact my_function --pipeline-dir path/to/codebase/
```

### Export GraphML

```bash
bigi analyze . && bigi export graph.graphml
```

### Analyze multiple repositories

```bash
bigi analyze repo1/ repo2/ repo3/ --html org_graph.html
```

### Run the live monitor

```bash
bigi monitor --html graph.html --log run.log
```

## Command palette

Press `Ctrl/Cmd + K` in the graph view to open one place for the main actions:

- search nodes
- jump to a node
- trace a path between nodes
- change depth and grouping
- toggle focus and Git filters
- reset, pause, or export the graph

## Advanced graph views

- Trace the shortest path between two nodes
- Limit focus mode to 1, 2, 3, or all hops
- Collapse files, folders, or packages into groups
- Highlight changed files and downstream impact
- Export the same graph as HTML or GraphML

## Output

BiGI can generate:

- an interactive HTML graph
- GraphML for Cytoscape, Gephi, or other graph tools
- a markdown PR impact report
- a live execution overlay for jobs, tasks, and runs

## GitHub Action

BiGI can comment on pull requests with the downstream impact of changed files.

```yaml
name: BiGI Blast Radius
on:
  pull_request:
    branches: [main, master]

permissions:
  pull-requests: write
  contents: read

jobs:
  blast-radius:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: AtlasMindAI/bigi@main
        with:
          pipeline-dir: '.'
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## How it works

1. Parse supported files and extract functions, calls, files, and schema reads.
2. Build a directed graph of dependencies.
3. Trace downstream impact from the item you changed.
4. Render the result in a self-contained HTML view.

## CLI reference

| Command | Description |
|---|---|
| `bigi analyze <dir\|url> [--html out.html]` | Build a graph and optionally export HTML |
| `bigi impact <symbol> [--pipeline-dir .]` | Trace downstream impact for a rule, function, or file |
| `bigi export <file.graphml>` | Export the saved index to GraphML |
| `bigi pr-report [--pipeline-dir .] [--output report.md]` | Generate a markdown blast radius report |
| `bigi remediate <symbol> --prompt "..."` | Ask Gemini for a code fix with impact context |
| `bigi monitor --html graph.html --log run.log` | Serve the graph and stream execution state |

## Testing

```bash
pytest tests/ -v
```

## Vercel

BiGI can also run as a web app. Visit your deployment and append `owner/repo`:

```text
https://your-bigi-app.vercel.app/AtlasMindAI/bigi
```
