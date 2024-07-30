import json
from llms.azuremulti import AzureMulti
from llms.tools.confluence_search import ConfluenceSearch

# Inherit from the OpenaiMulti class
class AzureConfluenceAgent(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',info_link='',type='assistant',
                 wait_limit=300, confluence_url="",confluence_token=""):
        # Call the parent class constructor
        super().__init__(api_key,model,endpoint,version,info_link,wait_limit,type)

        # Tools
        self.confluence_search = ConfluenceSearch(confluence_url, confluence_token)


        self.agent_instructions = """
        You are a specialized agent that can search Atlassian Confluence, for information.
        As this is your primary job, you will always use the confluence_CQL_search and confluence_site_search tools to search for information in the Atlassian Confluence system.
        If you don't find what you need, try using the confluence_search tool again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        Your response can only be 512kb in size.
        """
        # Additional tools created for the orchestrator
        self.tools = [
            {
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
            },            {
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
        debug = True # Set to True to print debug information
        args = json.loads(tool.function.arguments)
        if tool_name == "confluence_CQL_search":
            if debug: print(f"Searching the Wiki (Confluence): {args['CQL']}")
            confluence_info = ""
            confluence_data = self.confluence_search.search(args['CQL'], num_results=25)
            if confluence_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for page_text in confluence_data:
                    #append the link and page test
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
                    #append the link and page test
                    confluence_info += f"Page Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{confluence_info}'
        else:
            results =  "Tool not supported"
        
        return results