import traceback
from io import StringIO
import string
import random
from contextlib import redirect_stdout

import sys
import subprocess

class Executor:

    def run(self, code, globals_env=None, locals_env=None):
        # returns output and error
        try:
            tmp_code = ""
            for line in code.split("\n"):
                if not line.startswith("```"):
                    tmp_code += line + "\n"
            
            
            # f = StringIO()
            # with redirect_stdout(f):
            #     exec(tmp_code, globals_env, locals_env)
            # return f.getvalue(), ""

            result = subprocess.run(
                [sys.executable, "-c", tmp_code],
                #cwd=os.path.abspath(workspace),
                capture_output=True,
                text=True,
            )
            return result.stdout, result.stderr


        except Exception as e:
            return "", str(traceback.format_exc())[-100:]
        return "", "Exception when executing Python code"


if __name__ == "__main__":
    e = Executor()
    output, error = e.run("print('hello')", globals(), locals())
    print("output:", output)
    print("error:", error)