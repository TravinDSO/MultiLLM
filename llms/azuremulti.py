import time
import json
from llms.tools.image_gen import Azure_OpenAI_ImageGen
from openai import AzureOpenAI

class AzureMulti():
    def __init__(self, api_key, endpoint='', version='', model='gpt-4o',
                 api_key_2='', endpoint_2='', version_2='', model_2='gpt-4o',
                 info_link='', wait_limit=300, type='chat'):
        try:
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=version,
                azure_endpoint=endpoint
            )
            self.model = model
            self.api_key = api_key
            self.endpoint = endpoint
            self.version = version
            if api_key_2:
                try:
                    self.client_2 = AzureOpenAI(
                        api_key=api_key_2,
                        api_version=version_2,
                        azure_endpoint=endpoint_2
                    )
                    self.model_2 = model_2
                    self.api_key_2 = api_key_2
                    self.endpoint_2 = endpoint_2
                    self.version_2 = version_2
                except Exception as e:
                    print(f'Could not create Azure Client 2: {e}')
                    self.client_2 = self.client
                    self.model_2 = self.model
            else:
                self.client_2 = self.client
                self.model_2 = self.model
                self.api_key_2 = self.api_key
                self.endpoint_2 = self.endpoint
                self.version_2 = self.version
        except Exception as e:
            print(f'Could not create Azure Client: {e}')

        self.image_gen_tool = Azure_OpenAI_ImageGen(self.api_key, self.version, self.endpoint)

        self.openai_assistant_id = {}
        self.openai_assistant_thread = {}
        self.info_link = info_link
        self.wait_limit = int(wait_limit)
        self.assistant_name = "MultiLLM (Agentic AI)"
        self.agent_instructions = None
        self.number_of_responses = 0
        self.conversation_history = {}
        self.extra_messages = {}
        self.type = type
        self.use_assistants = True if type == 'assistant' else False
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "generate_image",
                    "description": "Generate an image if needed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Generate an image based on the prompt. Format the response in HTML to display the image."
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            }
        ]

    def generate(self, user, prompt):
        if self.type == 'assistant':
            return self.assistant_generate(user, prompt)
        elif self.type == 'chat':
            return self.direct_generate(user, prompt)
        elif self.type == 'image':
            return self.image_generate(user, prompt, model=self.model)
        else:
            return "Not supported"

    def handle_tool(self, user, tool):
        tool_name = tool.function.name
        args = json.loads(tool.function.arguments)
        if tool_name == "generate_image":
            self.extra_messages[user].append(f'<HR><i>Generating image using this prompt: {args["prompt"]}</i>')
            response = self.image_gen_tool.image_generate(prompt=args['prompt'])
            return response
        else:
            return "Tool not supported"

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
            print(f'Could not process direct prompt to Azure: {e}')
            return f'Could not process direct prompt to Azure: {e}'

    def assistant_generate(self, user, prompt):
        # Check if the user has an Azure OpenAI ASSISTANT and create one if not
        if user not in self.openai_assistant_id:
            try:
                self.openai_assistant_id[user] = self.client.beta.assistants.create(name=self.assistant_name,model=self.model,tools=self.tools,instructions=self.agent_instructions)
                try:
                    # Append the new assistant id
                    with open('azure_openai_assistants.txt', 'a') as f:
                        f.write(f"{self.openai_assistant_id[user].id}\n")
                except Exception as e:
                    print(f'Could not write Azure Assistant ID to file: {e}')
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
            result = self.client.beta.threads.runs.retrieve(thread_id=self.openai_assistant_thread[user].id, run_id=run.id)
            # Check if the function returned a result and if the run is no longer queued
            if result.status == "completed":
                break
            elif result.status == "requires_action":
                tool_outputs = []
                for each_tool_call in result.required_action.submit_tool_outputs.tool_calls:
                    try:
                        response = self.handle_tool(user, each_tool_call)
                        tool_outputs.append(
                            {
                                "tool_call_id": each_tool_call.id,
                                "output": response
                            }
                        )
                    except:
                        tool_outputs.append(
                            {
                                "tool_call_id": each_tool_call.id,
                                "output": "Error processing tool"
                            }
                        )
                # Tool output has been submitted, so we can continue
                try:
                    tool_run = self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.openai_assistant_thread[user].id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                except Exception as e:
                    print(f'Error submitting tool output: {e}')
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
    
    def get_extra_messages(self, user):
        if user not in self.extra_messages:
            self.extra_messages[user] = []  # Initialize the list if the key doesn't exist
        messages = self.extra_messages[user]
        self.extra_messages[user] = []  # Clear messages after fetching
        return messages

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
        if self.type in ['assistant', 'chat']:
            prompt = 'Summarize the current conversation. If code was generated, preserve it, presenting the most complete version to the user.'
            return self.generate(user, prompt)
        else:
            return "Not supported"

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
# The following test cell is used to test the implementation of the `AzureMulti` class to ensure it works as expected.
if __name__ == '__main__':
    try:
        response = ''
        # load the env file
        import os
        from dotenv import load_dotenv

        load_dotenv('../environment.env', override=True)

        azure_gpt4o = AzureMulti(
            os.getenv('OPENAI_API_KEY'),
            'gpt-4o',
            os.getenv('AZURE_OPENAI_API_ENDPOINT'),
            os.getenv('AZURE_OPENAI_API_VERSION'),
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
