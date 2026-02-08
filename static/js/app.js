// GoHighLevel AI Agent - Frontend JavaScript

let isProcessing = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Test API connection
    testConnection();
    
    // Setup enter key to send
    const input = document.getElementById('commandInput');
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendCommand();
        }
    });
    
    // Auto-resize textarea
    input.addEventListener('input', autoResize);
});

// Auto-resize textarea as user types
function autoResize() {
    const input = document.getElementById('commandInput');
    input.style.height = 'auto';
    input.style.height = input.scrollHeight + 'px';
}

// Test the API connection
async function testConnection() {
    const statusIndicator = document.getElementById('statusIndicator');
    
    try {
        const response = await fetch('/api/test');
        const data = await response.json();
        
        if (data.success) {
            statusIndicator.classList.add('connected');
            statusIndicator.querySelector('.status-text').textContent = 'Connected';
        } else {
            statusIndicator.querySelector('.status-text').textContent = 'Connection Error';
        }
    } catch (error) {
        console.error('Connection test failed:', error);
        statusIndicator.querySelector('.status-text').textContent = 'Offline';
    }
}

// Send command to backend
async function sendCommand() {
    const input = document.getElementById('commandInput');
    const command = input.value.trim();
    
    if (!command || isProcessing) return;
    
    // Add user message to chat
    addMessage(command, 'user');
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';
    
    // Show loading
    const loadingId = addLoadingMessage();
    
    // Disable send button
    isProcessing = true;
    updateSendButton(true);
    
    try {
        const response = await fetch('/api/command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command: command })
        });
        
        const data = await response.json();
        
        // Remove loading message
        removeLoadingMessage(loadingId);
        
        // Add bot response
        addBotResponse(data);
        
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage('❌ Error: Could not connect to server. Please check your connection.', 'bot');
        console.error('Error:', error);
    } finally {
        isProcessing = false;
        updateSendButton(false);
    }
}

// Add a message to the chat
function addMessage(text, sender) {
    const chatContainer = document.getElementById('chatContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = sender === 'bot' ? '🤖' : '👤';
    const senderName = sender === 'bot' ? 'AI Agent' : 'You';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="${sender}-avatar">${avatar}</span>
                <span class="message-sender">${senderName}</span>
            </div>
            <div class="message-text">
                <p>${escapeHtml(text)}</p>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Add bot response with structured data
function addBotResponse(data) {
    const chatContainer = document.getElementById('chatContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    let messageContent = '';
    
    // Add plan/confirmation if available
    if (data.plan) {
        messageContent += `<div class="plan-text">📋 ${escapeHtml(data.plan)}</div>`;
    }
    
    // Add main message
    messageContent += `<p>${escapeHtml(data.message)}</p>`;
    
    // Add structured data if available
    if (data.data && Array.isArray(data.data)) {
        messageContent += '<div class="data-card">';
        data.data.forEach((item, index) => {
            messageContent += `
                <div class="data-item">
                    <div class="data-label">Contact ${index + 1}</div>
                    <div class="data-value"><strong>${escapeHtml(item.name || 'No name')}</strong></div>
                    <div class="data-value">📧 ${escapeHtml(item.email || 'No email')}</div>
                    <div class="data-value">📱 ${escapeHtml(item.phone || 'No phone')}</div>
                    ${item.tags && item.tags.length > 0 ? `
                        <div class="tags">
                            ${item.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        });
        messageContent += '</div>';
    }
    
    const messageClass = data.success ? 'success-message' : 'error-message';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="bot-avatar">🤖</span>
                <span class="message-sender">AI Agent</span>
            </div>
            <div class="message-text ${messageClass}">
                ${messageContent}
            </div>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Add loading indicator
function addLoadingMessage() {
    const chatContainer = document.getElementById('chatContainer');
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message';
    loadingDiv.id = 'loading-' + Date.now();
    
    loadingDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="bot-avatar">🤖</span>
                <span class="message-sender">AI Agent</span>
            </div>
            <div class="message-text">
                <div class="loading">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        </div>
    `;
    
    chatContainer.appendChild(loadingDiv);
    scrollToBottom();
    
    return loadingDiv.id;
}

// Remove loading indicator
function removeLoadingMessage(id) {
    const loading = document.getElementById(id);
    if (loading) {
        loading.remove();
    }
}

// Update send button state
function updateSendButton(disabled) {
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = disabled;
}

// Send a suggestion
function sendSuggestion(button) {
    const input = document.getElementById('commandInput');
    input.value = button.textContent;
    autoResize();
    sendCommand();
}

// Send quick action
function sendQuickAction(action) {
    const input = document.getElementById('commandInput');
    
    const prompts = {
        'add contact': 'Add contact ',
        'search contacts': 'Search for ',
        'add note': 'Add note to ',
        'add tag': 'Tag '
    };
    
    input.value = prompts[action] || action;
    input.focus();
    autoResize();
}

// Scroll chat to bottom
function scrollToBottom() {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Handle mobile keyboard
window.addEventListener('resize', function() {
    scrollToBottom();
});
