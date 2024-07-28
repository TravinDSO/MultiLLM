import os
from dotenv import load_dotenv
from atlassian import Confluence # pip install atlassian-python-api
from bs4 import BeautifulSoup  # pip install beautifulsoup4

class ConfluenceSearch:
    def __init__(self, url, api_token):
        self.url = url
        self.api_token = api_token
        self.confluence = Confluence(url=self.url, token=self.api_token)

    def search(self, search_string, num_results=1):
        cql = "siteSearch ~ \"" + search_string + "\""
        page_ids, page_contents = [], []
        try:
            confluence_search_results = self.confluence.cql(cql=cql,limit=num_results)['results']
            for each in confluence_search_results:
                if each['content']['type'] == 'page':
                    page_id = each['content']['id']
                    page_ids.append(page_id)
                    
                    page_content = self.confluence.get_page_by_id(page_id=page_id, expand='body.storage')
                    content = BeautifulSoup(page_content['body']['storage']['value'], 'html.parser').get_text()
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
        results = confluence_search.search('AI Power', num_results=3)
        for result in results:
            print(f"Search result link: {result[0]}")
            #print(f"Page text: {result[1]}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")