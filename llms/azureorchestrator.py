# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

import json
import datetime
from llms.azuremulti import AzureMulti
from llms.ollamamulti import OllamaMulti
from llms.agents.confluence_agent import AzureConfluenceAgent
from llms.agents.jira_agent import AzureJiraAgent
from llms.agents.websearch_agent import AzureWebsearchAgent
from llms.agents.mail_agent import AzureMailAgent
from llms.agents.calendar_agent import AzureCalAgent
from llms.agents.quantive_agent import AzureQuantiveAgent
from llms.tools.weather import WeatherChecker

# Inherit from the OpenaiMulti class
class AzureOrchestrator(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',
                 api_key_2='',model_2='',endpoint_2='',version_2='',
                 info_link='',type='assistant', wait_limit=300,
                 google_key="",google_cx="",quantive_url="",quantive_key="",quantive_account_id="",
                 confluence_url="",confluence_token="",
                 jira_url="",jira_token="",openweathermap_key=""):
        # Call the parent class constructor
        super().__init__(api_key,model=model,endpoint=endpoint,version=version,
                         api_key_2=api_key_2,model_2=model_2,endpoint_2=endpoint_2,version_2=version_2,
                         info_link=info_link,wait_limit=wait_limit,type=type)

        #Agents
        self.azure_agent = AzureMulti(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant')
        self.confluence_agent = AzureConfluenceAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant',confluence_url=confluence_url,confluence_token=confluence_token)
        self.jira_agent = AzureJiraAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant',jira_url=jira_url,jira_token=jira_token)
        self.quantive_agent = AzureQuantiveAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant',quantive_url=quantive_url,quantive_key=quantive_key,quantive_account_id=quantive_account_id,confluence_url=confluence_url,confluence_token=confluence_token,jira_url=jira_url,jira_token=jira_token)
        self.websearch_agent = AzureWebsearchAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant',google_key=google_key,google_cx=google_cx)
        self.mail_agent = AzureMailAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant')
        self.tasks_agent = AzureCalAgent(api_key=api_key,model=model,endpoint=endpoint,version=version,type = 'assistant')
        self.math_agent = OllamaMulti('llama3.1:latest')
        self.weather_checker = WeatherChecker(openweathermap_key)

        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        Use the get_weather and get_forcast tools to check the current weather, temperature and forecast for a location.
        Use the agent_websearch tool to find real-time information that may not be available in the model.
        Use the agent_mailsearch tool to search user mail for information. Include a time range and supporting information if nessesary.
        Use the agent_tasksearch tool to search user tasks and calendars for information. Include a time range and supporting information if nessesary.
        The agent_tasksearch tool can also check room and employee availability to coordinate meetings.
        If you are asked for availability, this means you should check for non-meeting times/dates.
        If someone asks for information from the Wiki or Confluence, you should as the agent_confluence tool.
        If someone asks for information from JIRA, you should use the agent_jira tool.
        If someone asks for imformation from Quantive, you should use the agent_quantive tool.
        If someone asks a business question, the agent_jira, agent_confluence and agent_quantive tools should be asked as well.
        Always include supporting URLs in your response.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Images responses should be formatted in HTML to display the image. Example: <img src="https://www.example.com/image.jpg" alt="image">
        Use the agent_mathmatician tool when attempting to solve mathmatical or logical problems. Include all supporting information in the prompt.
        Use the agent_researcher tool when attempting to respond to highly factual or technical prompts. This tool will provide you with feedback to improve your response.
        The agent_writer tool can be used to enhance your response with professional writing skills.
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
            },{
            "type": "function",
            "function": {
                    "name": "agent_mailsearch",
                    "description": "Use this agent to search the user's mail information related to the question/problem. Include a time range and supporting information if nessesary.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Prompt, asking the agent to search user mail for information related to the user's question/problem."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "agent_tasksearch",
                    "description": "Use this agent to search the user's tasks related to the question/problem. Include a time range and supporting information if nessesary.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Prompt, asking the agent to search user's task for information related to the user's question/problem."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "agent_quantive",
                    "description": "Use this agent to search the Quantive system for information related to the question/problem. Include a time range and supporting information if nessesary.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Prompt, asking the agent to search the Quantive system for information related to the user's question/problem."
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
        elif tool_name == "agent_writer":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Writer (Azure): {args["prompt"]}</i>')
            self.azure_agent.agent_instructions = "You are a professional writer. Use the information and instructions provided to write a response."
            results = self.azure_agent.generate(user, args['prompt'])
        elif tool_name == "agent_researcher":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Researcher (Azure): {args["prompt"]}</i>')
            self.azure_agent.agent_instructions = "You are a professional researcher and analyist. Use the information and instructions provided to research and provide feedback."
            results = self.azure_agent.generate(user, args['prompt'])
        elif tool_name == "agent_mathmatician":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Mathmatician (Ollama): {args["prompt"]}</i>')
            results = self.math_agent.generate(user, args['prompt'])
        elif tool_name == "agent_confluence":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Confluence (Azure): {args["prompt"]}</i>')
            results = self.confluence_agent.generate(user, args['prompt'])
        elif tool_name == "agent_jira":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent JIRA (Azure): {args["prompt"]}</i>')
            results = self.jira_agent.generate(user, args['prompt'])
        elif tool_name == "agent_websearch":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Websearch (Azure): {args["prompt"]}</i>')
            results = self.websearch_agent.generate(user, args['prompt'])
        elif tool_name == "agent_mailsearch":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Mailsearch (Azure): {args["prompt"]}</i>')
            results = self.mail_agent.generate(user, args['prompt'])
        elif tool_name == "agent_tasksearch":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Tasksearch (Azure): {args["prompt"]}</i>')
            results = self.tasks_agent.generate(user, args['prompt'])
        elif tool_name == "agent_quantive":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Quantive (Azure): {args["prompt"]}</i>')
            results = self.quantive_agent.generate(user, args['prompt'])
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