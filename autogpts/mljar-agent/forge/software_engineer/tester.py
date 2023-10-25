import os
import sys
import subprocess

def run_tests(test_fname):

    print("run_tests")
    print(sys.executable, test_fname)
    print("WD")
    print(os.getcwd())

    result = subprocess.run(
        [sys.executable, test_fname],
        #cwd=os.path.abspath(workspace),
        capture_output=True,
        text=True,
    )

    return result.stderr

def tests_failed(test_results):
    return "FAILED" in test_results or "Error" in test_results
