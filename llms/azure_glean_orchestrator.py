# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

import json
import datetime
from llms.azuremulti import AzureMulti
from llms.tools.glean_search import GleanSearch
from llms.tools.weather import WeatherChecker

# Inherit from the OpenaiMulti class
class GleanOrchestrator(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',
                 info_link='',type='assistant', wait_limit=300,agent_name="Glean Orchestrator",
                 glean_token="",glean_api_url="",openweathermap_key=""):
        # Call the parent class constructor
        super().__init__(api_key,model=model,endpoint=endpoint,version=version,
                         info_link=info_link,wait_limit=wait_limit,type=type,agent_name=agent_name)

        #Agents
        self.azure_agent = AzureMulti(api_key=api_key,model=model,endpoint=endpoint,version=version,type='assistant',agent_name='Azure Assistant')
        self.glean_search = GleanSearch(glean_api_url,glean_token)
        self.weather_checker = WeatherChecker(openweathermap_key)

        # Response token size for agents
        self.azure_agent.token_run_size = 3000

        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        Use the get_weather and get_forcast tools to check the current weather, temperature and forecast for a location.
        Unless specifically directed, always use the company_knowledgebase_search tool to search the company knowledgebase for information.
        If the company knowledgebase does not have the information you need or there is ambiguity in the information, use the web_search tool to augment your search.
        Always include supporting URLs in your response.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Images responses should be formatted in HTML to display the image. Example: <img src="https://www.example.com/image.jpg" alt="image">
        For all tools, wait for the response before continuing to the next tool.
        For all tools, you should ask follow-up questions to get more information if needed.
        """

        # Localized instructions for the orchestrator
        self.agent_instructions += """
        All times should be converted to Eastern time. If a time or date specific question is asked to and agent, ensure they know the time zone is Eastern.
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
            },
            {
            "type": "function",
            "function": {
                    "name": "company_knowledgebase_search",
                    "description": "Search the company knowledgebase for information.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "The prompt to search the company knowledgebase for information."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },
            {
            "type": "function",
            "function": {
                    "name": "web_search",
                    "description": "Search the web for information.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "The prompt to search the web for information."
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
        results = ""
        if tool_name == "generate_image":
            self.extra_messages[user].append(f'<HR><i>Generating image using this prompt: {args["prompt"]}</i>')
            results = self.image_gen_tool.image_generate(prompt=args['prompt']) # image gen is already part of the AzureMulti class
        elif tool_name == "get_weather":
            self.extra_messages[user].append(f'<HR><i>Getting the weather for latitude: {args["latitude"]} and longitude: {args["longitude"]}</i>')
            results = json.dumps(self.weather_checker.get_weather(args['latitude'], args['longitude']))
        elif tool_name == "get_forecast":
            self.extra_messages[user].append(f'<HR><i>Getting the forecast for latitude: {args["latitude"]} and longitude: {args["longitude"]}</i>')
            results = json.dumps(self.weather_checker.get_forecast(args['latitude'], args['longitude']))
        elif tool_name == "date_time":
            self.extra_messages[user].append(f'<HR><i>Getting the current date and time</i>')
            results = f"The current date and time is: {datetime.datetime.now()}"
        elif tool_name == "company_knowledgebase_search":
            # example: results = glean_search.chat([{"role": "user", "content": "What is Project Management?"}], agent="DEFAULT")
            self.extra_messages[user].append(f'<HR><i>Searching the company knowledgebase for information: {args["prompt"]}</i>')
            response = self.glean_search.chat([{"role": "user", "content": args["prompt"]}], agent="DEFAULT")
            for result in response:
                results += result
        elif tool_name == "web_search":
            # example: results = glean_search.chat([{"role": "user", "content": "What is Project Management?"}], agent="GPT")
            self.extra_messages[user].append(f'<HR><i>Searching the web for information: {args["prompt"]}</i>') 
            response = self.glean_search.chat([{"role": "user", "content": args["prompt"]}], agent="GPT")
            for result in response:
                results += result
        else:
            results =  "Tool not supported"
        return results
    
    # Override and run the clear_conversation method
    def clear_conversation(self, user):
        super().clear_conversation(user)
        self.azure_agent.clear_conversation(user)
        return "Conversation cleared"