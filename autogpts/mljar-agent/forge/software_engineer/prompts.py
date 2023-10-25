


def prompt_write_code(task):
    return f"""Your task is:

{task}

INSTRUCTIONS

Use python code to solve the task.

Please call the function that is solving the task if needed.

Please start the file with `# NEW_FILE filename.py` 

```
# NEW_FILE filename.py

# TODO: add imports

# TODO: your code here

```

Please return python code ONLY."""


def prompt_fix_linting(code, linter_output):
    return f"""Improve below Python code

```
{code}
```

Linter problems for above code

```
{linter_output}
```

INSTRUCTIONS

Please start the file with `# NEW_FILE test_filename.py` 

Please return improved python code ONLY.""".format(code, linter_output)

def prompt_write_tests(task, code): 
    return f"""Task is:

{task}

Generated code to solve task:

```
{code}
```

INSTRUCTIONS

Write tests that fulfill the task requirements.

Please start the file with `# NEW_FILE test_filename.py` 

Tests will be executed with command `python test_filename.py`, please call tests in the end.

```
# NEW_FILE test_filename.py

import unittest

#TODO: create tests here

if __name__ == '__main__':
    unittest.main()
```

Please return python code ONLY."""


def prompt_fix_code(task, code, test_code, test_results):
    return f"""Your task is:

{task}

Generated code:

```
{code}
```

Tests

```
{test_code}
```

Tests output

```
{test_results}
```

INSTRUCTIONS

Fix code to pass all tests and fulfill task requirements. 

Please start the file with `# NEW_FILE test_filename.py` 

Do NOT return the same code. 

Do NOT return tests.

Please return fixed python code ONLY.

"""

def prompt_requirements_list(task):
    return f"""what are the most important requirements for task:

{task}

Write short list with up to 200 words
"""