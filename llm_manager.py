import os
import json
import openai
import asyncio
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
from llms.openairealtime import OpenaiRealtime
from llms.openairealorchestrator import OpenaiRealOrchestrator
from llms.azure_glean_orchestrator import GleanOrchestrator

class LLMManager:
    def __init__(self, config_path='llm_config.json'):
        # Load the environment variables
        load_dotenv('environment.env', override=True)
        
        # Load the LLM configuration from the JSON file
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.llms = {}
        self.llm_links = {}
        self.async_llms = set()  # Track which LLMs are async

        # Clean up existing assistants if needed
        self._cleanup_assistants()
        
        # Initialize LLMs
        self._initialize_llms(config)

    def _cleanup_assistants(self):
        # Handle OpenAI assistants cleanup
        if os.path.exists('openai_assistants.txt'):
            client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
            self._delete_assistants('openai_assistants.txt', client)

        # Handle Azure OpenAI assistants cleanup
        if os.path.exists('azure_openai_assistants.txt'):
            client = openai.AzureOpenAI(
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
                azure_endpoint=os.getenv('AZURE_OPENAI_API_ENDPOINT')
            )
            self._delete_assistants('azure_openai_assistants.txt', client)

    def _delete_assistants(self, file_path, client):
        with open(file_path, 'r') as f:
            assistant_ids = f.readlines()

        for assistant_id in assistant_ids:
            assistant_id = assistant_id.strip()
            try:
                response = client.beta.assistants.delete(assistant_id)
                if response.deleted:
                    print(f"Assistant {assistant_id} deleted.")
                else:
                    print(f"Assistant {assistant_id} not deleted.")
            except Exception as e:
                print(f"Error deleting Assistant {assistant_id}: {e}")

        os.remove(file_path)

    def _initialize_llms(self, config):
        for name, llm_config in config['llms'].items():
            class_name = llm_config['class']
            params = llm_config['params']
            
            # Replace environment variable placeholders with actual values
            for key, value in params.items():
                if value in os.environ:
                    params[key] = os.getenv(value)
            
            # Get the class reference
            llm_class = globals()[class_name]
            
            # Create instance and store it
            llm_instance = llm_class(**params)
            self.llms[name] = llm_instance
            self.llm_links[name] = params['info_link']
            
            # Track if this is an async LLM
            if class_name in ["OpenaiRealtime", "OpenaiRealOrchestrator"]:
                self.async_llms.add(name)

    async def get_llm_response(self, llm_name, user, prompt):
        """Get a response from an LLM, handling both sync and async LLMs."""
        llm = self.llms.get(llm_name)
        if not llm:
            return None
            
        if llm_name in self.async_llms:
            # Handle async LLM
            return await llm.generate(user, prompt)
        else:
            # Handle synchronous LLM
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, llm.generate, user, prompt)

    def get_llm(self, name):
        return self.llms.get(name)

    def get_available_llms(self):
        return list(self.llms.keys())

    def get_llm_links(self):
        return self.llm_links

    def _get_active_users(self):
        """Get a set of all active users across all LLMs"""
        active_users = set()
        
        for llm in self.llms.values():
            # Check conversation history
            if hasattr(llm, 'conversation_history'):
                active_users.update(llm.conversation_history.keys())
            
            # Check assistant threads
            if hasattr(llm, 'openai_assistant_thread'):
                active_users.update(llm.openai_assistant_thread.keys())
                
            # Check Azure assistant threads
            if hasattr(llm, 'azure_assistant_thread'):
                active_users.update(llm.azure_assistant_thread.keys())
                
        return active_users
