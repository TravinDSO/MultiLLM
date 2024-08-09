import os
import json
import openai
from dotenv import load_dotenv

# Import LLM classes
from llms.openaimulti import OpenaiMulti
from llms.claudemulti import ClaudeMulti
from llms.ollamamulti import OllamaMulti
from llms.azuremulti import AzureMulti
from llms.openaiorchestrator import OpenaiOrchestrator
from llms.azureorchestrator import AzureOrchestrator
from llms.ollamaorchestrator import OllamaOrchestrator
from llms.aohybridorchestrator import AOHybridOrchestrator

class LLMManager:
    def __init__(self, config_path='llm_config.json'):
        # Load the environment variables
        load_dotenv('environment.env', override=True)
        
        # Load the LLM configuration from the JSON file
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.llms = {}
        self.llm_links = {}

        # Check if openai_assistants.txt exists and if so, iterate through the file and delete the assistants
        if os.path.exists('openai_assistants.txt'):
            client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
            with open('openai_assistants.txt', 'r') as f:
                # Read all lines (each line corresponds to an assistant ID)
                assistant_ids = f.readlines()

            for assistant_id in assistant_ids:
                assistant_id = assistant_id.strip()  # Remove any trailing newline characters
                try:
                    response = client.beta.assistants.delete(assistant_id)
                    if response.deleted:
                        print(f"Assistant {assistant_id} deleted.")
                    else:
                        print(f"Assistant {assistant_id} not deleted.")
                except Exception as e:
                    print(f"Error deleting Assistant {assistant_id}: {e}")

            # Once all assistants are deleted, remove the openai_assistants.txt file
            os.remove('openai_assistants.txt')

        # Check if azure_openai_assistants.txt exists and if so, iterate through the file and delete the assistants
        if os.path.exists('azure_openai_assistants.txt'):
            client = openai.AzureOpenAI(
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
                azure_endpoint=os.getenv('AZURE_OPENAI_API_ENDPOINT')
            )
            with open('azure_openai_assistants.txt', 'r') as f:
                # Read all lines (each line corresponds to an assistant ID)
                assistant_ids = f.readlines()

            for assistant_id in assistant_ids:
                assistant_id = assistant_id.strip()  # Remove any trailing newline characters
                try:
                    response = client.beta.assistants.delete(assistant_id)
                    if response.deleted:
                        print(f"Assistant {assistant_id} deleted.")
                    else:
                        print(f"Assistant {assistant_id} not deleted.")
                except Exception as e:
                    print(f"Error deleting Assistant {assistant_id}: {e}")

            # Once all assistants are deleted, remove the azure_openai_assistants.txt file
            os.remove('azure_openai_assistants.txt')

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
