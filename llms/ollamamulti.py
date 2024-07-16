from openai import OpenAI
import time

class OllamaMulti():
    def __init__(self, api_key, model='gpt-4o', endpoint='', version='', info_link='', use_assistants=True, wait_limit=300):
        try:
            self.client = OpenAI(
                api_key=api_key,
                api_version=version,
                azure_endpoint=endpoint
            )
        except Exception as e:
            print(f'Could not create Client: {e}')
        self.use_assistants = use_assistants
        self.model = model
        self.openai_assistant_id = {}
        self.openai_assistant_thread = {}
        self.info_link = info_link
        self.wait_limit = int(wait_limit)
        self.number_of_responses = 0
        self.conversation_history = {}

    def generate(self, user, prompt):
        if self.use_assistants:
            return self.assistant_generate(user, prompt)
        else:
            return self.direct_generate(user, prompt)

    def direct_generate(self,  user,prompt):
        # Check if the user has a conversation history and create one if not
        if user not in self.conversation_history:
            self.conversation_history[user] = []

        # Append the new user prompt to the conversation history
        self.conversation_history[user].append({
            'role': 'user',
            'content': prompt
        })
        try:
            response = ''
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history[user],
                max_tokens=4000,
                temperature=0.7,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False
            )
            response = completion.choices[0].message.content
            return response
        except Exception as e:
            print(f'Could not process direct prompt to Azure: {e}')
            return f'Could not process direct prompt to Azure: {e}'

    def assistant_generate(self, user, prompt):
        # Check if the user has an Azure OpenAI ASSISTANT and create one if not
        if user not in self.openai_assistant_id:
            try:
                self.openai_assistant_id[user] = self.client.beta.assistants.create(model=self.model)
            except Exception as e:
                print(f'Could not create Azure Assistant: {e}')

        # Check if the user has an Azure OpenAI Assistant THREAD and create one if not
        if user not in self.openai_assistant_thread:
            try:
                self.openai_assistant_thread[user] = self.client.beta.threads.create()
            except Exception as e:
                print(f'Could not create Azure Assistant Thread: {e}')

        client_message = self.client.beta.threads.messages.create(
            thread_id=self.openai_assistant_thread[user].id,
            role="user",
            content=prompt
        )

        run = self.client.beta.threads.runs.create(
            thread_id=self.openai_assistant_thread[user].id,
            assistant_id=self.openai_assistant_id[user].id
        )
        start_time = time.time()
        result = ""
        while (time.time() - start_time) < self.wait_limit:
            result = self.client.beta.threads.runs.retrieve(thread_id=self.openai_assistant_thread[user].id,
                                                            run_id=run.id)
            # Check if the function returned a result and if the run is no longer queued
            if result.status == "completed":
                break
            else:
                time.sleep(1)

        if result.status != "completed":
            response = f"No response from Assistant after {self.wait_limit} seconds."
        else:
            response = self.client.beta.threads.messages.list(
                thread_id=self.openai_assistant_thread[user].id
            )
            response = response.data[0].content[0].text.value
            self.number_of_responses += 1

        return response

    def check_for_previous_conversation(self, user):
        if self.use_assistants:
            # Check if the user has actual conversation history in self.number_of_responses
            if user in self.openai_assistant_thread and self.number_of_responses > 0:
                return True
            else:
                return False
        else:
            if user in self.conversation_history and len(self.conversation_history[user]) > 1:
                return True
            else:
                return False

    def summarize_conversation(self, user):
        prompt = 'Summarize the current conversation. If code was generated, preserve it, presenting the most complete version to the user.'
        return self.generate(user, prompt)

    def clear_conversation(self, user):
        if self.use_assistants:
            self.client.beta.threads.delete(thread_id=self.openai_assistant_thread[user].id)
            self.openai_assistant_thread[user] = self.client.beta.threads.create()
            self.number_of_responses = 0
            return "Conversation cleared."
        else:
            self.conversation_history[user] = []
            return "Conversation cleared."


# Test Cell
# Please do not modify
# The following test cell is used to test the implementation of the `GPT4o` class to ensure it works as expected.
if __name__ == '__main__':
    try:
        response = ''
        # load the env file
        import os
        from dotenv import load_dotenv

        load_dotenv('../environment.env', override=True)

        azure_gpt4o = OllamaMulti(
            os.getenv('OPENAI_API_KEY'),
            'gpt-4o',
            os.getenv('OPENAI_API_ENDPOINT'),
            os.getenv('OPENAI_API_VERSION'),
            'https://openai.com/index/hello-gpt-4o/',
            False,
            30
        )

        response = azure_gpt4o.generate('user', '1+1?')
        print(response)
        response = azure_gpt4o.generate('user', 'Why?')
        print(response)
    except Exception as e:
        print(e)