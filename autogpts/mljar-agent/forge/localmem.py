import os
import weaviate
from forge.chatgpt import num_tokens_from_string


class LocalMem():
    
    def __init__(self):
        self.client = weaviate.Client(
            embedded_options=weaviate.embedded.EmbeddedOptions(),
            additional_headers={
            "X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY", "")
          }
        )
        self.client.schema.delete_all()
        schema = {
           "classes": [
               {
                   "class": "LocalMem",
                   "description": "LocalMem",
                   "vectorizer": "text2vec-openai",
                   "moduleConfig": {
                       "text2vec-openai": { 
                            "model": "ada",
                            "modelVersion": "002",
                            "type": "text"
                        }
                   },
                   "properties": [
                       {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "Content chunks",
                       },
                       {
                        "name": "source",
                        "dataType": ["text"],
                        "description": "Content source",
                       }
                    ]
                }
            ]
        }
        self.client.schema.create(schema)

    def split_please(self, tmp):
        tokens = num_tokens_from_string(tmp)
        chunks = []
        if tokens < 1000:
            chunks += [tmp]
        else:
            a = tmp.split(" ")
            steps = len(a) // 1000 +1
            for s in range(steps):
                start = s*1000
                end = min(len(a), start + 1000)
                chunks += [" ".join(a[start:end])]
        return chunks
    
        
    def add(self, content, source):
        parts = 0
        chunks = []
        tmp = ""
        for l in content.split("\n"):
            #print(l)
            if l.startswith("## ") or l.startswith("### "):
                
                tokens = num_tokens_from_string(tmp)
                #print(parts, tokens)
                if tokens > 100:

                    if tokens < 1000:
                        parts += 1
                        chunks += [tmp]
                        #print(l)
                        tmp = ""
                    else:
                        a = tmp.split(" ")
                        #print(len(a))
                        steps = len(a) // 1000 +1
                        #print("steps", steps)
                        for s in range(steps):
                            start = s*1000
                            end = min(len(a), start + 1000)
                            #print(s, start, end)
                            parts += 1
                            chunks += [" ".join(a[start:end])]
                        #print(l)
                        tmp = ""


            tmp += l+"\n"
        if tmp != "":
            chunks += self.split_please(tmp)
            
        chunks_1k = []
        for chunk in chunks:
            tokens = num_tokens_from_string(chunk)
            if tokens < 1500:
                chunks_1k += [chunk]
            else:
                a = chunk.split(" ")
                if len(a) > 1:
                    steps = len(a) // 500 +1
                    for s in range(steps):
                        start = s*500
                        end = min(len(a), start + 500)
                        chunks_1k += [" ".join(a[start:end])]
        
        chunks = chunks_1k
            
        #print(f"{len(chunks)} new chunks")
        with self.client.batch as batch:
            for content in chunks:
                tokens = num_tokens_from_string(content)
                if tokens < 3000 and content != "" and tokens > 3:
                    self.client.batch.add_data_object({"content": content, "source": source}, "LocalMem")
                    #print(f"Add chunk with {tokens} tokens")
                
    def search(self, query, limit=3):
        
        try:
            response = (
                self.client.query
                .get("LocalMem", ["content", "source"])
                .with_near_text({
                    "concepts": [query]
                })
                .with_limit(limit) 
                .do()
            )
            return ["Source: " + c["source"] + "\n\nContent:\n" + c["content"] for c in response["data"]["Get"]["LocalMem"] if c["content"] != ""]
        except Exception as e:
            pass
        return []