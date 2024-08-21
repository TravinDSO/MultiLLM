import json
import datetime
from llms.azuremulti import AzureMulti
from llms.ollamamulti import OllamaMulti
from llms.tools.quantive import QuantiveAPI
from llms.tools.confluence_search import ConfluenceSearch
from llms.tools.jira_search import JiraSearch

# Inherit from the OpenaiMulti class
class AzureQuantiveAgent(AzureMulti):
    def __init__(self, api_key, model='gpt-4o', endpoint='', version='', info_link='', type='assistant',agent_name='Azure Quantive Agent',wait_limit=300,
                 quantive_url="",quantive_key="",quantive_account_id="",confluence_url="",confluence_token="",jira_url="",jira_token=""):
        # Call the parent class constructor
        super().__init__(api_key=api_key, model=model, endpoint=endpoint, version=version, info_link=info_link, wait_limit=wait_limit, type=type, agent_name=agent_name)

        # Tools
        self.quantive_search = QuantiveAPI(quantive_key,quantive_url,quantive_account_id)
        self.confluence_search = ConfluenceSearch(confluence_url, confluence_token)
        self.jira_search = JiraSearch(jira_url, jira_token)

        self.agent_instructions = """
        You are a specialized agent that can search Quantive's OKR tool, Atlassian Confluence and JIRA, for information.
        Always use the date_time tool to check the current date and time.
        As this is your primary job, you will always search Quantive first and then each of your tools for supporting information.
        Ensure your CQL search only searches for pages and not other types of content.
        If you don't find what you need, try using the confluence_search tool again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        Include supporting URLs in your response.
        For all tools, wait for the response before continuing to the next tool.
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
                        "description": "Craft a JIRA JQL string to find information from Atlassian JIRA."
                        }
                    },
                    "required": ["JQL"]
                    }
                } 
            },{
                "type": "function",
                "function": {
                    "name": "quantive_search",
                    "description": "Search the Quantive OKR system for information. If you don't find what you need, try again.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_string": {
                                "type": "string",
                                "description": "Craft a search string to find information from Quantive."
                            }
                        },
                        "required": ["query_string"]
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
            confluence_data = self.confluence_search.site_search(cql, num_results=25)
            if confluence_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for page_text in confluence_data:
                    # append the link and page test
                    confluence_info += f"Page Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{confluence_info}'
        elif tool_name == "jira_search":
            if debug: print(f"Searching JIRA: {args['JQL']}")
            jira_info = ""
            jira_data = self.jira_search.search(args['JQL'], num_results=100)
            if jira_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for ticket_text in jira_data:
                    #append the link and page test
                    jira_info += f"Page Text: {ticket_text}\n"
                results = f'Your search to answer the question produced the following results:\n{jira_info}'
        elif tool_name == "quantive_search":
            if debug: print(f"Searching Quantive: {args['query_string']}")
            text_search_filter = r'{name:{$regex: ".*' + args['query_string'] + '.*"}}'
            search_fields = 'url,name,description,closedStatus'
            query = f"filter={text_search_filter}&fields={search_fields}"
            quantive_data = self.quantive_search.search(query)
            if quantive_data is None:
                results = "No search results found"
            else:
                results = f'Your search to answer the question produced the following results:\n{quantive_data}'
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
        else:
            results = "Tool not supported"
        # Check if the results are greater than 100k characters and truncate if necessary
        if len(results) > 100000:
            results = results[:100000] + '... (truncated due to length)'
        return results