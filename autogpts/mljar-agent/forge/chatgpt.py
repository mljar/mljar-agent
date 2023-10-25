import os
import json
import time
import openai
import tiktoken
from datetime import datetime
from tenacity import retry, stop_after_delay

openai.api_key = os.environ["OPENAI_API_KEY"]


def num_tokens_from_string(string: str, encoding_name = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def num_tokens_from_functions(functions, model="gpt-3.5-turbo-0613"):
        """Return the number of tokens used by a list of functions."""
        
        if len(functions) == 0:
            return 0

        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
       
        num_tokens = 0
        for function in functions:
            function_tokens = len(encoding.encode(function['name']))
            function_tokens += len(encoding.encode(function['description']))
           
            if 'parameters' in function:
                parameters = function['parameters']
                if 'properties' in parameters:
                    for propertiesKey in parameters['properties']:
                        function_tokens += len(encoding.encode(propertiesKey))
                        v = parameters['properties'][propertiesKey]
                        for field in v:
                            if field == 'type':
                                function_tokens += 2
                                function_tokens += len(encoding.encode(v['type']))
                            elif field == 'description':
                                function_tokens += 2
                                function_tokens += len(encoding.encode(v['description']))
                            elif field == 'enum':
                                function_tokens -= 3
                                for o in v['enum']:
                                    function_tokens += 3
                                    function_tokens += len(encoding.encode(o))
                            else:
                                print(f"Warning: not supported field {field}")
                    function_tokens += 11

            num_tokens += function_tokens

        num_tokens += 12
        return num_tokens


def num_tokens_from_messages(messages):
    total = 0
    for m in messages:
        for k,v in m.items():
            total += num_tokens_from_string(k)+3 + num_tokens_from_string(str(v))
    return total


def num_tokens(params):
    tokens_messages = num_tokens_from_messages(params.get("messages", [])) 
    tokens_functions = num_tokens_from_functions(params.get("functions", []))
    return tokens_messages + tokens_functions

@retry(stop=stop_after_delay(30))
def completion(params):
    return openai.ChatCompletion.create(**params)


# keep list of tuples (datetime, tokens)
counter = {
    "gpt-3.5-turbo": [],
    "gpt-4": []
}

limits = {
    "gpt-3.5-turbo": 90000,
    "gpt-4": 10000
}

class ChatGPT():

    temperature = 0
    max_tokens = 2000
    top_p = 1
    frequency_penalty = 0
    presence_penalty = 0.6

    def __init__(self):
        self.prev_msgs = []
    
    @property
    def _default_params(self):
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "model": "gpt-3.5-turbo",
        }

    def chat(self, prompt, model="gpt-3.5-turbo", functions=None, use_prev_msgs=True):
        
        msgs = self.prev_msgs if use_prev_msgs else []
        msgs += [
            {
                "role": "user",
                "content": prompt,
            }
        ]
        
        params = {
            **self._default_params,
            "messages": msgs,
        }
        params["model"] = model # "gpt-3.5-turbo" # model
        
        if functions is not None:
            params["functions"] = functions
            params["function_call"] = "auto"
            

        tokens = num_tokens(params)

        params["max_tokens"] = max(4096 - tokens, 2000)

        if tokens > 4096:
            print("Try to trim messages")
            print(f"Starter msgs len={len(msgs)}")
            for i in range(1, len(msgs)-1):
                print(f"Trim {i} msgs")
                params["messages"] = msgs[i:].copy()
                tokens = num_tokens(params)
                if tokens < 3000:
                    params["max_tokens"] = 1000
                    break 


        # get last minute counts ...
        for chances in range(60):
            last_minute_tokens = 0
            for t in reversed(counter[model]):
                if (datetime.now()-t[0]).seconds > 60:
                    break
                last_minute_tokens += t[1]    
            #print(f"Last minute tokens {last_minute_tokens}")
            if last_minute_tokens > limits.get(model, 6000):
                #print("Let's wait a while")
                time.sleep(1)
            else:
                break


        for i in range(5):
            response = None
            try:
                #print(json.dumps(params, indent=4))
                response = completion(params)
                #print(num_tokens_from_messages(params["messages"]))

                #response = openai.ChatCompletion.create(**params)

                #print(json.dumps(response["usage"], indent=4))

                counter[model] += [(datetime.now(), response.get("usage", {}).get("total_tokens", 0))]

            except Exception as e:
                print("--- ChatGPT exception ---", i)
                print(str(e))
                
                if "Rate limit" in str(e) and params["model"] == "gpt-4":
                    if i < 4:
                        print("Please wait 10 seconds ...")
                        time.sleep(10)
                    else:
                        print("Try to use gpt-3.5")
                        params["model"] = "gpt-3.5-turbo"

                #import traceback
                #print(traceback.format_exc())
                #print(json.dumps(params, indent=4))
                #time.sleep(5)

            # all good break the loop
            if response is not None:
                break
        
        if "function_call" in response["choices"][0]["message"]:
            self.prev_msgs += [{
                "role": "assistant",
                "content": None,
                "function_call": response["choices"][0]["message"]["function_call"]
            }]    
            return response["choices"][0]["message"]
        
        self.prev_msgs += [{
            "role": "assistant",
            "content": response["choices"][0]["message"]["content"]
        }]

        return response["choices"][0]["message"]["content"]

    def add_function_response(self, function_name, response):
        self.prev_msgs += [{
            "role": "function",
            "name": function_name,
            "content": response
        }]

