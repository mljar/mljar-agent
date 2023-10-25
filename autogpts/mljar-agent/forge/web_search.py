import os
import datetime
import requests
from html2text import HTML2Text
from bs4 import BeautifulSoup

from forge.chatgpt import ChatGPT, num_tokens_from_string
from forge.get_website import get_website_text as get_website


def generate_search_engine_query(task, search_goal, query):
    return f"""Your task is:

{task}

Your search goal:

{search_goal}

Initial query is:

{query}

Current date is {str(datetime.datetime.now())}

INSTRUCTIONS

Propose 3 search phrases for searching web with Google Search.

Propose 1 search pharse for search in Wikipedia.

Make queries diverse.

Return ONLY search queries in format:

1. First query up to 5 words
2. Second query up to 10 words
3. Third query up to 3 words, different from first and second query
4. Wikipedia fourth query. Add Wikipedia at the beginning of query
"""

def analyze_search_result(task, search_goal, query, result): 
    return f"""Your task is:

{task}

Your search goal is:

{search_goal}

Query:

{query}

Web search results:

{result}

INSTRUCTIONS

Based on web search results, please provide answer to query.
"""

def compress_responses(task, search_goal, query, resp):
    return f"""Your task is:

{task}

Your search goal is:

{search_goal}

Query:

{query}

Web search results with different queries:

{resp}

INSTRUCTIONS

Please provide final answer. Please include your thoughts in up to 100 words.

Display final answer that generalize from previous responses.
"""     


class WebSearch():
    
    def __init__(self, task, search_goal, query, mem):
        self.task = task
        self.search_goal = search_goal
        self.query = query
        self.mem = mem
        self.search_agent = ChatGPT()
        self.checked_addresses = []
    
    def what_are_you_doing(self):
        return "I'm searching the internet and store information in local memory"
    
    def what_did_you_do(self):
        return "I've searched the internet"
    
    def do_scrapingbee_search(self, query, limit=5):
        
        if os.environ.get("SCRAPINGBEE_API_KEY") is None:
            print()
            print("IMPORTANT")
            print()
            print("Please set SCRAPINGBEE_API_KEY environment variable")
            print()
            return []

        response = requests.get(
            url="https://app.scrapingbee.com/api/v1/store/google",
            params={
                "api_key": os.environ.get("SCRAPINGBEE_API_KEY"),
                "search": query,
                "nb_results": limit
            },
        )
        links = []
        for r in response.json()["organic_results"]:
            links += [r["url"]]
        return links
    
    def do_google_search(self, query, limit=5):

        params = {
            "q": query,
            "hl": "en",
            "gl": "usa",
            "start": 0,
            "num": limit
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
        html = requests.get("https://www.google.com/search", params=params, headers=headers, timeout=30)
        
        links = []
        if html.status_code == 200:
            soup = BeautifulSoup(html.text, "html.parser")
            for el in soup.find_all("span"): 
                h3 = el.find_all("h3")
                a = el.find_all("a")
                if len(h3) == 1 and len(a) == 1:
                    links += [a[0]["href"]]
        return links


    def do_bing_search(self, query, limit=5):
        params = {
            "q": query,
            "setlang": "en",
            "cc": "us"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
        html = requests.get("https://bing.com/search", params=params, timeout=30)
        
        h = HTML2Text()
        h.ignore_links=True
        h.ignore_images=True
        #print(h.handle(html.text))
        
        soup = BeautifulSoup(html.text, "html.parser")
        #print(soup)
        links = []
        for el in soup.find_all("h2"): 
            #print(el)
            a = el.find_all("a")
            
            if len(a):
                links += [a[0]["href"]]
            #print(links)
        return links[:limit]
        
    def do_ddg_search(self, query, limit=5):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        }
        html = requests.post("https://html.duckduckgo.com/html", data={"q": query}, headers=headers)
        links = []
        soup = BeautifulSoup(html.text, "html.parser")
        for el in soup.find_all("h2"): 
            #print(el)
            a = el.find_all("a")
            
            if len(a):
                links += [a[0]["href"]]
            #print(links)
        return links[:limit]
    
    def run(self):
        prompt_generate_query = generate_search_engine_query(self.task, self.search_goal, self.query)
        queries_response = self.search_agent.chat(prompt_generate_query, use_prev_msgs=False, model="gpt-4")
        print("Queries", queries_response.split("\n"))
        first_query = None
        for q in queries_response.split("\n"):
            if q.startswith("1. ") or q.startswith("2. ") or q.startswith("3. ") or q.startswith("4. "):
                query = q[3:].replace('"', '')
                print("🔎 Query", query)
                if first_query is None:
                    first_query = query
                links = []
                links = self.do_google_search(query, limit=1)
                if len(links) == 0:
                    links += self.do_scrapingbee_search(query, limit=1)
                if len(links) == 0:
                    links += self.do_bing_search(query, limit=1)
                if len(links) == 0:
                    links += self.do_ddg_search(query, limit=1)
                
                if len(links) == 0 and len(self.checked_addresses) == 0:
                    print("Cant do web search")
                    return "Cant do web search"
                
                for link in links[:1]:
                    if link not in self.checked_addresses:
                        print(f"🌐 Get website {link}")
                        content = get_website(link)
                        self.mem.add(content, source=link)
                        self.checked_addresses += [link]
        

        results = self.mem.search(self.task + " " + self.search_goal + " " + first_query, limit=3)

        responses = []
        for result in results:
            analyze_prompt = analyze_search_result(self.task, self.search_goal, self.query, result)
            print("📖 Summarize search result")
            print(result)
            responses += [ChatGPT().chat(analyze_prompt, model="gpt-4")] # with gpt-4 results might be better
            print("🤔 Agent summary")
            print(responses[-1])
            
        resp = ""
        for j, r in enumerate(responses):
            resp += f"{j+1}. {r}\n"
        compress_prompt = compress_responses(self.task, self.search_goal, self.query, resp)
        response = ChatGPT().chat(compress_prompt, model="gpt-4")
        print("🤔 All responses")
        print(resp)
        print("🤓 Final answer")
        print(response)

        return response


if __name__ == "__main__":
    from localmem import LocalMem
    #query = "Tesla revenue in 2022"
    #search_goal = "Find information about Tesla's revenue in 2022"
    query = "Tesla revenue by year"
    search_goal = "Find reliable sources for Tesla's revenue by year"
    task = "Write tesla's revenue every year since its creation into a .txt file. Use the US notation, with a precision rounded to the nearest million dollars (for instance, $31,578 million)."
    mem = LocalMem()

    gs = WebSearch(task, search_goal, query, mem)
    #gs.run()

    gs.do_google_search(query="AutoGPT creator")