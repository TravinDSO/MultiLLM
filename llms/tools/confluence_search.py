import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

class ConfluenceSearch:
    def __init__(self, url, api_token):
        self.url = url
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

    def search(self, search_string, num_results=1):
        #cql = f'siteSearch ~ "{search_string}"'
        cql = search_string
        search_url = f'{self.url}/rest/api/content/search'
        params = {
            'cql': cql,
            'limit': num_results
        }
        page_ids, page_contents = [], []

        try:
            response = requests.get(search_url, headers=self.headers, params=params)
            response.raise_for_status()
            confluence_search_results = response.json().get('results', [])

            #print(f"Search URL: {search_url}")
            #print(f"Params: {params}")
            #print(f"Response Status Code: {response.status_code}")
            #print(f"Response JSON: {response.json()}")

            for each in confluence_search_results:
                if each['type'] == 'page':
                    page_id = each['id']
                    page_ids.append(page_id)
                    
                    page_content_url = f'{self.url}/rest/api/content/{page_id}?expand=body.storage'
                    page_response = requests.get(page_content_url, headers=self.headers)
                    page_response.raise_for_status()
                    page_content = page_response.json()
                    
                    if 'body' in page_content and 'storage' in page_content['body']:
                        title = page_content['title']
                        url = f"{self.url}/pages/viewpage.action?pageId={page_id}"
                        body = BeautifulSoup(page_content['body']['storage']['value'], 'html.parser').get_text()
                        content = f"----\nPage: {title}\n{title} URL: {url}\n{title} Content: {body}\n----\n"
                        page_contents.append(content)
            return page_contents
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return "Could not retrieve search results"

# Test Cell
# Please do not modify
if __name__ == '__main__':
    try:
        # Load the env file
        load_dotenv('environment.env', override=True)

        confluence_search = ConfluenceSearch(os.getenv('CONFLUENCE_URL'), os.getenv('CONFLUENCE_TOKEN'))
        results = confluence_search.search('type=page AND text~"Myers-Briggs workshops"', num_results=3)
        for result in results:
            print(f"Page text: {result}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
