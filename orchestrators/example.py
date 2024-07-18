# This is an example of an orchestrator that uses the OpenaiMulti class to orchestrate a number of LLMs as agents

from llms.openaimulti import OpenaiMulti

# Inherit from the OpenaiMulti class
class exampleOrchestrator(OpenaiMulti):
    def __init__(self, api_key,model='gpt-4o',info_link='',wait_limit=300, type='chat'):
        # Call the parent class constructor
        super().__init__(api_key,model,info_link,wait_limit,type)