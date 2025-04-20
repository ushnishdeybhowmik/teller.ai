from openai import OpenAI
from dotenv import load_dotenv
import os

class GPT:
    def __init__(self):
        env_path = os.path.join(os.getcwd(), ".env")
        load_dotenv(env_path)
        self.__client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 
        
    def __get_openai_response(self, query: str):
        try:
            response = self.__client.chat.completions.create(
                model="gpt-3.5-turbo",  # or "gpt-4" if you upgrade
                messages=[
                    {"role": "system", "content": "You are a helpful banking assistant."},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error: {e}"
        
    def __call__(self, prompt):
        return self.__get_openai_response(prompt)
    
    def __str__(self):
        return "GPT"
        