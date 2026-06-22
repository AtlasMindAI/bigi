import os
import pytest
import subprocess
import shutil
import tempfile
import json
from bigi.parsers.generic import parse_generic_file
from bigi.parsers.snakemake import parse_snakemake_file

# Check if Rscript is available
has_rscript = shutil.which("Rscript") is not None

def test_generic_parser():
    """Test the regex-based generic AST parser using a dummy JavaScript script."""
    dummy_code = '''
function my_function(a, b) {
    console.log("hello");
}

my_function(1, 2);
other_function();
    '''
    test_file = "/tmp/test_dummy.js"
    with open(test_file, "w") as f:
        f.write(dummy_code)
        
    try:
        res = parse_generic_file(test_file, "/tmp")
        defs, calls = res["definitions"], res["calls"]
        
        # Verify function definition
        assert len(defs) == 1
        assert defs[0]["name"] == "my_function"
        
        # Verify function calls
        call_names = [c["name"] for c in calls]
        assert "my_function" in call_names
        assert "other_function" in call_names
        assert "log" in call_names
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


@pytest.mark.skipif(not has_rscript, reason="Rscript not installed")
def test_r_parser():
    """Test the R AST parser with standard and complex/anonymous R code structure."""
    dummy_code = """
    # Standard assignment
    my_fun <- function(a) {
      print(a)
    }

    # Call it
    my_fun(10)

    # Anonymous / nested function that has no assignment operator as parent
    lapply(1:10, function(x) { x * 2 })
    
    # Nested function definition with assignment in complex structure
    # to ensure LHS detection doesn't crash with NA node IDs
    nested_list <- list(
      sub_fun = function(y) {
        return(y)
      }
    )
    """
    
    with tempfile.NamedTemporaryFile(suffix=".R", mode="w", delete=False) as tf:
        tf.write(dummy_code)
        temp_r_file = tf.name
        
    try:
        # Resolve r_parser.R path relative to tests directory
        parser_r_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bigi", "parsers", "r_parser.R")
        
        # We pass the temporary R file inside a JSON array, as r_parser.R expects
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as json_tf:
            json.dump([temp_r_file], json_tf)
            temp_json_file = json_tf.name
            
        try:
            res = subprocess.run(
                ["Rscript", parser_r_path, temp_json_file, tempfile.gettempdir()],
                capture_output=True, text=True, check=True
            )
            parsed_data = json.loads(res.stdout)
            
            defs = parsed_data.get("definitions", [])
            calls = parsed_data.get("calls", [])
            
            def_names = [d["name"] for d in defs]
            assert "my_fun" in def_names
            
            call_names = [c["name"] for c in calls]
            assert "my_fun" in call_names
            assert "lapply" in call_names
            assert "print" in call_names
            
        finally:
            if os.path.exists(temp_json_file):
                os.remove(temp_json_file)
    finally:
        if os.path.exists(temp_r_file):
            os.remove(temp_r_file)
