import os

from forge.software_engineer.linter import lint
from forge.software_engineer.tester import run_tests, tests_failed
from forge.software_engineer.prompts import *
from forge.chatgpt import ChatGPT

class JuniorDev:
    def __init__(self):
        self.gpt = ChatGPT()
    
    def chat(self, prompt):
        return self.gpt.chat(prompt, model="gpt-3.5-turbo", use_prev_msgs=False) #, system_role="You are Python developer")

class SeniorDev:
    def __init__(self):
        self.gpt = ChatGPT()
    
    def chat(self, prompt):
        return self.gpt.chat(prompt, model="gpt-4", use_prev_msgs=True) #, system_role="You are senior Python developer")



def response2code(response):
    code_fname = ""
    tmp_code = ""
    ticks_count = 0
    for i, line in enumerate(response.split("\n")):
        if i < 2 and line.startswith("#") and code_fname == "":
            code_fname = line.split(" ")[-1]
        if line.startswith("```"):
            ticks_count += 1
        if not line.startswith("```") and ticks_count < 2:
            tmp_code += line + "\n"
    has_main = "if __name__ ==" in tmp_code
    if code_fname != "":
        with open(code_fname, "w") as fin:
            fin.write(tmp_code)
        if not os.path.exists("__init__.py"):
            with open("__init__.py", "w") as fin:
                fin.write("")
    return tmp_code, code_fname, has_main

def run_coder(task, explain):
    #junior = JuniorDev()
    senior = SeniorDev()

    task += "\n\nExplanation:\n\n" + explain
    #req_list = senior.chat(prompt_requirements_list(task))
    #task += "\n\nImportant requirements:\n\n"+req_list+"\n\n"
    
    print(task)
    # write code
    print("⌨️ WRITE CODE")
    #response = senior.chat(prompt_write_code(task))
    response = senior.chat(prompt_write_code(task))
    code, code_fname, has_main = response2code(response)
    
    print(code_fname)
    print(code)
    
    # # lint
    # linter_output = lint(code_fname)
    # print("LINTER")
    # print(linter_output)
    # if linter_output != "":
    #     # fix linter problems
    #     response = junior.chat(prompt_fix_linting(code, linter_output))
    #     code, code_fname, has_main = response2code(response)
    # #if has_main:
    # # write tests
    # print("WRITE TESTS")
    # response = junior.chat(prompt_write_tests(task, code))
    # test_code, test_fname, _ = response2code(response)
    
    # print(test_fname)
    # print(test_code)

    # # lint tests
    # print("lint tests")
    # linter_output = lint(test_fname)
    # print(linter_output)
    # if linter_output != "":
    #     # fix linter problems
    #     response = junior.chat(prompt_fix_linting(test_code, linter_output))
    #     test_code, test_fname, _ = response2code(response)

    # # 3 times ... run tests
    # for _ in range(3):
    #     print("RUN TESTS")
    #     test_results = run_tests(test_fname)
    #     if tests_failed(test_results):
    #         break

    # print("TEST RESULTS")
    # print(test_results)
    # if "FAILED" in test_results or "Error" in test_results:
    #     response = senior.chat(prompt_fix_code(task, code, test_code, test_results))
    #     code, code_fname, has_main = response2code(response)

            
    return f"Software developer successfully created a file {code_fname}"
    #senior.chat("summarize what have you done in up to 50 words")