# Project Title

Very basic application to layer a frontend to multiple LLMs for simultaneous use.

## Set up environment

```bash
python -m venv venv

.\venv\Scripts\activate

pip install -r requirements.txt

```

## Copy and rename the following:
users_example.json > users.json

llm_config_example.json > llm_config.json

environment_example.env > environment.json

## Configure application
Update users.json to local users for app

Modify llm_config.json to match desired LLMs

Update the environment.json
* APP_IP & APP_PORT supoort specifying an IP for external use (something other than 127.0.0.1)
* SECRET_KEY is a hash that secure your Fluke install (webserver)
* OpenAI and Claude settings are if you will be utilizing those external LLMs
* OLLAMA_API_BASE_URL only needs to be modified if you are not using a local Ollama install

## Run application
```bash
python main.py
```
