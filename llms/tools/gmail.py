import os
import base64
import pickle
from google.auth.transport.requests import Request  # pip install google-auth
from google_auth_oauthlib.flow import InstalledAppFlow # pip install google-auth-oauthlib
from googleapiclient.discovery import build # pip install google-api-python-client

# Create a Project in the Google Developers Console:
    # Go to the Google Developers Console: https://console.developers.google.com/
    # Create a new project
    # Enable the Gmail API for your project
    # Enable the Calendar API for your project
    # Create OAuth 2.0 credentials (Desktop App) and download the credentials file (credentials.json)
    # Store the credentials file:
        # Save the downloaded credentials.json file in root directory of the project adding your username to the file: user_gmail_credentials.json
# The first time you run this class, it will open a browser window asking you to log in to your Google account and authorize the application
# The class will save the credentials in a user_token.pickle file for future use

class GmailClient:
    def __init__(self, user):
        self.creds = None
        self.credentials_file = f'{user}_gmail_credentials.json'
        self.token_file = f'{user}_token.pickle'
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.labels',
            'https://www.googleapis.com/auth/calendar.readonly'
        ]
        self.service = None
        self.calendar_service = None
        self.login()

    def login(self):
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('gmail', 'v1', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)

    def search_emails(self, query):
        try:
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            return messages
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def get_email_details(self, message_id):
        try:
            message = self.service.users().messages().get(userId='me', id=message_id).execute()
            payload = message.get('payload')
            headers = payload.get('headers', [])
            parts = payload.get('parts', [])
            snippet = message.get('snippet')
            body_data = None

            if parts:
                for part in parts:
                    if part.get('body', {}).get('data'):
                        body_data = part['body']['data']
                        break
            else:
                body_data = payload.get('body', {}).get('data')

            subject = 'No subject found.'
            sender = 'No sender found.'
            date = 'No date found.'
            to = 'No recipient found.'

            for header in headers:
                name = header.get('name')
                value = header.get('value')
                if name == 'Subject':
                    subject = value
                elif name == 'From':
                    sender = value
                elif name == 'Date':
                    date = value
                elif name == 'To':
                    to = value

            if body_data:
                msg_str = base64.urlsafe_b64decode(body_data).decode('utf-8')
            elif snippet:
                msg_str = snippet
            else:
                msg_str = "No message body found."

            email_link = f"https://mail.google.com/mail/u/0/#inbox/{message_id}"

            return f'subject: {subject}, sender: {sender}, to: {to}, date: {date}, message: {msg_str}, link: {email_link}'
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def mark_as_read(self, message_id):
        try:
            self.service.users().messages().modify(
                userId='me', id=message_id, body={'removeLabelIds': ['UNREAD']}).execute()
            print(f'Message {message_id} marked as read.')
        except Exception as e:
            print(f'An error occurred: {e}')

    def archive_email(self, message_id):
        try:
            self.service.users().messages().modify(
                userId='me', id=message_id, body={'removeLabelIds': ['INBOX']}).execute()
            print(f'Message {message_id} archived.')
        except Exception as e:
            print(f'An error occurred: {e}')

    def delete_email(self, message_id):
        try:
            self.add_label(message_id, 'deleteme')
            self.mark_as_read(message_id)
            print(f'Message {message_id} deleted.')
        except Exception as e:
            print(f'An error occurred: {e}')

    def list_labels(self):
        labels_list = ""
        try:
            labels = self.service.users().labels().list(userId='me').execute()
            for label in labels['labels']:
                labels_list += f"Label name: {label['name']}, Label ID: {label['id']}\n"
            # print(labels_list)
            return labels_list
        except Exception as e:
            print(f'An error occurred while listing labels: {e}')
            return None

    def create_label(self, label_name):
        label = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }
        try:
            created_label = self.service.users().labels().create(userId='me', body=label).execute()
            print(f"Label {label_name} created with ID: {created_label['id']}")
            return created_label['id']
        except Exception as e:
            print(f'An error occurred while creating label: {e}')
            return None

    def get_label_id(self, label_name):
        try:
            labels = self.service.users().labels().list(userId='me').execute()
            for label in labels['labels']:
                if label['name'] == label_name:
                    return label['id']
            return None
        except Exception as e:
            print(f'An error occurred while retrieving label ID: {e}')
            return None

    def add_label(self, message_id, label_name):
        try:

            try:
                label_id = self.get_label_id(label_name)
                if not label_id:
                    label_id = label_name    
            except Exception as e:
                label_id = label_name

            self.service.users().messages().modify(
                userId='me', id=message_id, body={'addLabelIds': [label_id]}).execute()
            print(f'Label {label_id} added to message {message_id}.')
        except Exception as e:
            print(f'An error occurred: {e}')

    def search_calendar_events(self, time_min, time_max, query=None):
        try:
            events_result = self.calendar_service.events().list(
                calendarId='primary', timeMin=time_min, timeMax=time_max,
                maxResults=100, singleEvents=True, orderBy='startTime', q=query).execute()
            events = events_result.get('items', [])
            return events
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

# Usage
if __name__ == "__main__":
    client = GmailClient('user')

    from datetime import datetime, timedelta, timezone
    start_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    end_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    print("Emails from yesterday:")
    email_query = f'after:{start_date}'
    emails = "" #client.search_emails(email_query)

    if emails:
        for email in emails:
            email_details = client.get_email_details(email['id'])
            print(email_details)
    else:
        print('No emails found.')

    email_id = "19115bbe68bc7f4e"


    try:
        #client.mark_as_read(email_id)
        #client.archive_email(email_id)
        #client.delete_email(email_id)
        #client.add_label(email_id, 'deleteme')  # Replace 'Label_1_ID' with the actual label ID
        client.list_labels()
        #client.create_label('Test21')
    except Exception as e:
        print(f'An error occurred: {e}')

    #print("\nCalendar events for today with keyword 'meeting':")
    events = "" #client.search_calendar_events(start_date, end_date, query='meeting')

    if events:
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
    else:
        print('No upcoming events found.')
