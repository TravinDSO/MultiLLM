# Google Search API
import requests
from bs4 import BeautifulSoup  # pip install beautifulsoup4

class GoogleSearch:
    def __init__(self, api_key, google_cx):
        self.api_key = api_key
        self.google_cx = google_cx
    
    def search(self,search_string):
            google_search_url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.google_cx}&q={search_string}"

            try:
                # Fetch the top search result from Google Custom Search
                search_response = requests.get(google_search_url)
                search_response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code
                data = search_response.json()

                if 'items' in data:
                    top_result_link = data['items'][0]['link']

                    # Fetch the content from the top search result link
                    page_response = requests.get(top_result_link)
                    page_response.raise_for_status()  # Raise an HTTPError for the page request if the HTTP request returned an unsuccessful status code

                    try:
                        # Parse the content with BeautifulSoup
                        soup = BeautifulSoup(page_response.text, 'html.parser')
                        page_text = soup.get_text(separator='\n', strip=True)
                    except Exception as e:
                        page_text = "Content could not be retrieved from page"

                    return top_result_link, page_text
                else:
                    return None, "No items found in search results"
            except requests.RequestException as e:
                print(f"HTTP Request failed: {e}")
                return None, str(e)
            
# Test Cell
# Please do not modify
if __name__ == '__main__':
    try:
        #load the env file
        import os
        from dotenv import load_dotenv
        load_dotenv('environment.env', override=True)

        google_search = GoogleSearch(os.getenv('GOOGLE_API_KEY'), os.getenv('GOOGLE_CX'))
        top_result_link, page_text = google_search.search('Top news today')
        print(f"Top search result link: {top_result_link}")
        print(f"Page text: {page_text}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")