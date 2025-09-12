import re
import json
import ollama

class OLLAMA_APP:
    def __init__(self, model):
        self.model = model
                                
    def request(self, payload, path=None):
      
        msg = dict()
        msg["role"] = "user"
        msg["content"] = f"{payload}"
        
        if path is not None: msg["images"] = [f"./{path}"]
        

        res = ollama.chat(
            model=self.model,
            messages=[msg],
            format="json" 
        )

        return json.loads(res["message"]["content"])
        