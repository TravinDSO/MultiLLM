import os
import requests
from dotenv import load_dotenv

class JiraSearch:
    def __init__(self, url, api_token):
        self.url = url
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

    def search(self, jql, num_results=1):
        search_url = f'{self.url}/rest/api/2/search'
        params = {
            'jql': jql,
            'maxResults': num_results
        }

        try:
            response = requests.get(search_url, headers=self.headers, params=params)
            response.raise_for_status()
            search_results = response.json().get('issues', [])

            #print(f"Search URL: {search_url}")
            #print(f"Params: {params}")
            #print(f"Response Status Code: {response.status_code}")
            #print(f"Response JSON: {response.json()}")

            issue_summaries = []
            for issue in search_results:
                issue_key = issue.get('key')
                issue_summary = issue.get('fields', {}).get('summary', '')
                issue_description = issue.get('fields', {}).get('description', '')
                issue_summaries.append({
                    'key': issue_key,
                    'summary': issue_summary,
                    'description': issue_description
                })

            return issue_summaries
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return "Could not retrieve search results"

# Test Cell
# Please do not modify
if __name__ == '__main__':
    try:
        # Load the env file
        load_dotenv('environment.env', override=True)

        jira_search = JiraSearch(
            os.getenv('JIRA_URL'),
            os.getenv('JIRA_PERSONAL_ACCESS_TOKEN')
        )
        results = jira_search.search('project = "INN" AND summary ~ "Taxonomy"', num_results=3)
        for result in results:
            print(f"Issue Key: {result['key']}")
            print(f"Summary: {result['summary']}")
            print(f"Description: {result['description']}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
