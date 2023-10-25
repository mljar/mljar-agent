import os

from forge.get_website import get_website
from forge.executor import Executor

from forge.chatgpt import ChatGPT
from forge.data_engineer.data_engineer import DataEngineerAgent
from forge.data_engineer.utils import guess_delimiter
from forge.web_search import WebSearch
from forge.localmem import LocalMem

from forge.software_engineer.software_engineer import run_coder

from forge.sdk import (
    ForgeLogger,
)

LOG = ForgeLogger(__name__)


def execute_python_code(code, explain=""):

    e = Executor()
    output, error = e.run(code, globals(), locals())
    if error is not None and error != "":
        return f"Error when running python code. {error}"
    response = f"{explain}\n\n"
    if output != "":
        response += f"Output:\n```\n{output}\n```\n"
    else:
        response += f"There is no output.\n\n"
    return f"{response}Code run successfully"


def read_file(filename):
    fpath = os.path.join(os.getcwd(), filename)
    
    if not os.path.exists(fpath):
        return f"File {filename} does not exist"

    content = ""
    with open(fpath, "r") as fin:
        content = fin.read()
    lines = content.split("\n")

    f = filename
    prompt = ""
    delimiter_str = ""
    if fpath.endswith(".csv"):
        delimiter = guess_delimiter(fpath)
        delimiter_str = f" (delimiter \"{delimiter}\")"
    if len(lines) == 0:
        prompt += f"\nfile {f} is empty\n\n"
    elif len(lines) < 50:
        prompt += f"\nfile {f}{delimiter_str} includes\n\n"
        prompt += "```\n"
        prompt += content + "\n```\n\n"
    else:
        prompt += f"\nfile {f}{delimiter_str} has {len(lines)} lines\nWE DONT INCLUDE FULL FILE HERE, ONLY FIRST 50 LINES. This file is longer than 50 lines\nbelow are first 50 lines from it\n```"
        for l in lines[:50]:
            prompt += f"{l}\n"
        prompt += "\n# REST OF THE FILE... \n"
        prompt += "\n```\n\n"
    return prompt


def save_to_file(filename, content):

    overwrite_msg = ""
    if os.path.exists(filename):
        overwrite_msg = f"File {filename} already exists. Its content will be overwritten."
        overwrite_msg += read_file(filename)
        overwrite_msg += "The above content will be OVERWRITTEN with a new content\n\nPlease be sure that you want to overwrite the file\n\n"

    try:
        with open(filename, "w") as fout:
            fout.write(content)
    except Exception as e:
        pass
    return f"{overwrite_msg}File {filename} saved successfully"


def check_if_file_exists(filename):
    fpath = os.path.join(os.getcwd(), filename)
    
    if not os.path.exists(fpath):
        return f"File {filename} does not exist"
    return f"File {filename} exists"

def web_search(task, search_goal, query):
    mem = LocalMem()
    ws = WebSearch(task, search_goal, query, mem)
    response = ws.run()
    LOG.info(response)
    return response

def call_software_engineer(task, explain):
    LOG.info("Software Engineer")
    return run_coder(task, explain)

def call_data_engineer(task):
    LOG.info("Data Engineer")

    agent = DataEngineerAgent(task)
    return agent.run()


def all_done():
    print("All done!")


def create_summary(input_text, summary_goal):
    chat = ChatGPT()
    return chat.chat(f"Create summary of the following text:\n\n{input_text}\n\nYour goal is {summary_goal}")
    

functions_map = {
    "web_search": web_search,
    "get_website": get_website,
    "save_to_file": save_to_file,
    "read_file": read_file,
    "check_if_file_exists": check_if_file_exists,
    "execute_python_code": execute_python_code,
    "call_software_engineer": call_software_engineer,
    "call_data_engineer": call_data_engineer,
    "create_summary": create_summary,
    "all_done": all_done,
}


functions = [
    {
        "name": "create_summary",
        "description": "Create summary or brief report from input text",
        "parameters": {
            "type": "object",
            "properties": {
                "input_text": {
                    "type": "string",
                    "description": "Input text to be summarized",
                },
                "summary_goal": {
                    "type": "string",
                    "description": "Goal of summary",
                },
                
            },
            "required": ["input_text", "summary_goal"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the internet to get information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query search engine",
                },
                "search_goal": {
                    "type": "string",
                    "description": "Verbose description of search goal, up to 50 words. It should be longer than query.",
                },
                
            },
            "required": ["search_goal", "query"],
        },
    },
    {
        "name": "get_website",
        "description": "Fetch website HTML source",
        "parameters": {
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Exact URL address of website",
                },
            },
            "required": ["address"],
        },
    },
    {
        "name": "execute_python_code",
        "description": "Execute Python code as script. It doesnt save code in file. Print variables with `print()` function to display its value (it is not Jupyter notebook). It doesnt keep open session between calls. It just executes code and returns output (stdout and stderr).",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to be run.",
                },
                "explain": {
                    "type": "string",
                    "description": "Explain what code is doing in up to 100 words"
                }
            },
            "required": ["code", "explain"],
        },
    },
    {
        "name": "call_software_engineer",
        "description": "This function calls Software Engineer agent. It creates Python program.",
        "parameters": {
            "type": "object",
            "properties": {
                "explain": {
                    "type": "string",
                    "description": "Explain what program should be doing in up to 100 words"
                }
            },
            "required": ["explain"],
        },
    },
    {
        "name": "call_data_engineer",
        "description": "This function calls Data Engineer agent. This function can manipulate and analyze data. It is using Pandas package.",
        "parameters": {
            "type": "object",
            "properties": {
                "explain": {
                    "type": "string",
                    "description": "Explain what should be done in up to 100 words"
                }
            },
            "required": ["explain"],
        },
    },
    {
        "name": "save_to_file",
        "description": "Save string to file. Please be aware that if file exists you will overwrite its content. If file exists it is better to check its content first",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "File name where content will be saved",
                },
                "content": {
                    "type": "string",
                    "description": "Content to be saved"
                },
            },
            "required": ["filename", "content"],
        },
    },
    {
        "name": "read_file",
        "description": "Read file and attach its content to discussion",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "File name",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "check_if_file_exists",
        "description": "Check if file exists",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "File name",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "all_done",
        "description": "Call this function when task is ready and done", # "Call it when all is done",
        "parameters": {
            "type": "object",
            "properties": {
                "response": {
                    "type": "string",
                    "description": "Final response",
                },
            },
            "required": [],
        },
    }
]
