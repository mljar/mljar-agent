from datetime import datetime


def prompt_thoughts(task): 
    return f"""Your task is:

{task}

Current date is {str(datetime.now().strftime("%Y-%m-%d"))}

INSTRUCTIONS

What might be difficulites in solving this task?

Write task requirements in up to 100 words. 

Please include your thoughts.
"""


