import os
import requests
from dotenv import load_dotenv

class QuantiveAPI:
    def __init__(self, api_key, base_url, account_id):
        self.api_key = api_key
        self.base_url = base_url
        self.account_id = account_id

    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'gtmhub-accountId': self.account_id,
            'Content-Type': 'application/json'
        }

    def search_goals(self, search_params):
        search_endpoint = f'{self.base_url}/goals'
        headers = self._get_headers()

        response = requests.get(search_endpoint, headers=headers, params=search_params)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def format_search_results(self, search_results):
        output = ""
        for objective in search_results.get('items', []):
            url = objective.get('url', "")
            title = objective.get('name', "")
            desc = objective.get('description', "")
            status = objective.get('closedStatus', {}).get('status', "")

            output += f'Title: {title}\nDescription: {desc}\nStatus: {status}\nURL: {url}\n\n'
        return output


if __name__ == '__main__':

    load_dotenv('environment.env', override=True)

    API_KEY = os.getenv('QUANTIVE_API_KEY')
    BASE_URL = os.getenv('QUANTIVE_API_BASE_URL')
    ACCOUNT_ID = os.getenv('QUANTIVE_ACCOUNT_ID')

    search_params = {
        'filter': '{name: {$in: ["Project Management", "Software Development"]}}',
        'fields': 'url,name,description,closedStatus'
    }

    quantive_api = QuantiveAPI(API_KEY, BASE_URL, ACCOUNT_ID)
    try:
        search_results = quantive_api.search_goals(search_params)
        formatted_results = quantive_api.format_search_results(search_results)
        print(formatted_results)
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')