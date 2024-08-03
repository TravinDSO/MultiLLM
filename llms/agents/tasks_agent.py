import json
import datetime
from llms.openaimulti import OpenaiMulti
from llms.tools.gmail import GmailClient

class OpenAITasksAgent(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',type='assistant',
                 wait_limit=300):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)

        self.gmail_clients = {}

        self.agent_instructions = """
        You are a specialized agent that keeps track of calendars, tasks, and to-do's.
        As this is your primary job, you will always use all the tools available to search for information.
        If you don't find what you need, try using the mail search tools again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        Your response must be less than 100k characters.
        """
        # Additional tools created for the orchestrator
        self.tools = [
            {
            "type": "function",
            "function": {
                    "name": "gmail_calendar_search",
                    "description": "Search Gmail's Calendars for details relating to the user's question.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                        "type": "string",
                        "description": "the isoformat of the start date of the search"
                        },
                        "end_date": {
                        "type": "string",
                        "description": "the isoformat of the end date of the search"
                        },
                        "search_string": {
                        "type": "string",
                        "description": "Your search string to find information in Gmail's Calendar. Ensure this is formatted correctly using Gmail's calendar search syntax."
                        }
                    },
                    "required": ["start_date","end_date","search_string"]
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
        if tool_name == "gmail_calendar_search":
            evt_details = ""
            # Check if the user has a Gmail client
            if user not in self.gmail_clients:
                try:
                    self.gmail_clients[user] = GmailClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            
            start_date = args['start_date']
            end_date = args['end_date']
            query = args['search_string']

            if debug: print(f"Searching Gmail Calendar: {start_date} to {end_date} for {query}")
            events = self.gmail_clients[user].search_calendar_events(start_date, end_date, query=query)
            
            if events:
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    evt_details += f"{start}: {event['summary']}\n"

            if evt_details:
                return evt_details
            else:
                return 'No events found.'
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
        else:
            results =  "Tool not supported"
        
        return results