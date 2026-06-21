# BiGI (BDB-Genomics Impact Graph)

BiGI is a command-line interface (CLI) tool designed for bioinformatics developers to answer: **"What breaks if I change this?"** across both the pipeline orchestration layer (Snakemake) and the code layer (R/Bioconductor scripts).

Unlike generic code-intelligence tools that only analyze general-purpose code or only view pipelines as static command blocks, BiGI builds a single, unified dependency graph connecting Snakemake rule inputs/outputs to the underlying R functions executed by those rules.

---

## Features

- **Pipeline DAG Parsing**: Extracts Snakemake rule configurations (inputs, outputs, scripts, and shell commands).
- **R Code Analysis**: Extracts function definitions and function calls (with local scope/caller resolution) directly from R scripts.
- **Cross-Layer Graph Connection**: Links rules to the R functions called by their scripts (both direct and transitive dependencies).
- **Impact Querying**: Traces downstream impact hierarchically across both layers starting from a rule or R function.
- **Honest Confidence Labeling**: Tags every dependency/impact relationship with `HIGH`, `AMBIGUOUS`, or `UNRESOLVED`.
- **Self-Contained HTML Export**: Generates an interactive force-directed graph visualization of the index with **zero external CDN dependencies** (works 100% offline).

---

## Architectural Decisions & R AST Choice

### R Parsing: `parse()` + `getParseData()`
To analyze R code, BiGI invokes R's built-in `parse(keep.source = TRUE)` combined with `getParseData()`.
- **Why this was chosen**: Unlike Python which has a standard, official `ast` module, R has multiple third-party packages for AST parsing (like `lintr` or `codetools`) which can be brittle or require external compilation. `getParseData()` is a native R API available in every standard R installation. It provides a detailed, token-by-token dataframe representing the parse tree (with exact line/column boundaries and parent-child relationships).
- **How caller resolution works**: BiGI extracts function definitions and their exact bounding ranges. For every `SYMBOL_FUNCTION_CALL` token, BiGI finds the narrowest enclosing function definition range. If no function encloses the call, it is classified as a global-scope call executing when the script runs.

---

## Limitations (What is NOT Handled)

BiGI aims to be honest about its static analysis limits:
1. **Dynamic R Dispatch & S4/R6 Classes**: BiGI uses static syntactic analysis. Dynamic method dispatch (e.g., S3/S4 generics, R6 class methods, or `UseMethod`) is not traced. These connections are reported as `UNRESOLVED`.
2. **Non-Standard Evaluation (NSE)**: R's NSE (frequent in packages like `dplyr` and `ggplot2` where arguments are interpreted as column names rather than variables/functions) is ignored.
3. **Dynamic Script Sourcing**: Function definitions loaded dynamically at runtime via `source("path/to/file.R")` are not statically followed if the path is dynamically constructed or if the source occurs inside control flow.
4. **Snakemake Wildcard Limits**: While BiGI parses and matches wildcards (e.g., matching `data/{sample}.csv` output to `data/{id}.csv` input), it cannot statically expand computed wildcards that rely on python code execution inside the Snakefile (e.g., `expand()` calls that query filesystem state).
5. **Nextflow Support**: Nextflow parsing is currently out of scope. Only Snakemake is supported as the pipeline orchestration layer.
6. **Cross-Package Resolution**: BiGI does not parse external R libraries (like `DESeq2` or `ggplot2`) that reside outside the indexed project directory. These external calls are labeled `UNRESOLVED`.

---

## Synthetic Test Pipeline Structure

We built a synthetic test pipeline to validate the tool:
- **`raw_data`**: Dummy shell command outputting `data/raw.csv`.
- **`preprocess`**: Runs `scripts/preprocess.R` on `data/raw.csv`, outputting `data/filtered.csv`. Defines `clean_names` and `log_transform`.
- **`normalise`**: Runs `scripts/normalize.R` on `data/filtered.csv`, outputting `data/normalized.csv`. Defines `normalize_counts` and a conflicting definition of `log_transform` (creating a deliberate name collision).
- **`plot_data`**: Runs `scripts/plot.R` on `data/normalized.csv`, outputting `plots/expression_plot.png`. Defines `generate_heatmap`, which calls `clean_names` (defined in `preprocess.R`) to verify cross-file call resolution.

---

## CLI Usage & Verification Results

### 1. Indexing the Codebase (`analyze`)
To analyze the directory and generate the index:
```bash
python3 bigi-cli analyze test_pipeline --html test_pipeline/visualization.html
```
*Output:*
```
Analyzing genomics pipeline at 'test_pipeline'...
Analysis complete. Index saved to 'test_pipeline/.bigi_index.json'.
Indexed 18 nodes and 26 edges.
Interactive graph visualization exported to 'test_pipeline/visualization.html'.
```

### 2. Querying Downstream Impact (`impact`)

#### Test Case A: Happy Path (`clean_names`)
Querying `clean_names` (which is defined in `preprocess.R` and called inside `plot.R`):
```bash
python3 bigi-cli impact clean_names --pipeline-dir test_pipeline
```
*Output:*
```
Symbol: function: clean_names (in scripts/preprocess.R, lines 2-5)
Downstream Impact (what breaks if changed):
  [Depth 1] function: generate_heatmap (in scripts/plot.R) (Confidence: HIGH)
    [Depth 2] rule: plot_data (Confidence: HIGH)
  [Depth 1] rule: preprocess (Confidence: HIGH)
    [Depth 2] rule: normalise (Confidence: HIGH - Input 'data/filtered.csv' matched output)
      [Depth 3] rule: plot_data (Confidence: HIGH - Input 'data/normalized.csv' matched output)
```

#### Test Case B: Ambiguous Resolution (`log_transform`)
Querying the conflicting function `log_transform` (defined in both `preprocess.R` and `normalize.R`):
```bash
python3 bigi-cli impact log_transform --pipeline-dir test_pipeline
```
*Output:*
```
Symbol: function: log_transform (in scripts/normalize.R, lines 7-10)
Downstream Impact (what breaks if changed):
  [Depth 1] rule: normalise (Confidence: AMBIGUOUS - Multiple definitions of 'log_transform' exist)
    [Depth 2] rule: plot_data (Confidence: HIGH - Input 'data/normalized.csv' matched output)
  [Depth 1] rule: preprocess (Confidence: AMBIGUOUS - Multiple definitions of 'log_transform' exist)
    [Depth 2] rule: normalise (Confidence: HIGH - Input 'data/filtered.csv' matched output)
      [Depth 3] rule: plot_data (Confidence: HIGH - Input 'data/normalized.csv' matched output)

Symbol: function: log_transform (in scripts/preprocess.R, lines 7-10)
Downstream Impact (what breaks if changed):
  [Depth 1] rule: normalise (Confidence: AMBIGUOUS - Multiple definitions of 'log_transform' exist)
    [Depth 2] rule: plot_data (Confidence: HIGH - Input 'data/normalized.csv' matched output)
  [Depth 1] rule: preprocess (Confidence: AMBIGUOUS - Multiple definitions of 'log_transform' exist)
    [Depth 2] rule: normalise (Confidence: HIGH - Input 'data/filtered.csv' matched output)
      [Depth 3] rule: plot_data (Confidence: HIGH - Input 'data/normalized.csv' matched output)
```

#### Test Case C: Rule Downstream + Touched Functions (`preprocess`)
Querying the rule `preprocess`:
```bash
python3 bigi-cli impact preprocess --pipeline-dir test_pipeline
```
*Output:*
```
Symbol: rule: preprocess (in Snakefile)
Downstream Impact (what breaks if changed):
  [Depth 1] rule: normalise (Confidence: HIGH - Input 'data/filtered.csv' matched output)
    [Depth 2] rule: plot_data (Confidence: HIGH - Input 'data/normalized.csv' matched output)
R Functions Touched by Script (direct and transitive calls):
  [Depth 1] function: clean_names (in scripts/preprocess.R) (Confidence: HIGH)
    [Depth 2] function: return (UNRESOLVED definition) (Confidence: UNRESOLVED)
  [Depth 1] function: log_transform (in scripts/normalize.R) (Confidence: AMBIGUOUS - Multiple definitions of 'log_transform' exist)
    [Depth 2] function: mean (UNRESOLVED definition) (Confidence: UNRESOLVED)
    [Depth 2] function: return (UNRESOLVED definition) (Confidence: UNRESOLVED)
  [Depth 1] function: log_transform (in scripts/preprocess.R) (Confidence: AMBIGUOUS - Multiple definitions of 'log_transform' exist)
    [Depth 2] function: log (UNRESOLVED definition) (Confidence: UNRESOLVED)
    [Depth 2] function: return (UNRESOLVED definition) (Confidence: UNRESOLVED)
  [Depth 1] function: read.csv (UNRESOLVED definition) (Confidence: UNRESOLVED)
  [Depth 1] function: write.csv (UNRESOLVED definition) (Confidence: UNRESOLVED)
```

#### Test Case D: Failure on Nonexistent Symbol
```bash
python3 bigi-cli impact nonexistent_symbol --pipeline-dir test_pipeline
```
*Output (exits with status 1):*
```
Error: Symbol or rule 'nonexistent_symbol' not found in the index.
```

---

## Recent Updates

- **Exponential DFS Traversal Fix**: Resolved a performance issue where the impact traversal explored all paths redundantly, which would cause the tool to hang on complex pipelines.
- **Python `async def` Support**: The Python AST parser now correctly captures asynchronous functions.
- **WASM Memory Safety**: Added array bounds checking for JS-provided link indices inside the Rust physics engine to prevent memory out-of-bounds crashes.
- **WASM Initialization Optimization**: Replaced an O(N×E) index loop during WASM graph renderer initialization with an O(1) Map lookup.
- **Graceful CLI Default**: Running `bigi` with no arguments now prints the help text instead of running a default analysis.
