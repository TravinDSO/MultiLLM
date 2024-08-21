import json
import datetime
from llms.openaimulti import OpenaiMulti
from llms.azuremulti import AzureMulti
from llms.tools.gmail import GmailClient
from llms.tools.office365 import OutlookClient

class OpenAICalAgent(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',type='assistant',
                 wait_limit=300):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)

        self.gmail_clients = {}

        self.agent_instructions = """
        You are a specialized agent that keeps track of calendars.
        As this is your primary job, you will always use all the tools available to search for information.
        If you don't find what you need, try using the calendar search tool again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        For all tools, wait for the response before continuing to the next tool.
        """

        # Localized instructions for the orchestrator
        self.agent_instructions += """
        All times should be converted to Eastern time. If a time or date specific question is asked to and agent, ensure they know the time zone is Eastern.
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
    
class AzureCalAgent(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',info_link='',type='assistant',agent_name='Azure Calendar Agent',wait_limit=300):
        # Call the parent class constructor
        super().__init__(api_key=api_key,model=model,endpoint=endpoint,version=version,info_link=info_link,type=type,wait_limit=wait_limit,agent_name=agent_name)

        self.outlook365_clients = {}

        self.agent_instructions = """
        You are a specialized agent that keeps track of calendars.
        Always get the current date and time using the date_time tool before using other tools.
        As this is your primary job, you will always use all the tools available to search for information.
        Use the search_calendar_events tool to search calendars for information. Include a time range and supporting information if nessesary.
        Use the check_room_availability tool to check room availability for meetings. Include a time range and the room email address.
        Use the check_person_availability tool to check person availability for meetings. Include a time range and the person email address.
        If you are asked for availability, this means you should check for non-meeting times/dates.
        If you are asked to search for non-specific things such as 'meetings' or 'events', just search with '*' as the search string.
        If you don't find what you need, try using the search tools again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        """
        # Localized instructions for the orchestrator
        self.agent_instructions += """
        If a time or date specific question is asked to and agent, ensure it is converted to Eastern Time if nessesary.
        """

        # Additional tools created for the orchestrator
        self.tools = [
            {
            "type": "function",
            "function": {
                    "name": "search_calendar_events",
                    "description": "Search Outlook's Calendars for details relating to the user's question.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "search_string": {
                        "type": "string",
                        "description": "Your search string to find information in Outlook's Calendar. Ensure this is formatted correctly using Outlook's Graph API search syntax."
                        },
                        "start_date": {
                        "type": "string",
                        "description": "a Python date.isoformat() [Eastern Standard Time] for the start date of the search"
                        },
                        "end_date": {
                        "type": "string",
                        "description": "a Python date.isoformat() [Eastern Standard Time] for the end date of the search"
                        }
                    },
                    "required": ["start_date","end_date","search_string"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "check_room_availability",
                    "description": "Check the availability of a room in Outlook.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "room_email": {
                        "type": "string",
                        "description": "Email address of the room to check availability for."
                        },
                        "start_date": {
                        "type": "string",
                        "description": "a Python date.isoformat() [Eastern Standard Time] for the start date of the search"
                        },
                        "end_date": {
                        "type": "string",
                        "description": "a Python date.isoformat() [Eastern Standard Time] for the end date of the search"
                        }
                    },
                    "required": ["start_date","end_date","room_email"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "check_person_availability",
                    "description": "Check the availability of a person in Outlook.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "person_email": {
                        "type": "string",
                        "description": "Email address of the person to check availability for."
                        },
                        "start_date": {
                        "type": "string",
                        "description": "a Python date.isoformat() [Eastern Standard Time] for the start date of the search"
                        },
                        "end_date": {
                        "type": "string",
                        "description": "a Python date.isoformat() [Eastern Standard Time] for the end date of the search"
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
        if tool_name == "search_calendar_events":
            events = None
            evt_details = ""
            # Check if the user has a Outlook client
            if user not in self.outlook365_clients:
                try:
                    self.outlook365_clients[user] = OutlookClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            
            start_date = args['start_date']
            end_date = args['end_date']
            query = args['search_string']

            if debug: print(f"Searching Outlook Calendar: {start_date} to {end_date} for {query}")
            events = self.outlook365_clients[user].search_calendar_events(query, start_date, end_date)

            if events:
                for event in events:
                     start = event['start'].get('dateTime', event['start'].get('date'))
                     evt_details += f"{start}: {event['subject']}\n"
                # If results are greater than 100k characters, truncate the response
                if len(evt_details) > 100000:
                    evt_details = evt_details[:100000]
                return evt_details
            else:
                 return 'No upcoming events found.'
        elif tool_name == "check_room_availability":
            # Check if the user has a Outlook client
            if user not in self.outlook365_clients:
                try:
                    self.outlook365_clients[user] = OutlookClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            room_email = args['room_email']
            start_date = args['start_date']
            end_date = args['end_date']
            if debug: print(f"Checking room availability for {room_email} from {start_date} to {end_date}")
            try:
                availability = self.outlook365_clients[user].check_room_availability(room_email, start_date, end_date)
                # If results are greater than 100k characters, truncate the response
                if len(availability) > 100000:
                    availability = availability[:100000]
                return availability
            except Exception as e:
                return f"An error occurred: {e}"
        elif tool_name == "check_person_availability":
            # Check if the user has a Outlook client
            if user not in self.outlook365_clients:
                try:
                    self.outlook365_clients[user] = OutlookClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            person_email = args['person_email']
            start_date = args['start_date']
            end_date = args['end_date']
            if debug: print(f"Checking person availability for {person_email} from {start_date} to {end_date}")
            try:
                availability = self.outlook365_clients[user].check_person_availability(person_email, start_date, end_date)
                # If results are greater than 100k characters, truncate the response
                if len(availability) > 100000:
                    availability = availability[:100000]
                return availability
            except Exception as e:
                return f"An error occurred: {e}"
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            return f"The current date and time is: {datetime.datetime.now()}"
        else:
            return "Tool not supported"