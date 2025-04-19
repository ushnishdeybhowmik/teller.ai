from llama_cpp import Llama
import os


class Mistral:
    __model = os.path.join(os.getcwd(), "core", "llm", "mistral", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    
    def __init__(self):
        self.llm = Llama(model_path=self.__model, n_ctx=2048, n_threads=6)
        
    def __call__(self, prompt):
        return self.llm(prompt)
    
    def __str__(self):
        return "Mistral\nType: 7b-instruct\nVersion: v0.2.Q4_K_M\nContext: 2048\nThreads: 6"
    
    
    

