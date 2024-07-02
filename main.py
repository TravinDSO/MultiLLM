from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from llm_manager import LLMManager
from logger import Logger
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a real secret key
llm_manager = LLMManager()
llm_logger = Logger()

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
            llm_logger.log(ip_address, llm_name, prompt, response)
            return jsonify({'response': response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'LLM not found'}), 404

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
    # Start the Flask app on IP 192.168.1.42 port 7860
    app.run(host='192.168.1.42', port=7860)
