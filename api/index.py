"""Vercel serverless function for BiGI web interface.

Downloads GitHub repositories as zip archives (no git binary needed)
and runs BiGI analysis using Python imports directly.
"""

from flask import Flask, Response
import tempfile
import os
import zipfile
import urllib.request
import traceback

from bigi.graph import build_graph
from bigi.cli import export_html

app = Flask(__name__)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if not path:
        return landing_page()

    parts = path.strip('/').split('/')
    if len(parts) < 2:
        return landing_page()

    owner = parts[0]
    repo = parts[1]

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Download repo as zip archive (no git binary required)
            zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
            zip_path = os.path.join(tmpdir, "repo.zip")
            extract_dir = os.path.join(tmpdir, "repo")

            urllib.request.urlretrieve(zip_url, zip_path)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            # GitHub zips have a single top-level folder like "repo-main/"
            contents = os.listdir(extract_dir)
            if len(contents) == 1 and os.path.isdir(
                os.path.join(extract_dir, contents[0])
            ):
                repo_dir = os.path.join(extract_dir, contents[0])
            else:
                repo_dir = extract_dir

            # Run BiGI analysis directly via Python API
            graph_data = build_graph(repo_dir)

            # Export to HTML
            html_out = os.path.join(tmpdir, "out.html")
            export_html(graph_data, html_out)

            with open(html_out, "r", encoding="utf-8") as f:
                html_content = f.read()

            return Response(html_content, mimetype='text/html')

        except urllib.error.HTTPError as e:
            if e.code == 404:
                err_html = f"""
                <html><body style="font-family:sans-serif;padding:2rem;background:#0a0a0f;color:white;">
                  <h1 style="color:#f87171;">Repository not found</h1>
                  <p>Could not find <strong>github.com/{owner}/{repo}</strong>.</p>
                  <p style="color:#9ca3af;">Make sure the repository exists, is public, and has a <code>main</code> branch.</p>
                  <a href="/" style="color:#818cf8;">← Back to home</a>
                </body></html>
                """
            else:
                err_html = f"""
                <html><body style="font-family:sans-serif;padding:2rem;background:#0a0a0f;color:white;">
                  <h1 style="color:#f87171;">GitHub error (HTTP {e.code})</h1>
                  <p>Failed to download <strong>github.com/{owner}/{repo}</strong>.</p>
                  <a href="/" style="color:#818cf8;">← Back to home</a>
                </body></html>
                """
            return Response(err_html, status=e.code, mimetype='text/html')

        except Exception as e:
            err_html = f"""
            <html><body style="font-family:sans-serif;padding:2rem;background:#0a0a0f;color:white;">
              <h1 style="color:#f87171;">Error analyzing repository</h1>
              <p>Could not analyze <strong>github.com/{owner}/{repo}</strong>.</p>
              <pre style="background:#1a1a2e;padding:1rem;border-radius:8px;overflow-x:auto;color:#fbbf24;">{traceback.format_exc()}</pre>
              <a href="/" style="color:#818cf8;">← Back to home</a>
            </body></html>
            """
            return Response(err_html, status=500, mimetype='text/html')


def landing_page():
    return Response("""
    <html>
      <body style="background:#0a0a0f;color:white;font-family:sans-serif;text-align:center;padding-top:20vh;">
        <h1 style="font-size:4rem;background:-webkit-linear-gradient(#818cf8, #34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">BiGI</h1>
        <p style="font-size:1.5rem;color:#9ca3af;">Instantly visualize any GitHub repository's dependency graph.</p>
        <p style="color:#6b7280;margin-top:2rem;">Add <code style="background:#1a1a2e;padding:4px 8px;border-radius:4px;">/owner/repo</code> to the URL to get started.</p>
        <p style="color:#4b5563;margin-top:1rem;">Example: <code style="background:#1a1a2e;padding:4px 8px;border-radius:4px;">/BDB-Genomics/bigi</code></p>
      </body>
    </html>
    """, mimetype='text/html')
