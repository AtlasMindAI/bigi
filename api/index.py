from flask import Flask, Response
import tempfile
import os
import subprocess

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    if not path:
        return index()
    parts = path.strip('/').split('/')
    if len(parts) >= 2:
        owner = parts[0]
        repo = parts[1]
        repo_url = f"https://github.com/{owner}/{repo}"
    else:
        return index()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        html_out = os.path.join(tmpdir, "out.html")
        try:
            import sys
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env = os.environ.copy()
            env["PYTHONPATH"] = root_dir + os.pathsep + env.get("PYTHONPATH", "")
            
            cmd = [sys.executable, "-m", "bigi.cli", "analyze", repo_url, "--html", html_out]
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            
            with open(html_out, "r", encoding="utf-8") as f:
                html_content = f.read()
                
            return Response(html_content, mimetype='text/html')
        except subprocess.CalledProcessError as e:
            err_html = f"""
            <html><body style="font-family:sans-serif;padding:2rem;">
              <h1>Error analyzing repository</h1>
              <p>Could not analyze <strong>{repo_url}</strong>. Ensure it is a public repository with Snakemake/Nextflow/Scripts.</p>
              <pre style="background:#eee;padding:1rem;overflow-x:auto;">{e.stderr}</pre>
            </body></html>
            """
            return Response(err_html, status=500, mimetype='text/html')
        except Exception as e:
            return Response(str(e), status=500)

@app.route('/')
def index():
    return Response("""
    <html>
      <body style="background:#0a0a0f;color:white;font-family:sans-serif;text-align:center;padding-top:20vh;">
        <h1 style="font-size:4rem;background:-webkit-linear-gradient(#818cf8, #34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">BiGIGitHub</h1>
        <p style="font-size:1.5rem;color:#9ca3af;">Instantly generate interactive dependency graphs.</p>
        <p style="color:#6b7280;margin-top:2rem;">Try: <code>/BDB-Genomics/BiGI</code></p>
      </body>
    </html>
    """, mimetype='text/html')

