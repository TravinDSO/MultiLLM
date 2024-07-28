import json
from llms.ollamamulti import OllamaMulti
from llms.tools.google_search import GoogleSearch
from llms.tools.confluence_search import ConfluenceSearch
from llms.tools.jira_search import JiraSearch

class OllamaOrchestrator(OllamaMulti):
    def __init__(self, api_base_url='http://localhost:11434', model='llama3.1', info_link='', wait_limit=300,
                 google_key="", google_cx="",confluence_url="",confluence_token="",jira_url="",jira_token=""):
        # Call the parent class constructor
        super().__init__(api_base_url, model, info_link, wait_limit)

        # Tools
        self.websearch = GoogleSearch(google_key, google_cx)
        self.confluence_search = ConfluenceSearch(confluence_url, confluence_token)
        self.jira_search = JiraSearch(jira_url, jira_token)

        # Agents
        self.llama3_1_agent = OllamaMulti(api_base_url, 'llama3.1:latest')

        self.verify_answers_asked = True
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

        # Additional tools created for the orchestrator
        self.tools = [
            {
            "type": "function",
            "function": {
                    "name": "web_search",
                    "description": "Search the web for real-time information to answer the prompt.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "search_string": {
                        "type": "string",
                        "description": "Search string to find more information on the web."
                        }
                    },
                    "required": ["search_string"]
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
                        "search_string": {
                        "type": "string",
                        "description": "Your search string to find information from Atlassian Confluence. Use this information in your response."
                        }
                    },
                    "required": ["search_string"]
                    }
                } 
            },{
            "type": "function",
            "function": {
                    "name": "jira_search",
                    "description": "Search the Atlassian JIRA system for information. If you don't find what you need, try again.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "JQL": {
                        "type": "string",
                        "description": "Craft a Confluence JQL string to find information from Atlassian Confluence."
                        }
                    },
                    "required": ["JQL"]
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
                    "description": "Use to take all of the information you have gathered and write a response.",
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
            },{
            "type": "function",
            "function": {
                    "name": "agent_researcher",
                    "description": "Use as a researcher and analyst to check facts, provide information and feedback to improve your response.",
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
    def handle_tool(self, user, tool_name, tool_args, prompt):
        debug = True  # Set to True to print debug information
        if tool_name == "web_search":
            if debug: print(f"Searching the web (Google)")
            web_info = ""
            web_data = self.websearch.search(tool_args['search_string'], num_results=3)
            if web_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for link, page_text in web_data:
                    #append the link and page test
                    web_info += f"Link: {link}\nPage Text: {page_text}\n"
                results = f'Your search to answer the question: {prompt} produced the following results:\n{web_info}'
        elif tool_name == "confluence_search":
            if debug: print(f"Searching the Wiki (Confluence): {tool_args['CQL']}")
            confluence_info = ""
            confluence_data = self.confluence_search.search(tool_args['CQL'], num_results=10)
            if confluence_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for page_text in confluence_data:
                    #append the link and page test
                    confluence_info += f"Page Text: {page_text}\n"
                results = f'Your search to answer the question: {prompt} produced the following results:\n{confluence_info}'
        elif tool_name == "jira_search":
            if debug: print(f"Searching JIRA: {tool_args['JQL']}")
            jira_info = ""
            jira_data = self.jira_search.search(tool_args['JQL'], num_results=10)
            if jira_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for ticket_text in jira_data:
                    #append the link and page test
                    jira_info += f"JIRA Text: {ticket_text}\n"
                results = f'Your search to answer the question: {prompt} produced the following results:\n{jira_info}'
        elif tool_name == "agent_writer":
            if debug: print(f"Asking the Agent Writer")
            agent_prompt = f"You are a professional writer. Use the information and instructions provided to write a response to the original question:{prompt}. Information and instructions: {tool_args['information']}"
            self.conversation_history[user].append({
                'role': 'user',
                'content': agent_prompt
            })
            self.llama3_1_agent.conversation_history[user] = self.conversation_history[user]
            results = self.llama3_1_agent.generate(user, agent_prompt)
        elif tool_name == "agent_researcher":
            if debug: print(f"Asking the Agent Researcher")
            agent_prompt = f"You are a professional researcher and analyst. Use the information and instructions provided to research and provide feedback to the original question: {prompt}. Information and instructions: {tool_args['information']}"
            self.conversation_history[user].append({
                'role': 'user',
                'content': agent_prompt
            })
            self.llama3_1_agent.conversation_history[user] = self.conversation_history[user]
            results = self.llama3_1_agent.generate(user, agent_prompt)
        elif tool_name == "agent_mathmatician":
            if debug: print(f"Asking the Agent Mathematician")
            agent_prompt = f"You are a professional mathematician. Use the information and instructions provided to solve the original question: {prompt}. Information and instructions: {tool_args['problem']}"
            self.conversation_history[user].append({
                'role': 'user',
                'content': agent_prompt
            })
            self.llama3_1_agent.conversation_history[user] = self.conversation_history[user]
            results = self.llama3_1_agent.generate(user, agent_prompt)
        else:
            results = "Tool not supported"

        return results