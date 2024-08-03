import json
import datetime
from llms.openaimulti import OpenaiMulti
from llms.tools.gmail import GmailClient

class OpenAIMailAgent(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',type='assistant',
                 wait_limit=300):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)

        self.gmail_clients = {}

        self.agent_instructions = """
        You are a specialized agent that can search user mail for information.
        As this is your primary job, you will always use all the mail tools to search for information.
        If you don't find what you need, try using the mail search tools again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
        Your response must be less than 100k characters.
        """
        # Additional tools created for the orchestrator
        self.tools = [
            {
            "type": "function",
            "function": {
                    "name": "gmail_search",
                    "description": "Search Gmail for details relating to the user's question.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "search_string": {
                        "type": "string",
                        "description": "Your search string to find information in Gmail. Ensure this is formatted correctly using Gmail's search syntax."
                        }
                    },
                    "required": ["search_string"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "gmail_mark_as_read",
                    "description": "Mark an email as read in Gmail.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                        "type": "string",
                        "description": "The message ID of the email to mark as read."
                        }
                    },
                    "required": ["message_id"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "gmail_archive",
                    "description": "Archive an email in Gmail.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                        "type": "string",
                        "description": "The message ID of the email to archive."
                        }
                    },
                    "required": ["message_id"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "gmail_label",
                    "description": "Label an email in Gmail.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                        "type": "string",
                        "description": "The message ID of the email to label."
                        },
                        "label_id": {
                        "type": "string",
                        "description": "The label ID to apply to the email."
                        }
                    },
                    "required": ["message_id","label_id"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "gmail_delete",
                    "description": "Delete an email in Gmail.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                        "type": "string",
                        "description": "The message ID of the email to delete."
                        }
                    },
                    "required": ["message_id"]
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
        if tool_name == "gmail_search":
            msg_details = ""
            # Check if the user has a Gmail client
            if user not in self.gmail_clients:
                try:
                    self.gmail_clients[user] = GmailClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            
            if debug: print(f"Searching Gmail: {args['search_string']}")
            gmail_data = self.gmail_clients[user].search_emails(args['search_string'])

            if gmail_data:
                for msg in gmail_data:
                    msg_details += self.gmail_clients[user].get_email_details(msg['id'])
            
            if msg_details:
                return msg_details
            else:
                return 'No messages found.'
        elif tool_name == "gmail_mark_as_read": 
            if user not in self.gmail_clients:
                try:
                    self.gmail_clients[user] = GmailClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            if debug: print(f"Marking email as read: {args['message_id']}")
            self.gmail_clients[user].mark_as_read(args['message_id'])
            return "Email marked as read"
        elif tool_name == "gmail_archive":
            if user not in self.gmail_clients:
                try:
                    self.gmail_clients[user] = GmailClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            if debug: print(f"Archiving email: {args['message_id']}")
            self.gmail_clients[user].archive_email(args['message_id'])
            return "Email archived"
        elif tool_name == "gmail_label":
            if user not in self.gmail_clients:
                try:
                    self.gmail_clients[user] = GmailClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            if debug: print(f"Labeling email: {args['message_id']}")
            self.gmail_clients[user].add_label(args['message_id'], args['label_id'])
            return "Label added to email"
        elif tool_name == "gmail_delete":
            if user not in self.gmail_clients:
                try:
                    self.gmail_clients[user] = GmailClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            if debug: print(f"Deleting email: {args['message_id']}")
            self.gmail_clients[user].delete_email(args['message_id'])
            return "Email deleted"
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
        else:
            results =  "Tool not supported"
        
        return results