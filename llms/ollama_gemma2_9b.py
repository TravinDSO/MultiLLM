import requests

class Gemma2_9b():
    def __init__(self, api_base_url='http://localhost:11434'):
        self.api_base_url = api_base_url
        self.model = 'gemma2'
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.conversation_history = []
        self.info_link = 'https://developers.googleblog.com/en/gemma-family-and-toolkit-expansion-io-2024/'

    def generate(self, prompt, options=None, stream=False):
        # Append the new user prompt to the conversation history
        self.conversation_history.append({
            'role': 'user',
            'content': prompt
        })
        
        payload = {
            'model': self.model,
            'messages': self.conversation_history,  # Use the conversation history
            'stream': stream
        }
        
        if options:
            payload['options'] = options

        response = requests.post(
            f'{self.api_base_url}/api/chat',
            headers=self.headers,
            json=payload
        )
        
        if stream:
            responses = []
            for line in response.iter_lines():
                if line:
                    responses.append(line.decode('utf-8'))
            return responses
        else:
            if response.status_code == 200:
                parsed_response = response.json()
                assistant_message = parsed_response['message']['content']
                # Append the assistant's response to the conversation history
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': assistant_message
                })
                return assistant_message
            else:
                response.raise_for_status()

    def clear_conversation(self):
        self.conversation_history = []
        return "Conversation cleared."

# Test Cell
# Please do not modify
# The following test cell is used to test the implementation of the `Gemma2` class to ensure it works as expected.

# Verify the file is being run directly
if __name__ == '__main__':
    try:
        gemma2 = Gemma2_9b()
        response = gemma2.generate('1+1?')
        print(response)
        response = gemma2.generate('Why?')
        print(response)
        response = gemma2.generate('What was the original question?')
        print(response)
        response = gemma2.clear_conversation()
        response = gemma2.generate('What was the original question?')
        print(response)
    except Exception as e:
        print(e)
