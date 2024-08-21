import json
import datetime
from llms.openaimulti import OpenaiMulti
from llms.azuremulti import AzureMulti
from llms.tools.gmail import GmailClient
from llms.tools.office365 import OutlookClient

class OpenAIMailAgent(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',type='assistant',
                 wait_limit=300):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)

        self.gmail_clients = {}

        self.agent_instructions = """
        You are a specialized agent that can search user mail for information.
        As this is your primary job, you will always use all the mail tools to search for information.
        When dealing with Labels, always use the gmail_list_labels tool to ensure you are using the correct label ID.
        If you don't find what you need, try using the mail search tools again.
        Verify the information you find is accurate and relevant prior to responsing to the user.
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
                    "name": "gmail_list_labels",
                    "description": "List all labels in Gmail.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                        "type": "string",
                        "description": "The prompt to list all labels."
                        }
                    },
                    "required": ["prompt"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "gmail_create_label",
                    "description": "Create a label in Gmail.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "label_name": {
                        "type": "string",
                        "description": "The name of the label to create."
                        }
                    },
                    "required": ["label_name"]
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
            gmail_data = self.gmail_clients[user].search_emails(args['search_string'], 20)

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
        elif tool_name == "gmail_list_labels":
            if user not in self.gmail_clients:
                try:
                    self.gmail_clients[user] = GmailClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            if debug: print(f"Listing labels")
            labels = self.gmail_clients[user].list_labels()
            return labels
        elif tool_name == "gmail_create_label":
            if user not in self.gmail_clients:
                try:
                    self.gmail_clients[user] = GmailClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            if debug: print(f"Creating label: {args['label_name']}")
            label_id = self.gmail_clients[user].create_label(args['label_name'])
            return f"Label created with ID: {label_id}"
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
        else:
            results =  "Tool not supported"
        
        return results
    
class AzureMailAgent(AzureMulti):
    def __init__(self, api_key,model='gpt-4o',endpoint='',version='',info_link='',type='assistant',wait_limit=300,agent_name='Azure Mail Agent'):
        # Call the parent class constructor
        super().__init__(api_key=api_key, model=model, endpoint=endpoint, version=version, info_link=info_link, wait_limit=wait_limit, type=type, agent_name=agent_name)

        self.outlook365_clients = {}

        self.agent_instructions = """
        You are a specialized agent that can search user mail for information.
        As this is your primary job, you will always use the mail tools to search for information.
        Always get the current date and time using the date_time tool before using other tools.
        Always use the outlook_search first to get a list of emails.
        Only use the outlook_mail_details tool if you need more information on a specific email.
        If you don't find what you need, try using the mail search tools again.
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
                    "name": "outlook_search",
                    "description": "Search Outlook e-mail relating to the user's question.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "search_string": {
                        "type": "string",
                        "description": "Your search string to find e-mails in Outlook. Ensure this is formatted correctly using Outlook's Graph API search syntax."
                        },
                        "start_date": {
                        "type": "string",
                        "description": "a Python date.isoformat() for the start date of the search"
                        },
                        "end_date": {
                        "type": "string",
                        "description": "a Python date.isoformat() for the end date of the search"
                        }
                    },
                    "required": ["start_date","end_date","search_string"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "outlook_mail_details",
                    "description": "Get the details of an e-mail in Outlook.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "email_id": {
                        "type": "string",
                        "description": "The ID of the e-mail to get details for."
                        }
                    },
                    "required": ["email_id"]
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
        if tool_name == "outlook_search":
            msg_details = ""
            # Check if the user has a Outlook client
            if user not in self.outlook365_clients:
                try:
                    self.outlook365_clients[user] = OutlookClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"

            start_date = args['start_date']
            end_date = args['end_date']
            query = args['search_string']

            if debug: print(f"Searching Outlook: {start_date} to {end_date} for {query}")

            try:
                outlook_data = self.outlook365_clients[user].search_emails(query, start_date, end_date)
            except Exception as e:
                return f"An error occurred: {e}"

            if outlook_data:
                for msg in outlook_data:
                    title = msg['subject']
                    id = msg['id']
                    msg_details += f"Subject: {title}, ID: {id}\n"
                    print(title)
            
            if msg_details:
                results = msg_details
            else:
                return 'No messages found.'
        elif tool_name == "outlook_mail_details":
            if user not in self.outlook365_clients:
                try:
                    self.outlook365_clients[user] = OutlookClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            if debug: print(f"Getting email details: {args['email_id']}")
            email_details = self.outlook365_clients[user].get_email_details(args['email_id'])
            results = email_details
        elif tool_name == "date_time":
            if debug: print(f"Getting the date and time")
            results = f"The current date and time is: {datetime.datetime.now()}"
        else:
            results =  "Tool not supported"

        # Check if the results are greater than 100k characters and truncate if necessary
        if len(results) > 100000:
            results = results[:100000] + '... (truncated due to length)'
        return results