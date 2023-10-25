from codecs import ignore_errors
import json
import pprint
import uuid
import os
from datetime import datetime

from forge.sdk import (
    Agent,
    AgentDB,
    Step,
    StepRequestBody,
    Workspace,
    ForgeLogger,
    Task,
    TaskRequestBody,
    PromptEngine,
    chat_completion_request,
)

LOG = ForgeLogger(__name__)

from forge.chatgpt import ChatGPT

from forge.agent_funcs import functions, functions_map
from forge.agent_prompts import *
from forge.data_engineer.utils import files_to_prompt

import pydantic
import re 
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

def fix_json_escape_sequences(json_str: str) -> str:
    # Match all instances of \something that aren't valid JSON escape sequences
    pattern = r'\\(?![/bfnrtu"])'
    corrected_str = re.sub(pattern, r'\\\\', json_str)
    return corrected_str


class ForgeAgent(Agent):
    def __init__(self, database: AgentDB, workspace: Workspace):
        super().__init__(database, workspace)
        
    
    async def create_task(self, task_request: TaskRequestBody) -> Task:
        try:
            task = await self.db.create_task(
                input=task_request.input,
                additional_input=task_request.additional_input
            )

            LOG.info(
                f"📦📦📦 Task created: {task.task_id} input: {task.input[:40]}{'...' if len(task.input) > 40 else ''}"
            )
        except Exception as err:
            LOG.error(f"create_task failed: {err}")
            raise err

        return task



    async def execute_step(self, task_id: str, step_request: StepRequestBody) -> Step:

        task = await self.db.get_task(task_id)
    
        # Create a new step in the database
        # have AI determine last step
        step = await self.db.create_step(
            task_id=task_id,
            input=step_request,
            additional_input=step_request.additional_input,
            is_last=True
        )
        

        # initialize
        self.wd = os.path.join(str(self.workspace.base_path), task.task_id)
        LOG.info(f"💽 Set working directory: {self.wd}")
        if not os.path.exists(self.wd):
            os.makedirs(self.wd)
        os.chdir(self.wd)

        self.files = {f:os.path.getmtime(os.path.join(self.wd, f)) for f in os.listdir(self.wd) if os.path.isfile(os.path.join(self.wd, f))}
        
        if self.files.keys():
            LOG.info("📂 Current files")
            LOG.info(str(self.files.keys()))

        LOG.info(
            f"🧠 Think about requirements for task"
        )
        self.ctrl = ChatGPT()

        inc_files = files_to_prompt(self.wd, self.files.keys())
        task_desc = task.input
        if inc_files != "":
            task_desc += f"\n\nThere are {len(self.files)} files in the current directory. Files are listed below:\n\n"
            task_desc += inc_files
            
        LOG.info(prompt_thoughts(task_desc))
        steps_response = self.ctrl.chat(prompt_thoughts(task_desc), model="gpt-4")
        LOG.info("💬 Initial thoughts about task:")
        LOG.info(steps_response)

        prev_func_name, prev_func_args = None, None

        for iteration in range(6):

            LOG.info(f"------------ NEW ITERATION ({iteration}) -------------")
        
            which = "first" if iteration == 0 else "next"
            step_prompt = f"Call function for the {which} step"
            if which == "next":
                step_prompt += ". Do not call the same function two times in a row"
            LOG.info(f"⏭️ {step_prompt}")
            step_response = self.ctrl.chat(step_prompt, functions=functions, model="gpt-4")
            print(step_response)

            print()

            if "function_call" in step_response:
                func_name = step_response["function_call"]["name"]

                args = json.loads(fix_json_escape_sequences(step_response["function_call"]["arguments"]), strict=False)

                LOG.info(f"{func_name} {args}")
                print(f"⚡ Call function {func_name}")
                print()

                if prev_func_name is not None:
                    if prev_func_name == func_name and json.dumps(prev_func_args) == json.dumps(args):
                        LOG.info("Duplicate function!")
                        response = self.ctrl.chat("You are trying to call the same function again. Whats wrong with you? Do something different", model="gpt-4")
                        print(response)
                        continue                        

                prev_func_name = func_name 
                prev_func_args = args

                if func_name in ["call_data_engineer"]:
                    args = {"task": task.input}

                if func_name in ["call_software_engineer", "web_search"]:
                    args["task"] = task.input

                if func_name == "all_done":
                    break
                else:
                    
                    try:
                        func = functions_map[func_name]

                        func_response = func(**args)                    

                        print("Function response")
                        print(func_response)
                        self.ctrl.add_function_response(function_name=func_name, response=func_response)
                    except Exception as e:
                        print(str(e))
                        self.ctrl.add_function_response(function_name=func_name, response=f"Error when calling function. {str(e)}")



            for file_path in os.listdir(os.getcwd()):
                # skip directories
                if os.path.isdir(os.path.join(self.wd, file_path)):
                    continue
                if self.files.get(file_path, "") != "" or self.files.get(file_path, 0) != os.path.getmtime(os.path.join(self.wd, file_path)):
                    LOG.info(f"🗒️ Create artifact {file_path}")

                    await self.db.create_artifact(
                        task_id=task_id,
                        step_id=step.step_id,
                        file_name=file_path,
                        relative_path="",
                        agent_created=True,
                    )
                    self.files[file_path] = os.path.getmtime(os.path.join(self.wd, file_path))

                    self.ctrl.add_function_response(function_name="save_to_file", response=f"Created a new file {file_path}")

            #critique_response = self.ctrl.chat("Is all OK? What is wrong? What can be done additionally? Provide critique to previous steps in up to 50 words", functions=functions)
            #LOG.info(str(critique_response))
            

        # Return the completed step
        return step