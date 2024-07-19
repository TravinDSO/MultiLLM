# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

from openaimulti import OpenaiMulti

# Inherit from the OpenaiMulti class
class exampleOrchestrator(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',wait_limit=300, type='chat'):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)
        self.tools = [
            {
            "type": "function",
            "function": {
                "name": "generate_image",
                "description": "Generate and image if needed",
                "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                    "type": "string",
                    "description": "Generate an image based on the prompt"
                    }
                },
                "required": ["prompt"]
                }
            }
            }
        ]


# Test Cell
# Please do not modify
if __name__ == '__main__':
    try:
        #load the env file
        import os
        from dotenv import load_dotenv
        load_dotenv('environment.env', override=True)
        
        #gpt4o = OpenaiMulti(os.getenv('OPENAI_API_KEY'),os.getenv('OPENAI_ASSISTANT_ID'),type='assistant')
        gpt4o = exampleOrchestrator(os.getenv('OPENAI_API_KEY'),type='assistant')

        response = gpt4o.generate('user','1+1?')
        print(response)
        #response = gpt4o.generate('user','Why?')
        #print(response)
    except Exception as e:
        print(e)