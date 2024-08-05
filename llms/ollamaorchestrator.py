import json
import datetime
from llms.ollamamulti import OllamaMulti
from llms.tools.google_search import GoogleSearch
from llms.tools.confluence_search import ConfluenceSearch
from llms.tools.jira_search import JiraSearch
from llms.tools.office365 import OutlookClient
from llms.tools.weather import WeatherChecker

class OllamaOrchestrator(OllamaMulti):
    def __init__(self, api_base_url='http://localhost:11434', model='llama3.1', info_link='', wait_limit=300,
                 google_key="", google_cx="",confluence_url="",confluence_token="",jira_url="",jira_token="",openweathermap_key=""):
        # Call the parent class constructor
        super().__init__(api_base_url, model, info_link, wait_limit)

        # Tools
        self.websearch = GoogleSearch(google_key, google_cx)
        self.confluence_search = ConfluenceSearch(confluence_url, confluence_token)
        self.jira_search = JiraSearch(jira_url, jira_token)
        self.outlook365_clients = {}
        self.weather_checker = WeatherChecker(openweathermap_key)

        # Agents
        self.llama3_1_agent = OllamaMulti(api_base_url, 'llama3.1:latest')

        self.verify_answers_asked = True
        self.agent_instructions = """
        You are an orchestrator agent. You should maximize the use of the tools available to you.
        Always get the current date and time using the date_time tool before starting to answer a question that is time or date based.
        Always use the get_weather and get_forcast tools to check the current weather, temperature and forecast for a location.
        Use the web_search tool to find real-time information that may not be available in the model.
        If someone asks for information from the Wiki or Confluence, you should use the confluence_search tool. The confluence_search tool also contains information relating to the our business, Cvent.
        Use the mail tools to search user mail for information. Include a time range and supporting information if nessesary.
        Only use the outlook_mail_details tool if you need more information on a specific email, start with the outlook_search tool first.
        Use the search_calendar_events tool to search calendars for information. Include a time range and supporting information if nessesary.
        Use the check_room_availability tool to check room availability for meetings. Include a time range and the room email address.
        Use the check_person_availability tool to check person availability for meetings. Include a time range and the person email address.
        If you are asked for availability, this means you should check for non-meeting times/dates.
        If you are asked to search for non-specific things such as 'meetings' or 'events', just search with '*' as the search string.
        If you are asked for availability, this means you should check for non-meeting times/dates.
        For all tools, you may also ask follow-up questions to get more information.
        Links should always be HTML formatted using href so they can be clicked on. Example: <a href="https://www.example.com" target"_blank">Page Title</a>
        Images responses should be formatted in HTML to display the image. Example: <img src="https://www.example.com/image.jpg" alt="image">
        Use the agent_mathmatician tool when attempting to solve mathmatical or logical problems. Include all supporting information in the prompt.
        Use the agent_researcher tool when attempting to respond to highly factual or technical prompts. This tool will provide you with feedback to improve your response.
        If needed, the final response should flow through the agent_writer tool to generate a well formed response.
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
            },{
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
                    "name": "get_weather",
                    "description": "Check the current weather for a location.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                        "type": "string",
                        "description": "The latitude decimal (-90; 90) of the location to check the current weather."
                        },
                        "longitude": {
                        "type": "string",
                        "description": "The longitude decimal (-180; 180) of the location to check the current weather."
                        }
                    },
                    "required": ["latitude" , "longitude"]
                    }
                }
            },{
            "type": "function",
            "function": {
                    "name": "get_forecast",
                    "description": "Check the weather forecast for a location.",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                        "type": "string",
                        "description": "The latitude decimal (-90; 90) of the location to check the weather forecast."
                        },
                        "longitude": {
                        "type": "string",
                        "description": "The longitude decimal (-180; 180) of the location to check the weather forecast."
                        }
                    },
                    "required": ["latitude" , "longitude"]
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
        if tool_name == "web_search":
            self.extra_messages[user].append(f'<HR><i>Searching the web for: {tool_args["search_string"]}</i>')
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
            self.extra_messages[user].append(f'<HR><i>Searching Confluence for: {tool_args["search_string"]}</i>')
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
            self.extra_messages[user].append(f'<HR><i>Searching JIRA for: {tool_args["JQL"]}</i>')
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
        elif tool_name == "outlook_search":
            msg_details = ""
            # Check if the user has a Outlook client
            if user not in self.outlook365_clients:
                try:
                    self.outlook365_clients[user] = OutlookClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"

            start_date = tool_args['start_date']
            end_date = tool_args['end_date']
            query = tool_args['search_string']

            self.extra_messages[user].append(f'<HR><i>Searching Outlook Mail: {start_date} to {end_date} for {query}</i>')

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
                return msg_details
            else:
                return 'No messages found.'
        elif tool_name == "outlook_mail_details":
            if user not in self.outlook365_clients:
                try:
                    self.outlook365_clients[user] = OutlookClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            self.extra_messages[user].append(f'<HR><i>Getting Outlook Mail Details for: {tool_args["email_id"]}</i>')
            email_details = self.outlook365_clients[user].get_email_details(tool_args['email_id'])
            return email_details
        if tool_name == "search_calendar_events":
            events = None
            evt_details = ""
            # Check if the user has a Outlook client
            if user not in self.outlook365_clients:
                try:
                    self.outlook365_clients[user] = OutlookClient(user)
                except Exception as e:
                    return f"An error occurred: {e}"
            
            start_date = tool_args['start_date']
            end_date = tool_args['end_date']
            query = tool_args['search_string']

            self.extra_messages[user].append(f'<HR><i>Searching Outlook Calendar: {start_date} to {end_date} for {query}</i>')
            events = self.outlook365_clients[user].search_calendar_events(query, start_date, end_date)

            if events:
                for event in events:
                     start = event['start'].get('dateTime', event['start'].get('date'))
                     evt_details += f"{start}: {event['subject']}\n"
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
            room_email = tool_args['room_email']
            start_date = tool_args['start_date']
            end_date = tool_args['end_date']
            self.extra_messages[user].append(f'<HR><i>Checking room availability for {room_email} from {start_date} to {end_date}</i>')
            try:
                availability = self.outlook365_clients[user].check_room_availability(room_email, start_date, end_date)
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
            person_email = tool_args['person_email']
            start_date = tool_args['start_date']
            end_date = tool_args['end_date']
            self.extra_messages[user].append(f'<HR><i>Checking person availability for {person_email} from {start_date} to {end_date}</i>')
            try:
                availability = self.outlook365_clients[user].check_person_availability(person_email, start_date, end_date)
                return availability
            except Exception as e:
                return f"An error occurred: {e}"
        elif tool_name == "get_weather":
            self.extra_messages[user].append(f'<HR><i>Getting the weather for latitude: {tool_args["latitude"]} and longitude: {tool_args["longitude"]}</i>')
            results = json.dumps(self.weather_checker.get_weather(tool_args['latitude'], tool_args['longitude']))
        elif tool_name == "get_forecast":
            self.extra_messages[user].append(f'<HR><i>Getting the forecast for latitude: {tool_args["latitude"]} and longitude: {tool_args["longitude"]}</i>')
            results = json.dumps(self.weather_checker.get_forecast(tool_args['latitude'], tool_args['longitude']))
        elif tool_name == "date_time":
            self.extra_messages[user].append(f'<HR><i>Getting the current date and time</i>')
            results = f"The current date and time is: {datetime.datetime.now()}"
        elif tool_name == "agent_writer":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Writer</i>')
            agent_prompt = f"You are a professional writer. Use the information and instructions provided to write a response to the original question:{prompt}. Information and instructions: {tool_args['information']}"
            self.conversation_history[user].append({
                'role': 'user',
                'content': agent_prompt
            })
            self.llama3_1_agent.conversation_history[user] = self.conversation_history[user]
            results = self.llama3_1_agent.generate(user, agent_prompt)
        elif tool_name == "agent_researcher":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Researcher</i>')
            agent_prompt = f"You are a professional researcher and analyst. Use the information and instructions provided to research and provide feedback to the original question: {prompt}. Information and instructions: {tool_args['information']}"
            self.conversation_history[user].append({
                'role': 'user',
                'content': agent_prompt
            })
            self.llama3_1_agent.conversation_history[user] = self.conversation_history[user]
            results = self.llama3_1_agent.generate(user, agent_prompt)
        elif tool_name == "agent_mathmatician":
            self.extra_messages[user].append(f'<HR><i>Asking the Agent Mathmatician</i>')
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