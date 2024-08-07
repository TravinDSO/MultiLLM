const ongoingRequests = {};

// Function to cancel a request
function cancelRequest(llm) {
    if (ongoingRequests[llm]) {
        ongoingRequests[llm].abort();
        delete ongoingRequests[llm];
        clearInterval(timerInterval);

        // Hide spinner and reset timer
        document.getElementById(`${llm}-spinner`).style.visibility = 'hidden';
        document.getElementById(`${llm}-spinner-toggle`).style.visibility = 'hidden';
        document.getElementById(`${llm}-timer`).style.display = 'none';
    } else {
        console.log('No ongoing request to cancel');
    }
}

// Function to check login status and update UI accordingly
function checkLoginStatus() {
    fetch('/is_logged_in')
        .then(response => response.json())
        .then(data => {
            if (data.logged_in) {
                document.getElementById('login-form').classList.add('hidden');
                document.getElementById('header').classList.remove('hidden');
                document.getElementById('app-content').classList.remove('hidden');
                document.getElementById('main-content').style.display = 'flex';
                adjustLayout(); // Call adjustLayout here to ensure proper rendering
            } else {
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('header').classList.add('hidden');
                document.getElementById('app-content').classList.add('hidden');
            }
        })
        .catch(error => {
            console.error('Error checking login status:', error);
        });
}

// Login function
function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Force a page reload to ensure all content is properly displayed
            window.location.reload();
        } else {
            document.getElementById('login-error').textContent = 'Invalid username or password';
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        document.getElementById('login-error').textContent = 'An error occurred';
    });
}

// Logout function
function logout() {
    fetch('/logout')
        .then(response => {
            if (response.ok) {
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('header').classList.add('hidden');
                document.getElementById('app-content').classList.add('hidden');
                document.getElementById('main-content').style.display = 'flex';
                // Clear any user data or reset form fields if necessary
            } else {
                console.error('Logout failed');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Function to adjust layout based on visible LLM blocks
function adjustLayout() {
    const llmBlocks = document.querySelectorAll('.llm-block:not(.hidden)');
    const container = document.querySelector('.container');

    if (llmBlocks.length === 1) {
        llmBlocks[0].style.flex = '1 1 100%';
    } else if (llmBlocks.length === 2) {
        llmBlocks.forEach(block => block.style.flex = '1 1 30%');
    } else {
        llmBlocks.forEach(block => block.style.flex = '1 1 30%');
    }
}

// Function to fill each LLM outputDiv with historical messages after page load
function summarizeThread(llm) {
    const outputDiv = document.getElementById(`${llm}-output`);
    const spinner = document.getElementById(`${llm}-spinner`);
    const toggleSpinner = document.getElementById(`${llm}-spinner-toggle`);
    const timer = document.getElementById(`${llm}-timer`);
    
    let startTime = new Date();
    let timerInterval;

    spinner.style.visibility = 'visible';
    toggleSpinner.style.visibility = 'visible';
    timer.style.display = 'inline-block';
    timerInterval = setInterval(() => {
        let elapsedTime = new Date() - startTime;
        let seconds = (elapsedTime / 1000).toFixed(3);
        timer.textContent = `${seconds}s`;
    }, 10);

    fetch('/summarize_thread', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ llm: llm }),
    })
    .then(thread => thread.json())
    .then(data => {
        // Process the thread and separate code blocks from plain text
        const parts = data.thread.split(/(```[\s\S]*?```)/g); // Split by code blocks
        let formattedThread = '';

        parts.forEach(part => {
            if (part.startsWith('```') && part.endsWith('```')) {
                const codeBlock = part.slice(3, -3).replace(/\n/g, '<br>');
                formattedThread += `<pre><code>${codeBlock}</code></pre>`;
            } else {
                formattedThread += part.replace(/\n/g, '<br>');
            }
        });

        const llmResponse = `<strong>${llm}:</strong><br>${formattedThread}<br>`;
        outputDiv.innerHTML = `${llmResponse}`;

        spinner.style.visibility = 'hidden';
        toggleSpinner.style.visibility = 'hidden';
        timer.style.display = 'none';

    })
    .catch((error) => {
        console.error('Error:', error);
        spinner.style.visibility = 'hidden';
        toggleSpinner.style.visibility = 'hidden';
        timer.style.display = 'none';
        clearInterval(timerInterval);
    });
}

// Function to generate response from LLM
function generateResponse(llm) {
    const input = document.getElementById(`${llm}-input`).value;
    const outputDiv = document.getElementById(`${llm}-output`);
    const spinner = document.getElementById(`${llm}-spinner`);
    const toggleSpinner = document.getElementById(`${llm}-spinner-toggle`);
    const timer = document.getElementById(`${llm}-timer`);
    
    let startTime = new Date();
    let timerInterval;

    spinner.style.visibility = 'visible';
    toggleSpinner.style.visibility = 'visible';
    timer.style.display = 'inline-block';
    timerInterval = setInterval(() => {
        let elapsedTime = new Date() - startTime;
        let seconds = (elapsedTime / 1000).toFixed(3);
        timer.textContent = `${seconds}s`;
    }, 10);

    const controller = new AbortController();
    const signal = controller.signal;
    ongoingRequests[llm] = controller;

    fetch('/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ llm: llm, prompt: input }),
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(timerInterval);
        delete ongoingRequests[llm];
        let elapsedTime = (new Date() - startTime) / 1000;
        
        // Process the response and separate code blocks from plain text
        const parts = data.response.split(/(```[\s\S]*?```)/g); // Split by code blocks
        let formattedResponse = '';

        parts.forEach(part => {
            if (part.startsWith('```') && part.endsWith('```')) {
                const codeBlock = part.slice(3, -3).replace(/\n/g, '<br>');
                formattedResponse += `<pre><code>${codeBlock}</code></pre>`;
            } else {
                formattedResponse += part.replace(/\n/g, '<br>');
            }
        });

        const userPrompt = `<strong>User:</strong> ${input.replace(/\n/g, '<br>')}<br><br>`;
        const llmResponse = `<strong>${llm} (${elapsedTime.toFixed(3)}s):</strong><br>${formattedResponse}<br>`;

        outputDiv.innerHTML = `<hr>${llmResponse}<hr><i>${userPrompt}</i>` + outputDiv.innerHTML;

        clearInterval(timerInterval);
        spinner.style.visibility = 'hidden';
        toggleSpinner.style.visibility = 'hidden';
        timer.style.display = 'none';
    })
    .catch((error) => {
        if (error.name === 'AbortError') {
            console.log('Fetch aborted');
        } else {
            console.error('Error:', error);
        }
        const errorResponse = 'An error occurred';
        outputDiv.innerHTML = `<hr><div>${errorResponse}</div>` + outputDiv.innerHTML;

        spinner.style.visibility = 'hidden';
        toggleSpinner.style.visibility = 'hidden';
        timer.style.display = 'none';
        clearInterval(timerInterval);
        delete ongoingRequests[llm];
    });
}


// Function to confirm starting a new thread
function confirmNewThread(llm) {
    if (confirm('Are you sure you want to start a new thread? This will clear all previous messages.')) {
        clearThread(llm);
    }
}

// Function to confirm summarizing LLM historical messages
function confirmSummarize(llm) {
    if (confirm('Are you sure you want to summarize historical responses? This will clear all previous messages.')) {
        summarizeThread(llm);
    }
}

// Function to clear thread
function clearThread(llm) {
    document.getElementById(`${llm}-input`).value = '';
    document.getElementById(`${llm}-output`).innerHTML = '';

    fetch('/clear_thread', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ llm: llm }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('Thread cleared:', data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// Function to check if the user has a conversation with the LLM
function checkConversation(llm) {
    fetch('/check_conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ llm: llm }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.has_conversation) {
            if (confirm('You already have a conversation with this LLM. Would you like to summarize it?')) {
                summarizeThread(llm);
            }
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// Function to toggle LLM visibility
function toggleLLM(llm) {
    // If the LLM block is being toggled on, check if the user has a conversation
    if (document.getElementById(llm + '-block').classList.contains('hidden')) {
        checkConversation(llm);
    }
    var llmBlock = document.getElementById(llm + '-block');
    llmBlock.classList.toggle('hidden');
    adjustLayout();
}

// Function to poll for extra messages
function pollExtraMessages(llm) {
    const outputDiv = document.getElementById(`${llm}-output`);

    fetch(`/extra_messages?llm=${llm}`)
        .then(response => response.json())
        .then(data => {
            if (data.messages) {
                data.messages.forEach(message => {
                    const messageDiv = document.createElement('div');
                    messageDiv.innerHTML = message;
                    outputDiv.prepend(messageDiv);  // Prepend to show the latest message on top
                });
            }
        })
        .catch(error => {
            console.error('Error fetching extra messages:', error);
        });

    // Continue polling
    setTimeout(() => pollExtraMessages(llm), 2000);
}

window.addEventListener('resize', adjustLayout);
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    // Add polling for each LLM
    const llms = document.querySelectorAll('.llm-block');
    llms.forEach(llm => {
        const llmId = llm.id.split('-')[0];
        pollExtraMessages(llmId);
    });
});