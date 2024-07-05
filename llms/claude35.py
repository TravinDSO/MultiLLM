import requests

class Claude35():
    def __init__(self, api_key, api_base_url='https://api.anthropic.com', model='claude-3-5-sonnet-20240620',info_link='https://www.anthropic.com/news/claude-3-5-sonnet'):
        self.api_base_url = api_base_url
        self.model = model
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
        self.conversation_history = {}
        self.info_link = info_link

    def generate(self, user, prompt, max_tokens=2000, stop_sequences=None, temperature=1.0):
        
        # Check if the user has a conversation history and create one if not
        if user not in self.conversation_history:
            self.conversation_history[user] = []
        
        # Append the new user prompt to the conversation history
        self.conversation_history[user].append({
            'role': 'user',
            'content': prompt
        })
        
        payload = {
            'model': self.model,
            'messages': self.conversation_history[user],  # Use the conversation history
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        if stop_sequences:
            payload['stop_sequences'] = stop_sequences

        response = requests.post(
            f'{self.api_base_url}/v1/messages',
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            parsed_response = response.json()
            assistant_message = parsed_response['content'][0]['text']
            # Append the assistant's response to the conversation history
            self.conversation_history[user].append({
                'role': 'assistant',
                'content': assistant_message
            })
            return assistant_message
        else:
            response.raise_for_status()

    def summarize_conversation(self, user):
        # Check if the user has a conversation history and create one if not
        if user not in self.conversation_history:
            # Short-circuit if the user has no conversation history and return a message informing them of this
            self.conversation_history[user] = []
            return "No conversation history found."
        
        prompt = 'Summarize the current conversation. If code was generated, preserve it, presenting the most complete version to the user.'
        return self.generate(user, prompt)

    def clear_conversation(self,user):
        self.conversation_history[user] = []
        return "Conversation cleared."

# Test Cell
# Please do not modify
# The following test cell is used to test the implementation of the `Claude35` class to ensure it works as expected.

# Verify the file is being run directly
if __name__ == '__main__':
    # Load the env file
    import os
    from dotenv import load_dotenv
    load_dotenv('environment.env', override=True)
        
    try:
        claude = Claude35(os.getenv('CLAUDE_API_KEY'), api_base_url='https://api.anthropic.com')
    except Exception as e:
        print(f'Class Error: {e}')

    try:
        response = claude.generate('user','1+1?')
        print(response)
        response = claude.generate('user','Why?')
        print(response)
        response = claude.generate('user','What was the original question?')
        print(response)
        response = claude.clear_conversation('user')
        response = claude.generate('user','What was the original question?')
        print(response)
    except Exception as e:
        print(f'Runup Error:{e}')
