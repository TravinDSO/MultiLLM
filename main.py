import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from llm_manager import LLMManager
from logger import Logger
import json

#load the env file
load_dotenv('environment.env', override=True)

app = Flask(__name__)
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

@app.route('/')
def index():
    if 'username' in session:
        llms = llm_manager.get_available_llms()
        llm_links = llm_manager.get_llm_links()
        #capitalize the first letter of the username
        username = session['username'].capitalize()
        return render_template('index.html', llms=llms, llm_links=llm_links, username=username)
    return render_template('index.html', llms=[], llm_links={})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
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
def is_logged_in():
    if 'username' in session:
        return jsonify(logged_in=True)
    return jsonify(logged_in=False)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return '', 204  # No content response

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    llm_name = data['llm']
    prompt = data['prompt']

    # Grab IP address
    ip_address = request.remote_addr
    
    llm = llm_manager.get_llm(llm_name)
    user = session['username']
    if llm:
        try:
            response = llm.generate(user,prompt)
            llm_logger.log(ip_address, user, llm_name, prompt, response)
            return jsonify({'response': response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'LLM not found'}), 404

@app.route('/extra_messages', methods=['GET'])
def get_extra_messages():
    llm_name = request.args.get('llm')
    llm = llm_manager.get_llm(llm_name)
    user = session['username']
    if llm:
        messages = llm.get_extra_messages(user)
        return jsonify({'messages': messages})
    else:
        return jsonify({'error': 'LLM not found'}), 404

@app.route('/summarize_thread', methods=['POST'])
def summarize_thread():
    data = request.get_json()
    llm_name = data['llm']
    user = session['username']
    try:
        llm = llm_manager.get_llm(llm_name)
        thread = llm.summarize_conversation(user)
        return jsonify({'thread': thread}), 200
    except:
        return jsonify({'status': 'error', 'message': 'Error getting thread'}), 500

@app.route('/check_conversation', methods=['POST'])
def check_conversation():
    data = request.get_json()
    llm_name = data['llm']
    user = session['username']
    try:
        llm = llm_manager.get_llm(llm_name)
        has_conversation = llm.check_for_previous_conversation(user)
        return jsonify({'has_conversation': has_conversation}), 200
    except:
        return jsonify({'status': 'error', 'message': 'Error checking conversation'}), 500

@app.route('/clear_thread', methods=['POST'])
def clear_thread():
    data = request.get_json()
    llm_name = data['llm']
    user = session['username']
    try:
        llm = llm_manager.get_llm(llm_name)
        llm.clear_conversation(user)
        return jsonify({'status': 'success'}), 200
    except:
        return jsonify({'status': 'error', 'message': 'Error clearing thread'}), 500

if __name__ == '__main__':
    
    APP_IP = os.getenv('APP_IP')
    APP_PORT = os.getenv('APP_PORT')

    if APP_IP and APP_PORT:
        print(f"Running on http://{APP_IP}:{APP_PORT}")
        app.run(host=APP_IP, port=APP_PORT)
    else:
        print("Running on http://localhost:5000")
        app.run()