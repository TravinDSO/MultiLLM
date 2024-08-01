import requests
import ollama
import json
import time

class OllamaMulti():
    def __init__(self, api_base_url='http://localhost:11434', model='llama3.1', info_link='https://ollama.com/library', wait_limit=300):
        self.api_base_url = api_base_url
        self.model = model
        self.conversation_history = {}
        self.extra_messages = {}
        self.info_link = info_link
        self.wait_limit = wait_limit
        self.agent_instructions = None
        self.tools = []
        self.verify_answers_asked = False

    def generate(self, user, prompt, tool_use=True):
        if user not in self.conversation_history:
            self.conversation_history[user] = []

        prompt_with_instructions = f'{self.agent_instructions}\nQuestion: {prompt}'
        self.conversation_history[user].append({
            'role': 'user',
            'content': prompt_with_instructions
        })

        # First response from the model
        try:
            if tool_use:
                self.response = ollama.chat(
                    model=self.model,
                    messages=self.conversation_history[user],
                    tools=self.tools,
                    stream=False
                )
            else:
                self.response = ollama.chat(
                    model=self.model,
                    messages=self.conversation_history[user],
                    stream=False
                )
        except Exception as e:
            print(f"Top level LLM request error: {e}")
            return f"Top level LLM request error: {e}"

        if self.response['message'].get('tool_calls'):
            for tool_call in self.response['message']['tool_calls']:
                tool_name = tool_call['function']['name']

                if isinstance(tool_call['function']['arguments'], dict):
                    tool_args = tool_call['function']['arguments']
                else:
                    tool_args = json.loads(tool_call['function']['arguments'])

                tool_response = self.handle_tool(user, tool_name, tool_args, prompt)

                self.conversation_history[user].append({
                    'role': 'tool',
                    'content': tool_response
                })

            # Process the response again after the tool calls
            try:
                self.response = ollama.chat(
                    model=self.model,
                    messages=self.conversation_history[user],
                    tools=self.tools,
                    stream=False
                )
            except Exception as e:
                print(f"Tool response error: {e}")
                return f"Tool response error: {e}"

        self.assistant_message = self.response['message']['content']
        self.conversation_history[user].append({
            'role': 'assistant',
            'content': self.assistant_message
        })
        return self.assistant_message
    
    def get_extra_messages(self, user):
        if user not in self.extra_messages:
            self.extra_messages[user] = []  # Initialize the list if the key doesn't exist
        messages = self.extra_messages[user]
        self.extra_messages[user] = []  # Clear messages after fetching
        return messages

    def handle_tool(self, user, tool_name, tool_args, prompt):
        return

    def summarize_conversation(self, user, tool_use=False):
        if user not in self.conversation_history:
            return "No conversation history found."

        # Create a string that combines all user and assistant responses
        for item in self.conversation_history[user]:
            if item['role'] == 'user':
                conversation = item['content']
            elif item['role'] == 'assistant':
                conversation += f'\n{item["content"]}'

        prompt = f'Summarize this conversation: {conversation}. If code was generated, preserve it, presenting the most complete version to the user.'
        return self.generate(user, prompt)

    def check_for_previous_conversation(self, user):
        if user in self.conversation_history and len(self.conversation_history[user]) > 1:
            return True

    def clear_conversation(self, user):
        self.conversation_history[user] = []
        return "Conversation cleared."

# Test Cell
# Please do not modify
# The following test cell is used to test the implementation of the `OllamaMulti` class to ensure it works as expected.

if __name__ == '__main__':
    try:
        ollama_test = OllamaMulti()
        response = ollama_test.generate('user', 'Why is the sky blue?')
        print(response)
        #response = ollama_test.generate('user', 'Tell me more.')
        #print(response)
        #response = ollama_test.generate('user', 'What was the original question?')
        #print(response)
        #response = ollama_test.clear_conversation('user')
        #response = ollama_test.generate('user', 'What was the original question?')
        #print(response)
    except Exception as e:
        print(e)
