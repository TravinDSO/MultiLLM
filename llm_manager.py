import os
import json
import openai
from dotenv import load_dotenv

# Import LLM classes
from llms.openaimulti import OpenaiMulti
from llms.claudemulti import ClaudeMulti
from llms.ollamamulti import OllamaMulti
from llms.azuremulti import AzureMulti

class LLMManager:
    def __init__(self, config_path='llm_config.json'):
        # Load the environment variables
        load_dotenv('environment.env', override=True)
        
        # Load the LLM configuration from the JSON file
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.llms = {}
        self.llm_links = {}

        # Check if openai_assistants.json exists and if so, itterate through the file and delete the assistants
        if os.path.exists('openai_assistants.json'):
            client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
            with open('openai_assistants.json', 'r') as f:
                try:
                    assistants = json.load(f)
                except:
                    assistants = []
            for assistant in assistants:
                try:
                    response = client.beta.assistants.delete(assistants[assistant])
                    if response.deleted == True:
                        print(f"Assistant {assistants[assistant]} deleted.")
                    else:
                        print(f"Assistant {assistants[assistant]} not deleted.")
                    # Delete the openai_assistants.json file
                    os.remove('openai_assistants.json')
                except Exception as e:
                    print(e)

        # Dynamically instantiate LLM objects based on the configuration
        for name, llm_config in config['llms'].items():
            class_name = llm_config['class']
            params = llm_config['params']
            
            # Replace environment variable placeholders with actual values
            for key, value in params.items():
                if value in os.environ:
                    params[key] = os.getenv(value)
            
            # Dynamically get the class reference
            llm_class = globals()[class_name]
            self.llms[name] = llm_class(**params)
            self.llm_links[name] = params['info_link']

    def get_llm(self, name):
        return self.llms.get(name)

    def get_available_llms(self):
        return list(self.llms.keys())

    def get_llm_links(self):
        return self.llm_links
