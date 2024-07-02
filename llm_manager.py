import os
from dotenv import load_dotenv
from llms.gpt4o import GPT4o
from llms.claude35 import Claude35

# Temporarily disabled
#from llms.ollama_gemma2_9b import Gemma2_9b
#from llms.ollama_gemma2_27b import Gemma2_27b

class LLMManager:
    def __init__(self):
        
        #load the env file
        load_dotenv('environment.env', override=True)
        
        self.llms = {
            'GPT4o': GPT4o(os.getenv('OPENAI_API_KEY'),os.getenv('OPENAI_ASSISTANT_ID')),
            'Claude 3.5': Claude35(os.getenv('CLAUDE_API_KEY'))
        }
        # Temporarily disabled
        #'Gemma2': Gemma2_9b(os.getenv('GEMMA2_API_BASE_URL'))
        #'Gemma2 27b': Gemma2_27b(os.getenv('GEMMA2_API_BASE_URL'))

        self.llm_links = {
            'GPT4o': self.llms['GPT4o'].info_link,
            'Claude 3.5': self.llms['Claude 3.5'].info_link
        }
        # Temporarily disabled
        #'Gemma2': Gemma2_9b.info_link,
        #'Gemma2 27b': Gemma2_27b.info_link

    def get_llm(self, name):
        return self.llms.get(name)

    def get_available_llms(self):
        return list(self.llms.keys())
    
    def get_llm_links(self):
        return self.llm_links