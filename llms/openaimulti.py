import openai
import time
import json

class OpenaiMulti():
    def __init__(self, api_key,model='gpt-4o',info_link='',wait_limit=300, type='chat',assistant_functions=None):
        self.client = openai.Client()
        self.client.api_key = api_key
        self.openai_assistant_id = {}
        self.openai_assistant_thread = {}
        self.model = model
        self.info_link = info_link
        self.number_of_responses = 0
        self.wait_limit = int(wait_limit)
        self.type = type
        self.conversation_history = {}
        self.assistant_functions = assistant_functions if assistant_functions else []

    def generate(self, user, prompt):
        if self.type == 'assistant':
            return self.assistant_generate(user, prompt)
        elif self.type == 'chat':
            return self.direct_generate(user, prompt)
        elif self.type == 'image':
            return self.image_generate(user, prompt)
        else:
            return "Not supported"
    
    def image_generate(self, user, prompt):
        try:
            image = self.client.images.generate(
                    model=self.model,
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
            )
                
            # Return the image in a HTML tag
            return f'<img src="{image.data[0].url}" alt={prompt} style="max-width: 100%;">'
        except Exception as e:
            print(f'Could not process image prompt to OpenAI: {e}')
            return f'Could not process image: {e}'

    def direct_generate(self, user, prompt):
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
            print(f'Could not process direct prompt to OpenAI: {e}')
            return f'Could not process direct prompt to OpenAI: {e}'

    def assistant_generate(self, user, prompt):
        # Check if the user has an Azure OpenAI ASSISTANT and create one if not
        if user not in self.openai_assistant_id:
            try:
                self.openai_assistant_id[user] = self.client.beta.assistants.create(model=self.model)
                # Update openai_assistants.json with the new assistant id
                with open('openai_assistants.json', 'w') as f:
                    # If data existing append the id to the json file, otherwise create a new json file
                    try:
                        data = json.load(f)
                        data[user] = self.openai_assistant_id[user].id
                        json.dump(data, f)
                    except:
                        data = {user: self.openai_assistant_id[user].id}
                        json.dump(data, f)
            except Exception as e:
                print(f'Could not create Assistant: {e}')

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
            assistant_id=self.openai_assistant_id[user].id,
        )
        start_time = time.time()
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
        if self.type == 'assistant':
            # Check if the user has actual conversation history in self.number_of_responses
            if user in self.openai_assistant_thread and self.number_of_responses > 0:
                return True
            else:
                return False
        elif self.type == 'chat':
            # Check if the user has actual conversation history in self.conversation_history
            if user in self.conversation_history and len(self.conversation_history[user]) > 1:
                return True
            else:
                return False
        else:
            return False

    def summarize_conversation(self, user):
        if self.type in ['assistant','chat']:    
            prompt = 'Summarize the current conversation. If code was generated, preserve it, presenting the most complete version to the user.'
            return self.generate(user, prompt)
        else:
            return "Not supported"

    def clear_conversation(self,user):
        if self.type == 'assistant':
            self.client.beta.threads.delete(thread_id=self.openai_assistant_thread[user].id)
            self.openai_assistant_thread[user] = self.client.beta.threads.create()
            self.number_of_responses = 0
            return "Conversation cleared."
        elif self.type == 'chat':
            self.conversation_history[user] = []
            return "Conversation cleared."
        else:
            return "Not supported"
    
# Test Cell
# Please do not modify
# The following test cell is used to test the implementation of the `GPT4o` class to ensure it works as expected.
if __name__ == '__main__':
    try:
        #load the env file
        import os
        from dotenv import load_dotenv
        load_dotenv('environment.env', override=True)
        
        # Check if openai_assistants.json exists and if so, itterate through the file and delete the assistants
        if os.path.exists('openai_assistants.json'):
            client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
            with open('openai_assistants.json', 'r') as f:
                try:
                    assistants = json.load(f)
                except:
                    assistants = []
            for assistant in assistants:
                try:
                    response = client.beta.assistants.delete(assistants[assistant])
                    if response.deleted == True:
                        print(f"Assistant {assistants[assistant]} deleted.")
                    else:
                        print(f"Assistant {assistants[assistant]} not deleted.")
                    # Delete the openai_assistants.json file
                    os.remove('openai_assistants.json')
                except Exception as e:
                    print(e)

        #gpt4o = OpenaiMulti(os.getenv('OPENAI_API_KEY'),os.getenv('OPENAI_ASSISTANT_ID'),type='assistant')
        gpt4o = OpenaiMulti(os.getenv('OPENAI_API_KEY'),type='assistant')

        response = gpt4o.generate('user','1+1?')
        print(response)
        #response = gpt4o.generate('user','Why?')
        #print(response)
    except Exception as e:
        print(e)