import logging
import datetime
import os

class Logger:
    def __init__(self):
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
        # Set up logging configuration
        logging.basicConfig(
            filename=os.path.join('logs', 'app.log'),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def log_request(self, user, llm_name, prompt):
        """Log an incoming request."""
        self.logger.info(f"Request - User: {user}, LLM: {llm_name}, Prompt: {prompt}")

    def log_response(self, user, llm_name, response):
        """Log a response from an LLM."""
        self.logger.info(f"Response - User: {user}, LLM: {llm_name}, Response: {response[:200]}...")

    def log_error(self, user, llm_name, error_message):
        """Log an error."""
        self.logger.error(f"Error - User: {user}, LLM: {llm_name}, Error: {error_message}")

    def log(self, ip_address, user, llm_name, prompt, response):
        """Legacy log method for backward compatibility."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"{timestamp} - {ip_address} - {user} - {llm_name} - {prompt} - {response}")