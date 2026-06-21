import subprocess
import base64
import os
import re

def build_and_embed():
    # 1. Compile Rust to Wasm
    print("Compiling Rust physics library to WebAssembly...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wasm_dir = os.path.join(base_dir, "physics_wasm")
    result = subprocess.run(
        ["cargo", "build", "--target", "wasm32-unknown-unknown", "--release"],
        cwd=wasm_dir,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("Error compiling Rust project:")
        print(result.stderr)
        return False
    
    # 2. Read Wasm file
    wasm_path = os.path.join(wasm_dir, "target", "wasm32-unknown-unknown", "release", "physics_wasm.wasm")
    if not os.path.exists(wasm_path):
        print(f"Error: Wasm file not found at {wasm_path}")
        return False
        
    with open(wasm_path, "rb") as f:
        wasm_bytes = f.read()
        
    wasm_base64 = base64.b64encode(wasm_bytes).decode("utf-8")
    print(f"Compiled WebAssembly size: {len(wasm_bytes) / 1024:.2f} KB")
    print(f"Base64 string size: {len(wasm_base64) / 1024:.2f} KB")
    
    # 3. Update bigi/html_template.py
    template_path = os.path.join(base_dir, "bigi", "html_template.py")
    if not os.path.exists(template_path):
        print(f"Error: Template file not found at {template_path}")
        return False
        
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Search for the WASM_BASE64 placeholder line
    pattern = r'const WASM_BASE64 = ".*?"; // __WASM_BASE64__'
    replacement = f'const WASM_BASE64 = "{wasm_base64}"; // __WASM_BASE64__'
    
    if not re.search(pattern, content):
        print("Error: Could not find WASM_BASE64 placeholder in bigi/html_template.py")
        return False
        
    new_content = re.sub(pattern, replacement, content)
    
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Successfully compiled and embedded WebAssembly into bigi/html_template.py!")
    return True

if __name__ == "__main__":
    build_and_embed()
