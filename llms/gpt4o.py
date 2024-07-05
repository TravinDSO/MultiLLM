import openai
import time

class GPT4o():
    def __init__(self, api_key,assistant_id,model='gpt-4.0',info_link='https://openai.com/index/hello-gpt-4o/'):
        self.client = openai.Client()
        self.client.api_key = api_key
        self.openai_assistant_id = assistant_id
        self.openai_assistant_thread = {}
        self.info_link = info_link
        self.number_of_responses = 0

    def generate(self, user, prompt):
        # Check if the user has an openai assistant thread and create one if not
        if user not in self.openai_assistant_thread:
            self.openai_assistant_thread[user] = self.client.beta.threads.create()

        client_message = self.client.beta.threads.messages.create(
                thread_id=self.openai_assistant_thread[user].id,
                role="user",
                content=prompt
            )

        run = self.client.beta.threads.runs.create(
            thread_id=self.openai_assistant_thread[user].id,
            assistant_id=self.openai_assistant_id
        )
        start_time = time.time()
        self.wait_limit = 300
        result = ""
        while (time.time() - start_time) < self.wait_limit:
            result = self.client.beta.threads.runs.retrieve(thread_id=self.openai_assistant_thread[user].id,run_id=run.id)
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
        # Check if the user has actual conversation history in self.number_of_responses
        if user in self.openai_assistant_thread and self.number_of_responses > 0:
            return True
        else:
            return False

    def summarize_conversation(self, user):       
        prompt = 'Summarize the current conversation. If code was generated, preserve it, presenting the most complete version to the user.'
        return self.generate(user, prompt)

    def clear_conversation(self,user):
        self.client.beta.threads.delete(thread_id=self.openai_assistant_thread[user].id)
        self.openai_assistant_thread[user] = self.client.beta.threads.create()
        self.number_of_responses = 0
        return "Conversation cleared."
    
# Test Cell
# Please do not modify
# The following test cell is used to test the implementation of the `GPT4o` class to ensure it works as expected.
if __name__ == '__main__':
    try:
        #load the env file
        import os
        from dotenv import load_dotenv
        load_dotenv('environment.env', override=True)
        
        gpt4o = GPT4o(os.getenv('OPENAI_API_KEY'),os.getenv('OPENAI_ASSISTANT_ID'))

        response = gpt4o.generate('1+1?')
        print(response)
        response = gpt4o.generate('Why?')
        print(response)
    except Exception as e:
        print(e)