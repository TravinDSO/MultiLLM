import json
from llms.ollamamulti import OllamaMulti
from llms.tools.google_search import GoogleSearch  # Ensure this import is correct

class OllamaOrchestrator(OllamaMulti):
    def __init__(self, api_base_url='http://localhost:11434', model='llama3.1', info_link='', wait_limit=300, google_key="", google_cx=""):
        # Call the parent class constructor
        super().__init__(api_base_url, model, info_link, wait_limit)
        self.websearch = GoogleSearch(google_key, google_cx)

        # Agents
        self.llama3_1_agent = OllamaMulti(api_base_url, 'llama3.1:latest')

        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        You will always make use of the web_search tool to find real-time information that may not be available in the model.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Use the agent_mathmatician tool when attempting to solve mathematical or logical problems. Include all supporting information in the prompt.
        Use the agent_researcher tool when attempting to respond to highly factual or technical prompts. This tool will provide you with feedback to improve your response.
        All final responses should flow through the agent_writer tool to generate a response.
        """
        self.tools = [
            {
            "type": "function",
            "function": {
                    "name": "web_search",
                    "description": "Always search the web for real-time information that may not be available in the model. If you don't find what you need, try again.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "search_string": {
                        "type": "string",
                        "description": "Your search string to find information on the web. Use this information in your response."
                        }
                    },
                    "required": ["search_string"]
                    }
                }
            }, {
            "type": "function",
            "function": {
                    "name": "agent_writer",
                    "description": "Use the Claude API to take all of the information you have gathered and write a response.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "information": {
                        "type": "string",
                        "description": "All of the information you have gathered to write a response and instructions on what to do with it."
                        }
                    },
                    "required": ["information"]
                    }
                }
            }, {
            "type": "function",
            "function": {
                    "name": "agent_researcher",
                    "description": "Use the Claude API as a researcher and analyst to check facts, provide information and feedback to improve your response.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "information": {
                        "type": "string",
                        "description": "Information to research and analyze, providing feedback to improve your response."
                        }
                    },
                    "required": ["information"]
                    }
                }
            }, {
            "type": "function",
            "function": {
                    "name": "agent_mathmatician",
                    "description": "For mathematical or logical problems, use this agent to assist in solving the question. Include supporting information if necessary.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "problem": {
                        "type": "string",
                        "description": "Problem and information to use in solving the question, providing detailed data to improve your response."
                        }
                    },
                    "required": ["problem"]
                    }
                }
            }
        ]

    # Override the handle_tool method
    def handle_tool(self, user, tool_name, tool_args):
        debug = True  # Set to True to print debug information
        if tool_name == "web_search":
            top_result_link, page_text = self.websearch.search(tool_args['search_string'])
            results = f'Top search result link: {top_result_link}\nPage text: {page_text}'
            if debug: print(f"Searching the web (Google)")
        elif tool_name == "agent_writer":
            if debug: print(f"Asking the Agent Writer")
            agent_prompt = f"You are a professional writer. Use the information and instructions provided to write a response. Question: {tool_args['information']}"
            results = self.llama3_1_agent.generate(user, agent_prompt)
        elif tool_name == "agent_researcher":
            if debug: print(f"Asking the Agent Researcher")
            agent_prompt = f"You are a professional researcher and analyst. Use the information and instructions provided to research and provide feedback. Question: {tool_args['information']}"
            results = self.llama3_1_agent.generate(user, agent_prompt)
        elif tool_name == "agent_mathmatician":
            if debug: print(f"Asking the Agent Mathematician")
            agent_prompt = f"You are a professional mathematician. Use the information and instructions provided to solve the problem. Question: {tool_args['problem']}"
            results = self.llama3_1_agent.generate(user, agent_prompt)
        else:
            results = "Tool not supported"

        return results