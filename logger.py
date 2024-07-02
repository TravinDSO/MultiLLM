import logging
import os

class Logger:
    def __init__(self, log_file='llm.log'):
        #set path to .\logs
        self.log_file = os.path.join('logs', log_file)

        self.logger = logging.getLogger('Logger')
        self.logger.setLevel(logging.INFO)
        
        # Create handlers
        file_handler = logging.FileHandler(self.log_file)
        console_handler = logging.StreamHandler()
        
        # Create formatters and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, ip_address, llm, prompt, response):
        #strip all newlines
        prompt = prompt.replace('\n', ' ')
        response = response.replace('\n', ' ')

        self.logger.info(f'IP Address ({ip_address}) | LLM ({llm}) | Prompt({prompt}) | Response: ({response})')