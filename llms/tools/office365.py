import os
import time
import msal
import requests
import webbrowser
import pickle
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

TOKEN_FILE = 'token.pickle'

class OutlookClient:
    def __init__(self, user):
        load_dotenv('environment.env')
        self.client_id = os.getenv('OUTLOOK_CLIENT_ID')
        self.client_secret = os.getenv('OUTLOOK_CLIENT_SECRET')
        self.tenant_id = os.getenv('OUTLOOK_TENANT_ID')
        self.redirect_uri = 'http://localhost'
        self.token = None
        self.credentials_file = f'{user}_outlook_credentials.json'
        self.token_file = f'{user}_365_token.pickle'
        self.login()

    def get_msal_app(self):
        return msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}",
            client_credential=self.client_secret
        )

    def get_authorization_url(self):
        auth_url = self.get_msal_app().get_authorization_request_url(
            scopes=["https://graph.microsoft.com/.default"],
            redirect_uri=self.redirect_uri
        )
        return auth_url

    def acquire_token_by_authorization_code(self, authorization_code):
        result = self.get_msal_app().acquire_token_by_authorization_code(
            authorization_code,
            scopes=["https://graph.microsoft.com/.default"],
            redirect_uri=self.redirect_uri
        )
        if "access_token" in result:
            self.token = result
            self.save_token(result)
        else:
            raise Exception("Could not obtain access token")

    def save_token(self, token):
        with open(self.token_file, 'wb') as f:
            pickle.dump(token, f)

    def load_token(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as f:
                token = pickle.load(f)
                return token
        return None

    def refresh_token_if_needed(self):
        token = self.load_token()
        if token:
            self.token = token
            account = self.get_msal_app().get_accounts()
            if account:
                result = self.get_msal_app().acquire_token_silent_with_error(
                    scopes=["https://graph.microsoft.com/.default"],
                    account=account[0]
                )
                if "access_token" in result:
                    self.token = result
                    self.save_token(result)
                else:
                    self.token = None

    def login(self):
        self.refresh_token_if_needed()

        if not self.token:
            auth_url = self.get_authorization_url()
            print("Open this URL in your browser and sign in:", auth_url)
            webbrowser.open(auth_url)
            returned_url = input("Enter the full URL after signing in and being redirected: ")
            authorization_code = self.extract_code_from_url(returned_url)
            self.acquire_token_by_authorization_code(authorization_code)

    def extract_code_from_url(self, url):
        parsed_url = urlparse(url)
        code = parse_qs(parsed_url.query).get('code')
        if code:
            return code[0]
        else:
            raise Exception("Authorization code not found in the URL.")

    def search_emails(self, search_query=None, start_date=None, end_date=None):
        if not self.token:
            raise Exception("Access token is not available. Please authenticate first.")
        
        if not search_query:
            search_query = "*"

        if start_date:
            start_date = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Default to 1 year ago
            start_date = (datetime.now(timezone.utc) - timedelta(days=365)).strftime('%Y-%m-%dT%H:%M:%SZ')

        if end_date:
            end_date = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Default to current date
            end_date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/messages?$search=\"{search_query}\""
        headers = {'Authorization': f'Bearer {self.token["access_token"]}'}
        
        emails = []
        while endpoint:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                emails.extend(response_data['value'])
                endpoint = response_data.get('@odata.nextLink')
                # Wait for 1 second before making the next request
                time.sleep(1)
            else:
                raise Exception(f"Error retrieving emails: {response.status_code}, {response.text}")

        # Manually filter emails by date range
        filtered_emails = [
            email for email in emails 
            if start_date <= email['receivedDateTime'] <= end_date
        ]
        return filtered_emails


    def get_email_details(self, message_id):
        if not self.token:
            raise Exception("Access token is not available. Please authenticate first.")
        endpoint = f"https://graph.microsoft.com/v1.0/me/messages/{message_id}"
        headers = {'Authorization': f'Bearer {self.token["access_token"]}'}
        response = requests.get(endpoint, headers=headers)

        if response.status_code == 200:
                message = response.json()
                subject = message.get('subject', 'No subject found.')
                sender_info = message.get('from', {}).get('emailAddress', {})
                sender = sender_info.get('address', 'No sender found.')

                to_recipients = message.get('toRecipients', [])
                if to_recipients:
                    to = to_recipients[0].get('emailAddress', {}).get('address', 'No recipient found.')
                else:
                    to = 'No recipient found.'

                date = message.get('receivedDateTime', 'No date found.')
                body = message.get('body', {}).get('content', 'No message body found.')
                email_link = f"https://outlook.office.com/mail/deeplink/compose/{message_id}"

                return f'subject: {subject}, sender: {sender}, to: {to}, date: {date}, message: {body}, link: {email_link}'
        else:
            raise Exception(f"Error retrieving email details: {response.status_code}, {response.text}")

    def search_calendar_events(self, search_query=None, start_date=None, end_date=None):
        if not self.token:
            raise Exception("Access token is not available. Please authenticate first.")

        if start_date:
            start_date = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Default to 31 days ago
            start_date = (datetime.now(timezone.utc) - timedelta(days=31)).strftime('%Y-%m-%dT%H:%M:%SZ')

        if end_date:
            end_date = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            # Default to 31 days from now
            end_date = (datetime.now(timezone.utc) + timedelta(days=31)).strftime('%Y-%m-%dT%H:%M:%SZ')

        endpoint = f"https://graph.microsoft.com/v1.0/me/calendarView?startDateTime={start_date}&endDateTime={end_date}"
        if search_query:
            endpoint += f"&$search=\"{search_query}\""
        
        headers = {'Authorization': f'Bearer {self.token["access_token"]}'}
        
        events = []
        while endpoint:
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                events.extend(response_data['value'])
                endpoint = response_data.get('@odata.nextLink')
                # Wait for 1 second before making the next request
                time.sleep(1)
            else:
                raise Exception(f"Error retrieving calendar events: {response.status_code}, {response.text}")

        return events

# Usage
if __name__ == "__main__":
    client = OutlookClient('user')

    query = "Replicon"
    
    start_date = (datetime.now(timezone.utc)) - timedelta(days=31)
    end_date = datetime.now(timezone.utc)

    emails = client.search_emails(query,start_date, end_date)

    if emails:
        for email in emails:
            email_details = client.get_email_details(email['id'])
            print(email_details)
    else:
        print('No emails found.')

    #print("\nCalendar events for today with keyword 'meeting':")
    # events = client.search_calendar_events(query,start_date, end_date)

    # if events:
    #     for event in events:
    #         start = event['start'].get('dateTime', event['start'].get('date'))
    #         print(start, event['subject'])
    # else:
    #     print('No upcoming events found.')
