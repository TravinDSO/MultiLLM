import json
from llms.azuremulti import AzureMulti
from llms.tools.jira_search import JiraSearch

# Inherit from the OpenaiMulti class
class AzureJiraAgent(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',info_link='',type='assistant',
                 wait_limit=300, jira_url="",jira_token=""):
        # Call the parent class constructor
        super().__init__(api_key,model,endpoint,version,info_link,wait_limit,type)

        # Tools
        self.jira_search = JiraSearch(jira_url, jira_token)


        self.agent_instructions = """
        You are a specialized agent that can search Atlassian JIRA, for information.
        As this is your primary job, you will always use the jira_search tool to search for information in the Atlassian JIRA system.
        If you don't find what you need, try using the jira_search tool again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        Your response can only be 512kb in size.
        """
        # Additional tools created for the orchestrator
        self.tools = [
            {
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
            }
        ]

    # override the handle_tool method
    def handle_tool(self, user, tool):
        tool_name = tool.function.name
        debug = True # Set to True to print debug information
        args = json.loads(tool.function.arguments)
        if tool_name == "jira_search":
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
        else:
            results =  "Tool not supported"
        
        return results