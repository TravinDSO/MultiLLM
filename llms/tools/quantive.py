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

    def search(self, query_string):
        goal_search_results = self.search_goals(query_string)
        goal_formatted_results = self.format_goals(goal_search_results)
        metric_search_results = self.search_metrics(query_string)
        metric_formatted_results = self.format_metrics(metric_search_results)
        return goal_formatted_results + metric_formatted_results

    def search_goals(self, query_string):
        search_endpoint = f'{self.base_url}/goals?{query_string}'
        headers = self._get_headers()

        try:
            response = requests.get(search_endpoint, headers=headers)
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            return None

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def search_metrics(self, query_string):
        search_endpoint = f'{self.base_url}/metrics?{query_string}'
        headers = self._get_headers()

        try:
            response = requests.get(search_endpoint, headers=headers)
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}')
            return None

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def format_goals(self, search_results):
        output = ""
        for objective in search_results.get('items', []):
            url = objective.get('url', "")
            title = objective.get('name', "")
            desc = objective.get('description', "")
            status = objective.get('closedStatus', {}).get('status', "")

            output += f'[Objective] Title: {title}\nDescription: {desc}\nStatus: {status}\nURL: {url}\n\n'
        return output
    
    def format_metrics(self, search_results):
        output = ""
        for metric in search_results.get('items', []):
            url = metric.get('url', "")
            title = metric.get('name', "")
            desc = metric.get('description', "")
            status = metric.get('closedStatus', {}).get('status', "")

            output += f'[Key Result] Title: {title}\nDescription: {desc}\nStatus: {status}\nURL: {url}\n\n'
        return output


if __name__ == '__main__':

    load_dotenv('environment.env', override=True)

    API_KEY = os.getenv('QUANTIVE_API_KEY')
    BASE_URL = os.getenv('QUANTIVE_API_BASE_URL')
    ACCOUNT_ID = os.getenv('QUANTIVE_ACCOUNT_ID')

    # https://developer.quantive.com/api-reference/results/filtering.html

    # Define the filters as a Python dictionary
    search_text = 'Portfolio health'
    text_search_filter = r'{name:{$regex: ".*' + search_text + '.*"}}'
    search_fields = 'url,name,description,closedStatus'

    # Combine the filter and fields parameters into a query string
    query_string = f'filter={text_search_filter}&fields={search_fields}'

    quantive_api = QuantiveAPI(API_KEY, BASE_URL, ACCOUNT_ID)
    try:
        goal_search_results = quantive_api.search_goals(query_string)
        goal_formatted_results = quantive_api.format_goals(goal_search_results)
        metric_search_results = quantive_api.search_metrics(query_string)
        metric_formatted_results = quantive_api.format_metrics(metric_search_results)
        print(goal_formatted_results + metric_formatted_results)
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')