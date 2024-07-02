import os
from dotenv import load_dotenv
from llms.gpt4o import GPT4o
from llms.claude35 import Claude35
from llms.ollama_gemma2_27b import Gemma2_27b
from llms.ollama_codelamma_34b import Codelamma_34b
from llms.ollama_codeqwen_7b import Codeqwen_7b
from llms.ollama_codegemma_7b import Codegemma_7b

class LLMManager:
    def __init__(self):
        
        #load the env file
        load_dotenv('environment.env', override=True)
        
        self.llms = {
            'GPT4o': GPT4o(os.getenv('OPENAI_API_KEY'),os.getenv('OPENAI_ASSISTANT_ID')),
            'Claude 3.5': Claude35(os.getenv('CLAUDE_API_KEY')),
            'Gemma2 27b (local)': Gemma2_27b(os.getenv('GEMMA2_API_BASE_URL')),
            'Codelamma 34b (local)': Codelamma_34b(os.getenv('GEMMA2_API_BASE_URL')),
            'Codeqwen 7b (local)': Codeqwen_7b(os.getenv('GEMMA2_API_BASE_URL')),
            'Codegemma 7b (local)': Codegemma_7b(os.getenv('GEMMA2_API_BASE_URL'))
        }

        self.llm_links = {
            'GPT4o': self.llms['GPT4o'].info_link,
            'Claude 3.5': self.llms['Claude 3.5'].info_link,
            'Gemma2 27b (local)': self.llms['Gemma2 27b (local)'].info_link,
            'Codelamma 34b (local)': self.llms['Codelamma 34b (local)'].info_link,
            'Codeqwen 7b (local)': self.llms['Codeqwen 7b (local)'].info_link,
            'Codegemma 7b (local)': self.llms['Codegemma 7b (local)'].info_link
        }

    def get_llm(self, name):
        return self.llms.get(name)

    def get_available_llms(self):
        return list(self.llms.keys())
    
    def get_llm_links(self):
        return self.llm_links