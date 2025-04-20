from llama_cpp import Llama
import os


class TinyLlama:
    __model = os.path.join(os.getcwd(), "core", "llm", "tinyllama", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    
    def __init__(self):
        self.llm = Llama(model_path=self.__model, 
                         n_ctx=2048, 
                         n_threads=4, 
                         n_gpu_layers=20)
        
    def __call__(self, prompt):
        return self.llm(prompt,
                        max_tokens=1024,
                        temperature=0.7, # This is optional but useful
                        echo=False )
    
    def __str__(self):
        return "TinyLlama\nType: 1.1b-chat\nVersion: v1.0.Q4_K_M\nContext: 2048\nThreads: 4"