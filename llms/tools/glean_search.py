import os
import requests
from dotenv import load_dotenv

class GleanSearch:
    def __init__(self, url, api_token, auth_type='', act_as_email=None):
        # Initialize with the Glean API base URL and token
        self.url = url.rstrip('/')  # remove trailing slash if any
        self.api_token = api_token
        self.auth_type = auth_type
        self.act_as_email = act_as_email
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'X-Glean-Auth-Type': self.auth_type
        }
        if self.act_as_email:
            self.headers['X-Scio-ActAs'] = self.act_as_email

    def search(self, query, page_size=10):
        """
        Searches Glean documents using the given query and returns a list of formatted result strings.
        """
        search_url = f"{self.url}/search"
        payload = {
            "query": query,
            "pageSize": page_size,
            "requestOptions": {}  # Extend with additional options if needed
        }

        try:
            response = requests.post(search_url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            results_list = []
            for result in data.get('results', []):
                title = result.get('title', 'No Title')
                url = result.get('url', 'No URL')
                snippets = result.get('snippets', [])
                snippet_text = ''
                for snippet in snippets:
                    # Only add the snippet if it's not empty
                    if snippet.get('text'):
                        snippet_text += snippet.get('text')
                    else:
                        snippet_text += 'No text available'
                content = f"----\nDocument: {title}\nURL: {url}\nSnippet: {snippet_text}\n----\n"
                results_list.append(content)



            return results_list
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return ["Could not retrieve search results"]

    def chat(self, messages, agent="GPT", timezone_offset=0):
        # Construct the chat URL with timezone offset as query parameter
        chat_url = f"{self.url}/chat?timezoneOffset={timezone_offset}"
        # Format messages to the required payload structure
        formatted_messages = []
        for msg in messages:
            if 'role' in msg and 'content' in msg:
                formatted_messages.append({
                    "author": "USER" if msg['role'].lower() == "user" else msg['role'].upper(),
                    "messageType": "CONTENT",
                    "fragments": [{"text": msg['content']}]
                })
            else:
                formatted_messages.append(msg)
        payload = {
            "agentConfig": {"agent": agent},
            "messages": formatted_messages
        }
        try:
            response = requests.post(chat_url, headers=self.headers, json=payload)
            response.raise_for_status()
            data = response.json()
            primary_message = None
            for msg in data.get("messages", []):
                if msg.get("messageType") == "CONTENT":
                    primary_message = ''.join(fragment.get("text", "") for fragment in msg.get("fragments", []))
                    break
            if primary_message:
                return [primary_message]
            else:
                return [response.text]
        except Exception as e:
            print(f"An error occurred during chat request: {str(e)}")
            return {"error": str(e)}

# Test Cell
# Please do not modify
if __name__ == '__main__':
    try:
        load_dotenv('environment.env', override=True)
        glean_api_url = os.getenv('GLEAN_API_URL')
        glean_token = os.getenv('GLEAN_TOKEN')
        act_as_email = None #os.getenv('GLEAN_ACT_AS_EMAIL')  # Optional; required if using GLOBAL tokens

        glean_search = GleanSearch(glean_api_url, glean_token, act_as_email=act_as_email)
        results = glean_search.chat([{"role": "user", "content": "What is Project Management?"}], agent="DEFAULT") # GPT = Websearch, DEFAULT = Company Knowledge
        for result in results:
            print(result)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
