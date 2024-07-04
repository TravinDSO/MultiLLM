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
        llmBlocks.forEach(block => block.style.flex = '1 1 48%');
    } else {
        llmBlocks.forEach(block => block.style.flex = '1 1 30%');
    }
}

// Function to fill each LLM outputDiv with historical messages after page load
function fillHistoricalMessages(llm) {
    const outputDiv = document.getElementById(`${llm}-output`);

    fetch('/get_thread', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ llm: llm }),
    })
    .then(response => response.json())
    .then(data => {
        // // Separate user prompts and LLM responses
        // const messages = data.response.JSON;
        // let userMessages = [];
        // let assistantMessages = [];

        // messages.forEach(message => {
        //     if (message.role === 'user') {
        //         userMessages.push(message.content);
        //     } else if (message.role === 'assistant') {
        //         assistantMessages.push(message.content);
        //     }
        // });

        assistantMessages = data.response;

        const llmResponse = `<strong>${llm}:</strong><br>${assistantMessages}<br>`;
        outputDiv.innerHTML = `<hr>${llmResponse}`;
    })
    .catch((error) => {
        console.error('Error:', error);
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

        outputDiv.innerHTML = `<hr>${userPrompt}${llmResponse}` + outputDiv.innerHTML;

        spinner.style.visibility = 'hidden';
        toggleSpinner.style.visibility = 'hidden';
        timer.style.display = 'none';
    })
    .catch((error) => {
        console.error('Error:', error);
        const errorResponse = 'An error occurred';
        outputDiv.innerHTML = `<hr><div>${errorResponse}</div>` + outputDiv.innerHTML;

        spinner.style.visibility = 'hidden';
        toggleSpinner.style.visibility = 'hidden';
        timer.style.display = 'none';
        clearInterval(timerInterval);
    });
}


// Function to confirm starting a new thread
function confirmNewThread(llm) {
    if (confirm('Are you sure you want to start a new thread? This will clear all previous messages.')) {
        clearThread(llm);
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

// Function to toggle LLM visibility
function toggleLLM(llm) {
    // Check if the block is being unhidden and fill historical messages if necessary
    if (document.getElementById(llm + '-block').classList.contains('hidden')) {
        //fillHistoricalMessages(llm);
    }

    var llmBlock = document.getElementById(llm + '-block');
    llmBlock.classList.toggle('hidden');
    adjustLayout();
}

// Event listeners
window.addEventListener('resize', adjustLayout);
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
});