# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

import json
from llms.azuremulti import AzureMulti
from llms.claudemulti import ClaudeMulti
from llms.ollamamulti import OllamaMulti
from llms.tools.google_search import GoogleSearch
from llms.tools.confluence_search import ConfluenceSearch

# Inherit from the OpenaiMulti class
class AzureOrchestrator(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',info_link='',type='assistant',
                 wait_limit=300,google_key="",google_cx="",confluence_url="",confluence_token=""):
        # Call the parent class constructor
        super().__init__(api_key,model,endpoint,version,info_link,wait_limit,type)

        # Tools
        self.websearch = GoogleSearch(google_key,google_cx)
        self.confluence_search = ConfluenceSearch(confluence_url, confluence_token)

        #Agents
        self.azure_agent = AzureMulti(api_key,model,endpoint,version,info_link,wait_limit,type)
        self.math_agent = OllamaMulti('llama3.1:latest')

        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        You will always make use of the web_search tool to find real-time information that may not be available in the model.
        If someone asks for information from the Wiki or Confluence, you should use the confluence_search tool. The confluence_search tool also contains information relating to the our business, Cvent.
        For both web_search and confluence_search, you may also ask follow-up questions to get more information.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Images responses should be formatted in HTML to display the image. Example: <img src="https://www.example.com/image.jpg" alt="image">
        Use the agent_mathmatician tool when attempting to solve mathmatical or logical problems. Include all supporting information in the prompt.
        Use the agent_researcher tool when attempting to respond to highly factual or technical prompts. This tool will provide you with feedback to improve your response.
        All final responses should flow through the agent_writer tool to generate a response.
        """
        # Default tools available through the native orchestrator
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
            }
        ]

        # Additional tools created for the orchestrator
        self.tools += [
            {
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
                    "name": "confluence_search",
                    "description": "Search the Atlassian Confluence system for information. If you don't find what you need, try again.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Your search string to find information from Atlassian Confluence. Use this information in your response."
                        }
                    },
                    "required": ["prompt"]
                    }
                } 
            }
        ]

        # Agents available to the orchestrator
        self.tools += [
            {
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
            if debug: print(f"Generating an image (dall-e-3)")
            results =  self.image_generate(user, args['prompt'])  # image gen is already part of the OpenaiMulti class
        elif tool_name == "web_search":
            if debug: print(f"Searching the web (Google): {args['prompt']}")
            web_info = ""
            web_data = self.websearch.search(args['prompt'], num_results=3)
            if web_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for link, page_text in web_data:
                    #append the link and page test
                    web_info += f"Link: {link}\nPage Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{web_info}'
        elif tool_name == "confluence_search":
            if debug: print(f"Searching the Wiki (Confluence): {args['prompt']}")
            confluence_info = ""
            confluence_data = self.confluence_search.search(args['prompt'], num_results=10)
            if confluence_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for page_text in confluence_data:
                    #append the link and page test
                    confluence_info += f"Page Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{confluence_info}'
        elif tool_name == "agent_writer":
            if debug: print(f"Asking the Agent Writer (Azure)")
            self.azure_agent.agent_instructions = "You are a professional writer. Use the information and instructions provided to write a response."
            results = self.azure_agent.generate(user, args['prompt'])
        elif tool_name == "agent_researcher":
            if debug: print(f"Asking the Agent Researcher (Azure)")
            self.azure_agent.agent_instructions = "You are a professional researcher and analyist. Use the information and instructions provided to research and provide feedback."
            results = self.azure_agent.generate(user, args['prompt'])
        elif tool_name == "agent_mathmatician":
            if debug: print(f"Asking the Agent Mathmatician (Local: Llama3.1 7b)")
            results = self.math_agent.generate(user, args['prompt'])
        else:
            results =  "Tool not supported"
        
        return results