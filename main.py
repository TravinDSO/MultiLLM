import os
import logging
from dotenv import load_dotenv
from quart import Quart, render_template, request, jsonify, session, redirect, url_for
from llm_manager import LLMManager
from logger import Logger
import json
import asyncio
from functools import partial
from hypercorn.config import Config
from hypercorn.asyncio import serve

#load the env file
load_dotenv('environment.env', override=True)

app = Quart(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.debug = False
llm_manager = LLMManager()
llm_logger = Logger()

# Set the log level to WARNING to suppress HTTP request logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

def load_users():
    with open('users.json') as f:
        return json.load(f)['users']

def clear_outlook_pickles():
    # Search app root for any pickle files matching *_365_token.pickle and delete them
    for root, dirs, files in os.walk(os.getcwd()):
        for file in files:
            if file.endswith("_365_token.pickle"):
                os.remove(os.path.join(root, file))

def get_user_by_username(username):
    users = load_users()
    return next((user for user in users if user['username'] == username), None)

@app.route('/')
async def index():
    if 'username' in session:
        llms = llm_manager.get_available_llms()
        # Limit LLMs to only those that the user is authorized to use
        user = get_user_by_username(session['username'])
        if user:
            llms = [llm for llm in llms if llm in user['authorized_llms']]

        llm_links = llm_manager.get_llm_links()
        #capitalize the first letter of the username
        username = session['username'].capitalize()
        return await render_template('index.html', llms=llms, llm_links=llm_links, username=username)
    return await render_template('index.html', llms=[], llm_links={})

@app.route('/get_authorized_llms', methods=['POST'])
async def get_authorized_llms():
    data = await request.get_json()
    username = session['username']
    user = get_user_by_username(username)
    
    if user:
        return jsonify({"authorized_llms": user['authorized_llms']})
    else:
        return jsonify({"authorized_llms": []}), 403

@app.route('/login', methods=['POST'])
async def login():
    data = await request.get_json()
    #ensure usernames are lowercase
    username = data['username'].lower()
    password = data['password']
    users = load_users()
    
    for user in users:
        if user['username'] == username and user['password'] == password:
            session['username'] = username
            return jsonify(success=True)
    return jsonify(success=False)

@app.route('/is_logged_in')
async def is_logged_in():
    if 'username' in session:
        return jsonify(logged_in=True)
    return jsonify(logged_in=False)

@app.route('/logout')
async def logout():
    session.pop('username', None)
    return '', 204  # No content response

@app.route('/generate', methods=['POST'])
async def generate():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'})

    data = await request.get_json()
    llm_name = data.get('llm')
    prompt = data.get('prompt')
    user = session['username']

    # Log the request
    llm_logger.log_request(user, llm_name, prompt)

    try:
        # Get response from LLM (handles both sync and async)
        response = await llm_manager.get_llm_response(llm_name, user, prompt)
        
        # Get any extra messages
        llm = llm_manager.get_llm(llm_name)
        extra_messages = llm.get_extra_messages(user) if hasattr(llm, 'get_extra_messages') else []

        # Log the response
        llm_logger.log_response(user, llm_name, response)

        return jsonify({
            'response': response,
            'extra_messages': extra_messages
        })

    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        llm_logger.log_error(user, llm_name, error_message)
        return jsonify({'error': error_message})

@app.route('/extra_messages', methods=['GET'])
async def get_extra_messages():
    llm_name = request.args.get('llm')
    llm = llm_manager.get_llm(llm_name)
    user = session['username']
    if llm:
        messages = llm.get_extra_messages(user)
        return jsonify({'messages': messages})
    else:
        return jsonify({'error': 'LLM not found'}), 404

@app.route('/summarize_thread', methods=['POST'])
async def summarize_thread():
    data = await request.get_json()
    llm_name = data['llm']
    user = session['username']
    try:
        llm = llm_manager.get_llm(llm_name)
        thread = await llm.summarize_conversation(user)
        return jsonify({'thread': thread}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Error getting thread'}), 500

@app.route('/check_conversation', methods=['POST'])
async def check_conversation():
    data = await request.get_json()
    llm_name = data['llm']
    user = session['username']
    try:
        llm = llm_manager.get_llm(llm_name)
        has_conversation = llm.check_for_previous_conversation(user)
        return jsonify({'has_conversation': has_conversation}), 200
    except:
        return jsonify({'status': 'error', 'message': 'Error checking conversation'}), 500

@app.route('/clear_thread', methods=['POST'])
async def clear_thread():
    data = await request.get_json()
    llm_name = data['llm']
    user = session['username']
    try:
        llm = llm_manager.get_llm(llm_name)
        await llm.clear_conversation(user)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Error clearing thread'}), 500

if __name__ == '__main__':
    APP_IP = os.getenv('APP_IP', '127.0.0.1')
    
    # More robust port handling
    try:
        APP_PORT = int(os.getenv('APP_PORT', '5000').strip())
    except (ValueError, TypeError):
        print("Invalid APP_PORT in environment variables, using default port 5000")
        APP_PORT = 5000

    # Clear out any Outlook pickles that may be present
    clear_outlook_pickles()

    # Configure Hypercorn
    config = Config()
    config.bind = [f"{APP_IP}:{APP_PORT}"]
    
    print(f"Running on http://{config.bind[0]}")
    
    # Run the async server
    asyncio.run(serve(app, config))