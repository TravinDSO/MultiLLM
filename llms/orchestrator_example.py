# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

import json
from llms.openaimulti import OpenaiMulti
from llms.tools.google_search import GoogleSearch

# Inherit from the OpenaiMulti class
class ExampleOrchestrator(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',wait_limit=300, type='chat',google_key="",google_cx=""):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)
        self.websearch = GoogleSearch(google_key,google_cx)
        self.instructions = "This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents"
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
                        "description": "Generate an image based on the prompt. Format the response in HTML to display the image."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "web_search",
                    "description": "Always search the web for real-time information that may not be available in the model. If you don't find what you need, try again.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Your search string to find information on the web. Use this information in your response and include links if needed."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            }
        ]

    # override the handle_tool method
    def handle_tool(self, user, tool):
        tool_name = tool.function.name
        args = json.loads(tool.function.arguments)
        if tool_name == "generate_image":
            results =  self.image_generate(user, args['prompt'])  # image gen is already part of the OpenaiMulti class
        elif tool_name == "web_search":
            top_result_link, page_text = self.websearch.search(args['prompt'])
            results = f'Top search result link: {top_result_link}\nPage text: {page_text}'
        else:
            results =  "Tool not supported"
        
        return results




# Test Cell
# Please do not modify
if __name__ == '__main__':
    try:
        #load the env file
        import os
        from dotenv import load_dotenv
        load_dotenv('environment.env', override=True)
        
        #gpt4o = OpenaiMulti(os.getenv('OPENAI_API_KEY'),os.getenv('OPENAI_ASSISTANT_ID'),type='assistant')
        gpt4o = ExampleOrchestrator(os.getenv('OPENAI_API_KEY'),type='assistant', google_key=os.getenv('GOOGLE_API_KEY'), google_cx=os.getenv('GOOGLE_CX'))

        response = gpt4o.generate('user','Did President Biden drop out of the 2024 election?')
        print(response)
        #response = gpt4o.generate('user','Why?')
        #print(response)
    except Exception as e:
        print(e)