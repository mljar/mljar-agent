from io import StringIO
from pylint.lint import Run
from pylint.reporters.text import TextReporter

def lint(code_fname):
    pylint_output = StringIO()
    reporter = TextReporter(pylint_output)
    try:
        Run(args=["--disable=trailing-whitespace", 
                  "--disable=missing-function-docstring", 
                  "--disable=missing-module-docstring", 
                  "--disable=missing-class-docstring", 
                  "--disable=line-too-long",
                  #"--errors-only",
                  code_fname], reporter=reporter, exit=False)
    except Exception as e:
        print(str(e))

    content = pylint_output.getvalue()
    if content is None or content == "":
        return ""
    tmp_content = ""
    for l in content.split("\n"):
        if l.startswith("***"):
            continue
        if l.startswith("---"):
            break
        if l == "":
            continue
        tmp_content += l+"\n"
    return tmp_content

