import json
import datetime
from llms.azuremulti import AzureMulti
from llms.openaimulti import OpenaiMulti
from llms.tools.google_search import GoogleSearch

class AzureWebsearchAgent(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',info_link='',type='assistant',agent_name='Azure Websearch Agent',wait_limit=300,
                 google_key="",google_cx=""):
        # Call the parent class constructor
        super().__init__(api_key=api_key, model=model, endpoint=endpoint, version=version, info_link=info_link, wait_limit=wait_limit, type=type, agent_name=agent_name)

        # Tools
        self.google_search = GoogleSearch(google_key,google_cx)


        self.agent_instructions = """
        You are a specialized agent that can search the web for information.
        As this is your primary job, you will always use the web_search tool to search for information on the web.
        If you don't find what you need, try using the confluence_search tool again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        For all tools, wait for the response before continuing to the next tool.
        """
        # Additional tools created for the orchestrator
        self.tools = [
            {
            "type": "function",
            "function": {
                    "name": "web_search",
                    "description": "Always search the web for real-time information that may not be available in the model. If you don't find what you need, try again.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Your search string to find information on the web. Use this information in your response."
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
        if tool_name == "web_search":
            if debug: print(f"Searching the web (Google): {args['prompt']}")
            web_info = ""
            web_data = self.google_search.search(args['prompt'], num_results=1)
            if web_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for link, page_text in web_data:
                    #append the link and page test
                    web_info += f"Link: {link}\nPage Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{web_info}'
        else:
            results =  "Tool not supported"
        
        return results
    
class OpenAIWebsearchAgent(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',type='assistant',
                 wait_limit=300, google_key="",google_cx=""):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)

        # Tools
        self.google_search = GoogleSearch(google_key,google_cx)


        self.agent_instructions = """
        You are a specialized agent that can search the web for information.
        As this is your primary job, you will always use the web_search tool to search for information on the web.
        If you don't find what you need, try using the confluence_search tool again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        """
        # Additional tools created for the orchestrator
        self.tools = [
            {
            "type": "function",
            "function": {
                    "name": "web_search",
                    "description": "Always search the web for real-time information that may not be available in the model. If you don't find what you need, try again.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "Your search string to find information on the web. Use this information in your response."
                        }
                    },
                    "required": ["prompt"]
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

    # override the handle_tool method
    def handle_tool(self, user, tool):
        tool_name = tool.function.name
        debug = True # Set to True to print debug information
        args = json.loads(tool.function.arguments)
        if tool_name == "web_search":
            if debug: print(f"Searching the web (Google): {args['prompt']}")
            web_info = ""
            web_data = self.google_search.search(args['prompt'], num_results=1)
            if web_data is None:
                results = "No search results found"
            else:
                # Get each link and page text from the search results
                for link, page_text in web_data:
                    #append the link and page test
                    web_info += f"Link: {link}\nPage Text: {page_text}\n"
                results = f'Your search to answer the question produced the following results:\n{web_info}'
                # If results are greater than 100k characters, truncate the response
                if len(results) > 100000:
                    results = results[:100000]
            return results
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            return f"The current date and time is: {datetime.datetime.now()}"
        else:
            return "Tool not supported"