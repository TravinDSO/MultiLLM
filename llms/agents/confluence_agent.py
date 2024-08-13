import json
import datetime
from llms.azuremulti import AzureMulti
from llms.ollamamulti import OllamaMulti
from llms.tools.confluence_search import ConfluenceSearch

# Inherit from the OpenaiMulti class
class AzureConfluenceAgent(AzureMulti):
    def __init__(self, api_key, model='gpt-4o', endpoint='', version='', info_link='', type='assistant',agent_name='Azure Confluence Agent',wait_limit=1200,
                 confluence_url="", confluence_token=""):
        # Call the parent class constructor
        super().__init__(api_key=api_key, model=model, endpoint=endpoint, version=version, info_link=info_link, wait_limit=wait_limit, type=type, agent_name=agent_name)

        # Tools
        self.confluence_search = ConfluenceSearch(confluence_url, confluence_token)

        self.agent_instructions = """
        You are a specialized agent that can search Atlassian Confluence, for information.
        Always use the date_time tool to check the current date and time.
        As this is your primary job, you will always use the confluence_CQL_search and confluence_site_search tools to search for information in the Atlassian Confluence system.
        Ensure your CQL search only searches for pages and not other types of content.
        If you don't find what you need, try using the confluence_search tool again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        Include supporting URLs to the Confleunce pages in your response.
        For all tools, wait for the response before continuing to the next tool.
        Your response can be no larger than 10k characters.
        """
        # Additional tools created for the orchestrator
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "date_time",
                    "description": "Obtain the current date and time."
                }
            }, {
                "type": "function",
                "function": {
                    "name": "confluence_CQL_search",
                    "description": "Search the Atlassian Confluence system using query language. If you don't find what you need, try again.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "CQL": {
                                "type": "string",
                                "description": "Craft a Confluence CQL string to find information from Atlassian Confluence."
                            }
                        },
                        "required": ["CQL"]
                    }
                }
            }, {
                "type": "function",
                "function": {
                    "name": "confluence_site_search",
                    "description": "Used to perform a broad search of the Atlassian Confluence system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_string": {
                                "type": "string",
                                "description": "Craft a search string to find information from Atlassian Confluence."
                            }
                        },
                        "required": ["search_string"]
                    }
                }
            }
        ]

    # override the handle_tool method
    def handle_tool(self, user, tool):
        tool_name = tool.function.name
        debug = True  # Set to True to print debug information
        args = json.loads(tool.function.arguments)
        if tool_name == "confluence_CQL_search":
            if debug: print(f"Searching the Wiki (Confluence): {args['CQL']}")
            confluence_info = ""
            confluence_data = self.confluence_search.search(args['CQL'], num_results=10)
            if confluence_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for page_text in confluence_data:
                    # append the link and page test
                    confluence_info += f"Page Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{confluence_info}'
        elif tool_name == "confluence_site_search":
            cql = f"siteSearch ~ \"{args['search_string']}\""
            if debug: print(f"Searching the Wiki (Confluence): {cql}")
            confluence_info = ""
            confluence_data = self.confluence_search.site_search(cql, num_results=10)
            if confluence_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for page_text in confluence_data:
                    # append the link and page test
                    confluence_info += f"Page Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{confluence_info}'
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
        else:
            results = "Tool not supported"

        return results

# Inherit from the OllamaMulti class
class OllamaConfluenceAgent(OllamaMulti):
    def __init__(self, model='llama3.1:latest', confluence_url="", confluence_token=""):
        # Call the parent class constructor
        super().__init__(model)

        # Tools
        self.confluence_search = ConfluenceSearch(confluence_url, confluence_token)

        self.agent_instructions = """
        You are a specialized agent that can search Atlassian Confluence for information.
        Always use the date_time tool to check the current date and time.
        As this is your primary job, you will always use the confluence_CQL_search and confluence_site_search tools to search for information in the Atlassian Confluence system.
        Ensure your CQL search only searches for pages and not other types of content.
        If you don't find what you need, try using the confluence_search tool again.
        Verify the information you find is accurate and relevant prior to responding to the user.
        Include supporting URLs to the Confluence pages in your response.
        Your response can be no larger than 10k characters.
        """
        # Additional tools created for the orchestrator
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
                    "name": "confluence_CQL_search",
                    "description": "Search the Atlassian Confluence system using query language. If you don't find what you need, try again.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "CQL": {
                                "type": "string",
                                "description": "Craft a Confluence CQL string to find information from Atlassian Confluence."
                            }
                        },
                        "required": ["CQL"]
                    }
                }
            }, {
                "type": "function",
                "function": {
                    "name": "confluence_site_search",
                    "description": "Used to perform a broad search of the Atlassian Confluence system.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_string": {
                                "type": "string",
                                "description": "Craft a search string to find information from Atlassian Confluence."
                            }
                        },
                        "required": ["search_string"]
                    }
                }
            }
        ]

    # override the handle_tool method
    def handle_tool(self, user, tool_name, tool_args, prompt):
        debug = True  # Set to True to print debug information
        if tool_name == "confluence_CQL_search":
            if debug: print(f"Searching the Wiki (Confluence): {tool_args['CQL']}")
            confluence_info = ""
            confluence_data = self.confluence_search.search(tool_args['CQL'], num_results=10)
            if confluence_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for page_text in confluence_data:
                    # append the link and page test
                    confluence_info += f"Page Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{confluence_info}'
        elif tool_name == "confluence_site_search":
            cql = f"siteSearch ~ \"{tool_args['search_string']}\""
            if debug: print(f"Searching the Wiki (Confluence): {cql}")
            confluence_info = ""
            confluence_data = self.confluence_search.site_search(cql, num_results=25)
            if confluence_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for page_text in confluence_data:
                    # append the link and page test
                    confluence_info += f"Page Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{confluence_info}'
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
        else:
            results = "Tool not supported"

        return results
