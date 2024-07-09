import requests

class OllamaMulti():
    def __init__(self, api_base_url='http://localhost:11434',model = 'llama3', info_link='https://ollama.com/library'):
        self.api_base_url = api_base_url
        self.model = model
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.conversation_history = {}
        self.info_link = info_link

    def generate(self, user, prompt, options=None, stream=False):

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

    def check_for_previous_conversation(self, user):
        # Check if the user has actual conversation history in self.conversation_history
        if user in self.conversation_history and len(self.conversation_history[user]) > 1:
            return True

    def clear_conversation(self,user):
        self.conversation_history[user] = []
        return "Conversation cleared."

# Test Cell
# Please do not modify
# The following test cell is used to test the implementation of the `OllamaModel` class to ensure it works as expected.

# Verify the file is being run directly
if __name__ == '__main__':
    try:
        ollama_test = OllamaMulti()
        response = ollama_test.generate('1+1?')
        print(response)
        response = ollama_test.generate('Why?')
        print(response)
        response = ollama_test.generate('What was the original question?')
        print(response)
        response = ollama_test.clear_conversation()
        response = ollama_test.generate('What was the original question?')
        print(response)
    except Exception as e:
        print(e)
