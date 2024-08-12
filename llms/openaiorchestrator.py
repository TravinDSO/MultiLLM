# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

import json
import datetime
from llms.openaimulti import OpenaiMulti
from llms.claudemulti import ClaudeMulti
from llms.ollamamulti import OllamaMulti
from llms.agents.websearch_agent import OpenAIWebsearchAgent
from llms.agents.mail_agent import OpenAIMailAgent
from llms.agents.calendar_agent import OpenAICalAgent
from llms.tools.weather import WeatherChecker

# Inherit from the OpenaiMulti class
class OpenaiOrchestrator(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',
                 api_key_2='',model_2='gpt-4o',
                 wait_limit=300, type='chat',
                 google_key="",google_cx="",claude_key="",openweathermap_key=""):
        # Call the parent class constructor
        super().__init__(api_key,model=model,api_key_2=api_key_2,model_2=model_2,
                         info_link=info_link,wait_limit=wait_limit,type=type)

        #Agents
        self.claude_agent = ClaudeMulti(claude_key)
        self.websearch_agent = OpenAIWebsearchAgent(api_key=api_key,model=model,type = 'assistant',google_key=google_key,google_cx=google_cx)
        self.mail_agent = OpenAIMailAgent(api_key=api_key,model=model,type = 'assistant')
        self.tasks_agent = OpenAICalAgent(api_key=api_key,model=model,type = 'assistant')
        self.math_agent = OllamaMulti('llama3.1:latest')
        self.weather_checker = WeatherChecker(openweathermap_key)

        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        Use the agent_websearch tool to find real-time information that may not be available in the model.
        Use the agent_mailsearch tool to search user mail for information.
        Use the agent_tasksearch tool to search user tasks and calendars for information.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Images responses should be formatted in HTML to display the image. Example: <img src="https://www.example.com/image.jpg" alt="image">
        Use the agent_mathmatician tool when attempting to solve mathmatical or logical problems. Include all supporting information in the prompt.
        Use the agent_researcher tool when attempting to respond to highly factual or technical prompts. This tool will provide you with feedback to improve your response.
        All final responses should flow through the agent_writer tool to generate a response.
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
            },{
            "type": "function",
            "function": {
                    "name": "date_time",
                    "description": "Obtain the current date and time."
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
                    "description": "Use this agent to search the user's mail information related to the question/problem. Include supporting information if nessesary.",
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
            }
        ]

    # override the handle_tool method
    def handle_tool(self, user, tool):
        tool_name = tool.function.name
        debug = True # Set to True to print debug information
        args = json.loads(tool.function.arguments)
        if tool_name == "generate_image":
            self.extra_messages[user].append(f'<HR><i>Generating image using this prompt: {args["prompt"]}</i>')
            results = self.image_gen_tool.image_generate(prompt = args['prompt']) # image gen is already part of the OpenaiMulti class
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
        elif tool_name == "agent_websearch":
            if debug: print(f"Asking the Agent Websearcher (OpenAI)")
            results = self.websearch_agent.generate(user, args['prompt'])
        elif tool_name == "agent_mailsearch":
            if debug: print(f"Asking the Agent Mailsearcher (OpenAI)")
            results = self.mail_agent.generate(user, args['prompt'])
        elif tool_name == "agent_tasksearch":
            if debug: print(f"Asking the Agent Tasksearcher (OpenAI)")
            results = self.tasks_agent.generate(user, args['prompt'])
        else:
            results =  "Tool not supported"
        
        return results
    
    # Override and run the clear_conversation method
    def clear_conversation(self, user):
        super().clear_conversation(user)
        self.websearch_agent.clear_conversation(user)
        self.claude_agent.clear_conversation(user)
        self.math_agent.clear_conversation(user)
        return "Conversation cleared"