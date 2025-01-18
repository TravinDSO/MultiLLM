import json
import datetime
from llms.openairealtime import OpenaiRealtime
from llms.openaimulti import OpenaiMulti
from llms.claudemulti import ClaudeMulti
from llms.agents.websearch_agent import OpenAIWebsearchAgent
from llms.agents.mail_agent import OpenAIMailAgent
from llms.agents.calendar_agent import OpenAICalAgent
from llms.tools.weather import WeatherChecker
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenaiRealOrchestrator(OpenaiRealtime):
    def __init__(self, api_key, model='gpt-4o-realtime-preview-2024-12-17',
                 info_link='', wait_limit=300, type='chat', voice="alloy",
                 google_key="", google_cx="", claude_key="", openweathermap_key=""):
        # Call the parent class constructor
        super().__init__(api_key, model=model,
                        info_link=info_link, wait_limit=wait_limit,
                        type=type, voice=voice)

        # Initialize agents
        self.claude_agent = ClaudeMulti(claude_key)
        self.websearch_agent = OpenAIWebsearchAgent(api_key=api_key, model='gpt-4o', type='assistant', google_key=google_key, google_cx=google_cx)
        self.mail_agent = OpenAIMailAgent(api_key=api_key, model='gpt-4o', type='assistant')
        self.tasks_agent = OpenAICalAgent(api_key=api_key, model='gpt-4o', type='assistant')
        self.math_agent = OpenaiMulti(api_key=api_key, model='o1-preview', type='chat')
        self.researcher_agent = OpenaiMulti(api_key=api_key, model='o1-preview', type='chat')
        self.weather_checker = WeatherChecker(openweathermap_key)

        # Set token run size for agents
        self.websearch_agent.token_run_size = 3000
        self.mail_agent.token_run_size = 3000
        self.tasks_agent.token_run_size = 3000

        # Orchestrator instructions
        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        Use the agent_websearch tool to find real-time information that may not be available in the model.
        Use the agent_mailsearch tool to search user mail for information.
        Use agent_calendarsearch tool to search user tasks and calendars for information.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Images responses should be formatted in HTML to display the image. Example: <img src="https://www.example.com/image.jpg" alt="image">
        Use the agent_mathmatician tool when attempting to solve mathmatical or logical problems. Include all supporting information in the prompt.
        Use the agent_researcher tool when attempting to respond to highly factual or technical prompts. This tool will provide you with feedback to improve your response.
        All final responses should flow through the agent_writer tool to generate a response.
        For all tools, wait for the response before continuing to the next tool.
        For all tools, you should ask follow-up questions to get more information if needed.
        """

        # Localized instructions
        self.agent_instructions += """
        All times should be converted to Eastern time. If a time or date specific question is asked to and agent, ensure they know the time zone is Eastern.
        """

        # Update session config with tools
        self.session_config["instructions"] = self.agent_instructions
        self.session_config["tools"] = [
            {
                "type": "function",
                "name": "generate_image",
                "description": "Generate an image based on the prompt",
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
            },
            {
                "type": "function",
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
                    "required": ["latitude", "longitude"]
                }
            },
            {
                "type": "function",
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
                    "required": ["latitude", "longitude"]
                }
            },
            {
                "type": "function",
                "name": "date_time",
                "description": "Obtain the current date and time."
            },
            {
                "type": "function",
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
            },
            {
                "type": "function",
                "name": "agent_researcher",
                "description": "Use the OpenAI API as a researcher and analyist to check facts, provide information and feedback to improve your response.",
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
            },
            {
                "type": "function",
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
            },
            {
                "type": "function",
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
            },
            {
                "type": "function",
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
            },
            {
                "type": "function",
                "name": "agent_calendarsearch",
                "description": "Use this agent to search the user's calendar related to the question/problem. Include a time range and supporting information if nessesary.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Prompt, asking the agent to search user's calendar for information related to the user's question/problem."
                        }
                    },
                    "required": ["prompt"]
                }
            }
        ]

    async def handle_tool(self, user, tool):
        """Handle tool calls asynchronously."""
        tool_name = tool.get("name")
        debug = True  # Set to True to print debug information
        args = json.loads(tool["arguments"])

        if tool_name == "generate_image":
            self.extra_messages[user].append(f'<HR><i>Generating image using this prompt: {args["prompt"]}</i>')
            print(f'Generating image using this prompt: {args["prompt"]}')
            results = self.image_gen_tool.image_generate(prompt=args['prompt'])
        elif tool_name == "get_weather":
            if debug: logger.info("Getting the weather")
            results = json.dumps(self.weather_checker.get_weather(args['latitude'], args['longitude']))
            print(f'Getting the weather: {results}')
        elif tool_name == "get_forecast":
            if debug: logger.info("Getting the weather forecast")
            results = json.dumps(self.weather_checker.get_forecast(args['latitude'], args['longitude']))
            print(f'Getting the weather forecast: {results}')
        elif tool_name == "date_time":
            if debug: logger.info("Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
            print(f'Getting the date and time: {results}')
        elif tool_name == "agent_writer":
            if debug: logger.info("Asking the Agent Writer (Claude)")
            self.claude_agent.agent_instructions = "You are a professional writer. Use the information and instructions provided to write a response."
            results = self.claude_agent.generate(user, args['prompt'])
            print(f'Asking the Agent Writer (o1-preview): {results}')
        elif tool_name == "agent_researcher":
            if debug: logger.info("Asking the Agent Researcher (Claude)")
            self.claude_agent.agent_instructions = "You are a professional writer. Use the information and instructions provided to write a response."
            print(f'Asking the Agent Researcher (o1-preview): {results}')
        elif tool_name == "agent_mathmatician":
            self.math_agent.agent_instructions = "You are a professional mathmatician. Use the information and instructions provided to solve the problem."
            results = self.math_agent.generate(user, args['prompt'])
            print(f'Asking the Agent Mathmatician: {results}')
        elif tool_name == "agent_websearch":
            if debug: logger.info("Asking the Agent Websearcher (o1-preview)")
            results = self.websearch_agent.generate(user, args['prompt'])
            print(f'Asking the Agent Websearcher (OpenAI): {results}')
        elif tool_name == "agent_mailsearch":
            if debug: logger.info("Asking the Agent Mailsearcher (OpenAI)")
            results = self.mail_agent.generate(user, args['prompt'])
            print(f'Asking the Agent Mailsearcher (OpenAI): {results}')
        elif tool_name == "agent_calendarsearch":
            if debug: logger.info("Asking the Agent Calendar searcher (OpenAI)")
            results = self.tasks_agent.generate(user, args['prompt'])
            print(f'Asking the Agent Calendar searcher (OpenAI): {results}')
        else:
            results = "Tool not supported"

        return results

    async def clear_conversation(self, user):
        """Clear conversations for all agents."""
        await super().clear_conversation(user)
        self.websearch_agent.clear_conversation(user)
        self.researcher_agent.clear_conversation(user)
        self.claude_agent.clear_conversation(user)
        self.math_agent.clear_conversation(user)
        return "Conversation cleared"

# Test Cell
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    import asyncio

    async def test_real_orchestrator():
        # Load API key from environment
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        claude_key = os.getenv("CLAUDE_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        google_cx = os.getenv("GOOGLE_CX")
        openweathermap_key = os.getenv("OPENWEATHERMAP_API_KEY")
        
        if not api_key:
            print("Error: OPENAI_API_KEY not found in environment variables")
            return
            
        # Initialize the realtime orchestrator
        orchestrator = OpenaiRealOrchestrator(
            api_key,
            claude_key=claude_key,
            google_key=google_key,
            google_cx=google_cx,
            openweathermap_key=openweathermap_key
        )
        
        try:
            # Test basic conversation with tool use
            response = await orchestrator.generate("test_user", "What's the weather like in New York City and can you search for any recent news about the city?")
            print("AI Response:", response)
            
            # Get any extra messages
            extra_messages = orchestrator.get_extra_messages("test_user")
            for msg in extra_messages:
                print("Extra message:", msg)
                
        except Exception as e:
            print(f"Error during test: {e}")
        finally:
            # Clean up
            await orchestrator.cleanup()

    # Run the test
    asyncio.run(test_real_orchestrator()) 