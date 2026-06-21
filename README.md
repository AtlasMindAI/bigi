<div align="center">

# 🌐 BiGI: Blast-radius Impact Graph Indexer
**Universal Software Pipeline Intelligence & Static Analysis**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/BDB-Genomics/BiGI)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FBDB-Genomics%2FBiGI&root-directory=web&project-name=bigi-github)

<img src="assets/bigi_hero.jpg" width="800" alt="BiGI Futuristic Blast Radius Graph">

> **"What breaks if I change this code?"**  
> BiGI connects high-level workflow rules (like Snakemake or Nextflow) directly to the code inside them (Python, R). It builds a beautiful, interactive graph so you can see exactly what breaks if you change a file.

</div>

---

## ✨ Core Features

- 🔗 **See Everything**: We connect your pipeline rules directly to the underlying scripts. You can see the entire flow of your project in one place.
- 🚦 **Git Integration**: When you change a file, the graph lights up. Modified files glow **Red**, and everything that depends on them glows **Orange**. 
- 🤖 **AI Auto-Remediation**: Use the `bigi remediate` command to ask our AI to fix failing pipeline rules automatically based on the graph's blast radius.
- 📡 **Live Execution Overlay**: Run `bigi monitor` while your pipeline runs. The graph nodes will glow yellow (running), blue (done), or red (failed) in real time!
- 🗂️ **Data Contracts (Schemas)**: BiGI infers the data schemas passed between steps (like DataFrame columns). It warns you if a pipeline step expects a column that doesn't exist.
- 🛠️ **Works With Everything**: We natively support **Snakemake**, **Nextflow**, **Python**, and **R**. For everything else, our generic fallback parser can scan **any language** (Bash, Rust, Go, C++, JavaScript, etc.) to extract function calls and dependencies.
- ⚡ **No Setup Needed**: The graph is a single interactive HTML file. No servers or databases required.

---

## 🚀 Quickstart

Install BiGI globally so you can use it anywhere:

```bash
git clone https://github.com/BDB-Genomics/BiGI.git
cd BiGI
pip install -e .
```

---

## 📖 How to Use

BiGI is very easy to use.

### 1. Analyze a Local Project
```bash
bigi analyze path/to/project --html output.html
```

### 2. Live Execution Monitor
Watch your pipeline run in real-time in the graph view.
```bash
# Run your pipeline and save the log
snakemake -j 4 > run.log

# In another terminal, start the monitor
bigi monitor --html output.html --log run.log
```

### 3. AI Auto-Remediation
If a rule breaks, use Gemini AI to find a fix based on downstream impact context.
```bash
export GEMINI_API_KEY="your_api_key"
bigi remediate my_failing_rule --prompt "Fix the missing column error"
```

### 4. Check What Breaks (CLI)
Ask BiGI what happens if you change a specific function:
```bash
bigi impact log_transform --pipeline-dir my_pipeline
```

### 5. GitHub Actions Bot
Add BiGI to your GitHub Actions. It will automatically check Pull Requests and warn you about broken code:
```bash
bigi pr-report --pipeline-dir .
```

---

## 🧠 How it Works

BiGI does not run your code. Instead, it reads your code incredibly fast:
1. **Reads Pipelines**: It scans your `Snakefiles` and `.nf` files to find inputs and outputs.
2. **Reads Scripts**: It uses smart parsers to find all the functions and data structures inside your Python and R scripts.
3. **Builds the Graph**: It connects the scripts back to the pipeline rules, giving you a complete map of your project.

