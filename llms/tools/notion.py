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
    
    def retrieve_block_children(self, page_id):
        page_text_dump = ""
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

# dotenv.load_dotenv("environment.env")
# token = os.getenv('NOTION_API_KEY')

# notion_api = NotionAPI(token=token)

# # Query a database
# database_id = "" # Replace with your database ID
# try:
#     query_result = notion_api.query_database(database_id)
# except requests.exceptions.HTTPError as e:
#     print("Failed to query database:", e)

# # Retrieve block children
# database_text_dump = ""
# page_text_dump = ""
# for page in query_result['results']:
#     if page['object'] == 'page':
        
#         page_id = page['id']
#         page_title = ""
#         page_assignment = ""
#         page_last_edited = ""
#         page_url = ""
#         page_labels = ""
#         page_text_dump = ""

#         try:
#             page_title = page['properties']['Name']['title'][0]['plain_text'] if 'Name' in page['properties'] else "Untitled"
#             page_assignment = page['properties']['Status']['select']['name'] if 'Status' in page['properties'] else "Not Assigned"
#             page_due_date = page['properties']['Due']['date']['start'] if 'Due' in page['properties'] else "No Due Date"
#             page_last_edited = page['last_edited_time'] if 'last_edited_time' in page else "Unknown"
#             page_url = page['url'] if 'url' in page else "Unknown"
#             # Get labels
#             page_labels = ""
#             for label in page['properties']['Label']['multi_select']:
#                 page_labels += label['name'] + " "
#         except Exception as e:
#             page_title = f"Error parsing page {page_id}"

#         try:
#             page_text_dump += notion_api.retrieve_block_children(page_id)
#         except requests.exceptions.HTTPError as e:
#             print("Failed to retrieve block children:", e)

#         database_text_dump += f"Page Title: {page_title}\n"
#         database_text_dump += f"Page GTD Assignment: {page_assignment}\n"
#         database_text_dump += f"Page Due Date: {page_due_date}\n"
#         database_text_dump += f"Page Last Edited: {page_last_edited}\n"
#         database_text_dump += f"Page URL: {page_url}\n"
#         database_text_dump += f"Page Labels: {page_labels}\n"
#         database_text_dump += f"Page Text Dump: {page_text_dump}\n"
#         database_text_dump += "==========\n"

# Debug dump to file
# with open("notion_database_dump.txt", "w", encoding="utf-8") as f:
#     f.write(database_text_dump)