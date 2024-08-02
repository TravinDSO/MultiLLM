import os
import dotenv
import requests

class NotionAPI:
    BASE_URL = "https://api.notion.com/v1"
    VERSION = "2022-06-28"
    
    def __init__(self, token):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": self.VERSION,
            "Content-Type": "application/json"
        }
    
    def query_database(self, database_id, filter=None, sorts=None):
        url = f"{self.BASE_URL}/databases/{database_id}/query"
        data = {}
        if filter:
            data["filter"] = filter
        if sorts:
            data["sorts"] = sorts
        response = requests.post(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    def retrieve_block_children(self, page_title, page_id):
        page_text_dump = "Page Title: " + page_title + "\n"
        url = f"{self.BASE_URL}/blocks/{page_id}/children"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            for block in response.json()['results']:
                if block['type'] == 'paragraph':
                    for text in block['paragraph']['rich_text']:
                        page_text_dump += text['plain_text']
            return page_text_dump
        else:
            response.raise_for_status()

# Example usage:
# Replace 'your_notion_token' with your actual Notion integration token

dotenv.load_dotenv("environment.env")
token = os.getenv('NOTION_API_KEY')

notion_api = NotionAPI(token=token)

# Query a database
database_id = "294398eabc8146f885261d5012e53c6c"
try:
    query_result = notion_api.query_database(database_id)
except requests.exceptions.HTTPError as e:
    print("Failed to query database:", e)

# Retrieve block children
database_text_dump = ""
for page in query_result['results']:
    if page['object'] == 'page':
        page_id = page['id']
        try:
            page_title = page['properties']['Name']['title'][0]['plain_text']
        except Exception as e:
            page_title = "Untitled"
        try:
            database_text_dump += notion_api.retrieve_block_children(page_title,page_id)
        except requests.exceptions.HTTPError as e:
            print("Failed to retrieve block children:", e)

#block_children[0]['results'][0]['paragraph']['rich_text'][0]['plain_text']

print(database_text_dump)

#page_id = "your_page_id"
#try:
#    block_children = notion_api.retrieve_block_children(page_id)
#    print("Block Children Result:", block_children)
#except requests.exceptions.HTTPError as e:
#    print("Failed to retrieve block children:", e)
