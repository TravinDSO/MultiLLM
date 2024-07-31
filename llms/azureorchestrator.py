# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

import json
import datetime
from llms.azuremulti import AzureMulti
from llms.ollamamulti import OllamaMulti
from llms.agents.confluence_agent import AzureConfluenceAgent
from llms.agents.jira_agent import AzureJiraAgent
from llms.agents.websearch_agent import AzureWebsearchAgent
from llms.tools.weather import WeatherChecker

# Inherit from the OpenaiMulti class
class AzureOrchestrator(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',info_link='',type='assistant', wait_limit=300,
                 google_key="",google_cx="",confluence_url="",confluence_token="",
                 jira_url="",jira_token="",openweathermap_key=""):
        # Call the parent class constructor
        super().__init__(api_key,model,endpoint,version,info_link,wait_limit,type)

        #Agents
        self.azure_agent = AzureMulti(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant')
        self.confluence_agent = AzureConfluenceAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant',confluence_url=confluence_url,confluence_token=confluence_token)
        self.jira_agent = AzureJiraAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant',jira_url=jira_url,jira_token=jira_token)
        self.websearch_agent = AzureWebsearchAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant',google_key=google_key,google_cx=google_cx)
        self.math_agent = OllamaMulti('llama3.1:latest')
        self.weather_checker = WeatherChecker(openweathermap_key)

        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        Use the get_weather and get_forcast tools to check the current weather, temperature and forecast for a location.
        Use the agent_websearch tool to find real-time information that may not be available in the model.
        If someone asks for information from the Wiki or Confluence, you should as the agent_confluence tool.
        If someone asks for information from JIRA, you should use the agent_jira tool.
        If someone asks a business question, the agent_jira and agent_confluence tools should be asked as well.
        Always include supporting URLs in your response.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Images responses should be formatted in HTML to display the image. Example: <img src="https://www.example.com/image.jpg" alt="image">
        Use the agent_mathmatician tool when attempting to solve mathmatical or logical problems. Include all supporting information in the prompt.
        Use the agent_researcher tool when attempting to respond to highly factual or technical prompts. This tool will provide you with feedback to improve your response.
        The agent_writer tool can be used to enhance your response with professional writing skills.
        For all tools, you should ask follow-up questions to get more information if needed.
        """

        # Default tools available through the native orchestrator
        self.tools = [
            {
            "type": "function",
            "function": {
                    "name": "date_time",
                    "description": "Obtain the current date and time."
                }
            },{
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
                    "name": "get_weather",
                    "description": "Check the current weather for a location.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                        "type": "string",
                        "description": "The latitude decimal (-90; 90) of the location to check the current weather."
                        },
                        "longitude": {
                        "type": "string",
                        "description": "The longitude decimal (-180; 180) of the location to check the current weather."
                        }
                    },
                    "required": ["latitude" , "longitude"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "get_forecast",
                    "description": "Check the weather forecast for a location.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                        "type": "string",
                        "description": "The latitude decimal (-90; 90) of the location to check the weather forecast."
                        },
                        "longitude": {
                        "type": "string",
                        "description": "The longitude decimal (-180; 180) of the location to check the weather forecast."
                        }
                    },
                    "required": ["latitude" , "longitude"]
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
            },{
            "type": "function",
            "function": {
                    "name": "agent_confluence",
                    "description": "Use this agent to assist in finding information on Confluence. Include supporting information if nessesary.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Prompt, asking the agent to search Confluence for information related to the user's question/problem."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "agent_jira",
                    "description": "Use this agent to assist in finding information on JIRA. Include supporting information if nessesary.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Prompt, asking the agent to search JIRA for information related to the user's question/problem."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "agent_websearch",
                    "description": "Use this agent to search websites for more current or realtime information. Include supporting information if nessesary.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Prompt, asking the agent to search the web for information related to the user's question/problem."
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
        elif tool_name == "get_weather":
            if debug: print(f"Getting the weather")
            results = json.dumps(self.weather_checker.get_weather(args['latitude'], args['longitude']))
        elif tool_name == "get_forecast":
            if debug: print(f"Getting the weather forecast")
            results = json.dumps(self.weather_checker.get_forecast(args['latitude'], args['longitude']))
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
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
        elif tool_name == "agent_confluence":
            if debug: print(f"Asking the Agent Confluence (Azure)")
            results = self.confluence_agent.generate(user, args['prompt'])
        elif tool_name == "agent_jira":
            if debug: print(f"Asking the Agent JIRA (Azure)")
            results = self.jira_agent.generate(user, args['prompt'])
        elif tool_name == "agent_websearch":
            if debug: print(f"Asking the Agent Websearcher (Azure)")
            results = self.websearch_agent.generate(user, args['prompt'])
        else:
            results =  "Tool not supported"
        
        return results
    
    # Override and run the clear_conversation method
    def clear_conversation(self, user):
        super().clear_conversation(user)
        self.azure_agent.clear_conversation(user)
        self.confluence_agent.clear_conversation(user)
        self.jira_agent.clear_conversation(user)
        self.websearch_agent.clear_conversation(user)
        self.math_agent.clear_conversation(user)
        return "Conversation cleared"