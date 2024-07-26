# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

import json
from llms.openaimulti import OpenaiMulti
from llms.claudemulti import ClaudeMulti
from llms.ollamamulti import OllamaMulti
from llms.tools.google_search import GoogleSearch

# Inherit from the OpenaiMulti class
class ExampleOrchestrator(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',wait_limit=300, type='chat',google_key="",google_cx="",claude_key=""):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)
        self.websearch = GoogleSearch(google_key,google_cx)

        #Agents
        self.claude_agent = ClaudeMulti(claude_key)
        self.math_agent = OllamaMulti('llama3.1:latest')

        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        You will always make use of the web_search tool to find real-time information that may not be available in the model.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Images responses should be formatted in HTML to display the image. Example: <img src="https://www.example.com/image.jpg" alt="image">
        Use the agent_mathmatician tool when attempting to solve mathmatical or logical problems. Include all supporting information in the prompt.
        Use the agent_researcher tool when attempting to respond to highly factual or technical prompts. This tool will provide you with feedback to improve your response.
        All final responses should flow through the agent_writer tool to generate a response.
        """
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
                        "description": "Your search string to find information on the web. Use this information in your response."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "agent_writer",
                    "description": "Use the Claude API to take all of the information you have gathered and write a response.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "All of the information you have gathered to write a response and instructions on what to do with it."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "agent_researcher",
                    "description": "Use the Claude API as a researcher and analyist to check facts, provide information and feedback to improve your response.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Information to research and analize, providing feedback to improve your response."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "agent_mathmatician",
                    "description": "For mathmatical or logical problems, use this agent to assist in solving the question. Include supporting information if nessesary.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Problem and information to use in solving the question, providing detail data to improve your response."
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
        debug = True # Set to True to print debug information
        args = json.loads(tool.function.arguments)
        if tool_name == "generate_image":
            results =  self.image_generate(user, args['prompt'])  # image gen is already part of the OpenaiMulti class
            if debug: print(f"Generating an image (dall-e-3)")
        elif tool_name == "web_search":
            top_result_link, page_text = self.websearch.search(args['prompt'])
            results = f'Top search result link: {top_result_link}\nPage text: {page_text}'
            if debug: print(f"Searching the web (Google)")
        elif tool_name == "agent_writer":
            if debug: print(f"Asking the Agent Writer (Claude)")
            self.claude_agent.agent_instructions = "You are a professional writer. Use the information and instructions provided to write a response."
            results = self.claude_agent.generate(user, args['prompt'])
        elif tool_name == "agent_researcher":
            if debug: print(f"Asking the Agent Researcher (Claude)")
            self.claude_agent.agent_instructions = "You are a professional researcher and analyist. Use the information and instructions provided to research and provide feedback."
            results = self.claude_agent.generate(user, args['prompt'])
        elif tool_name == "agent_mathmatician":
            if debug: print(f"Asking the Agent Mathmatician (Local: Llama3.1 7b)")
            results = self.math_agent.generate(user, args['prompt'])
        else:
            results =  "Tool not supported"
        
        return results