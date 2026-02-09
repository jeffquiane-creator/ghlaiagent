// GoHighLevel AI Agent - Enhanced JavaScript with Premium Interactions

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
    
    // Add focus glow effect
    input.addEventListener('focus', function() {
        document.querySelector('.input-wrapper').style.transform = 'scale(1.01)';
    });
    
    input.addEventListener('blur', function() {
        document.querySelector('.input-wrapper').style.transform = 'scale(1)';
    });
    
    // Add typing indicator
    let typingTimeout;
    input.addEventListener('input', function() {
        clearTimeout(typingTimeout);
        // Could add "AI is thinking..." indicator here
    });
});

// Auto-resize textarea as user types
function autoResize() {
    const input = document.getElementById('commandInput');
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
}

// Test the API connection with enhanced feedback
async function testConnection() {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = statusIndicator.querySelector('.status-text');
    
    // Add connecting animation
    statusText.textContent = 'Connecting...';
    
    try {
        const response = await fetch('/api/test');
        const data = await response.json();
        
        if (data.success) {
            statusIndicator.classList.add('connected');
            statusText.textContent = 'Connected';
            
            // Success animation
            statusIndicator.style.animation = 'successPulse 0.5s ease-out';
            setTimeout(() => {
                statusIndicator.style.animation = '';
            }, 500);
        } else {
            statusText.textContent = 'Connection Error';
            showNotification('Connection Error', 'error');
        }
    } catch (error) {
        console.error('Connection test failed:', error);
        statusText.textContent = 'Offline';
        showNotification('Failed to connect to server', 'error');
    }
}

// Enhanced send command with better UX
async function sendCommand() {
    const input = document.getElementById('commandInput');
    const command = input.value.trim();
    
    if (!command || isProcessing) return;
    
    // Add send button animation
    const sendBtn = document.getElementById('sendButton');
    sendBtn.style.transform = 'scale(0.9) rotate(360deg)';
    setTimeout(() => {
        sendBtn.style.transform = '';
    }, 300);
    
    // Add user message to chat with animation
    addMessage(command, 'user');
    
    // Clear input with animation
    input.style.opacity = '0.5';
    setTimeout(() => {
        input.value = '';
        input.style.height = 'auto';
        input.style.opacity = '1';
    }, 150);
    
    // Show enhanced loading
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
        
        // Add bot response with enhanced display
        addBotResponse(data);
        
        // Success sound effect (subtle)
        if (data.success) {
            playSuccessSound();
        }
        
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage('❌ Error: Could not connect to server. Please check your connection.', 'bot');
        showNotification('Connection error', 'error');
        console.error('Error:', error);
    } finally {
        isProcessing = false;
        updateSendButton(false);
    }
}

// Add a message to the chat with enhanced animation
function addMessage(text, sender) {
    const chatContainer = document.getElementById('chatContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
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
    
    // Trigger animation
    setTimeout(() => {
        messageDiv.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 10);
    
    scrollToBottom();
}

// Enhanced bot response with better data display
function addBotResponse(data) {
    const chatContainer = document.getElementById('chatContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
    let messageContent = '';
    
    // Add plan/confirmation if available with icon
    if (data.plan) {
        const planIcon = data.success ? '📋' : '⚠️';
        messageContent += `<div class="plan-text ${data.success ? 'success-message' : 'error-message'}">${planIcon} ${escapeHtml(data.plan)}</div>`;
    }
    
    // Add main message with appropriate icon
    const messageIcon = data.success ? '✅' : '❌';
    messageContent += `<p><strong>${messageIcon}</strong> ${escapeHtml(data.message)}</p>`;
    
    // Add structured data with enhanced display
    if (data.data && Array.isArray(data.data)) {
        messageContent += '<div class="data-card">';
        data.data.forEach((item, index) => {
            messageContent += `
                <div class="data-item" style="animation: slideIn 0.3s ease-out ${index * 0.1}s both">
                    ${renderDataItem(item, index)}
                </div>
            `;
        });
        messageContent += '</div>';
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="bot-avatar">🤖</span>
                <span class="message-sender">AI Agent</span>
            </div>
            <div class="message-text">
                ${messageContent}
            </div>
        </div>
    `;
    
    chatContainer.appendChild(messageDiv);
    
    // Trigger animation
    setTimeout(() => {
        messageDiv.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 10);
    
    scrollToBottom();
}

// Render data item with appropriate formatting
function renderDataItem(item, index) {
    // Check if it's contact data
    if (item.name || item.email || item.phone) {
        return `
            <div class="data-label">Contact ${index + 1}</div>
            <div class="data-value"><strong>${escapeHtml(item.name || 'No name')}</strong></div>
            <div class="data-value">📧 ${escapeHtml(item.email || 'No email')}</div>
            <div class="data-value">📱 ${escapeHtml(item.phone || 'No phone')}</div>
            ${item.deal_value ? `<div class="data-value">💰 ${escapeHtml(item.deal_value)}</div>` : ''}
            ${item.tags && item.tags.length > 0 ? `
                <div class="tags">
                    ${item.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            ` : ''}
        `;
    }
    
    // Check if it's analytics/stats data
    if (item.total_deals || item.total_contacts || item.total_value) {
        return `
            ${item.total_value ? `<div class="data-value"><strong>Total Value:</strong> ${escapeHtml(item.total_value)}</div>` : ''}
            ${item.total_deals ? `<div class="data-value"><strong>Total Deals:</strong> ${item.total_deals}</div>` : ''}
            ${item.open_deals ? `<div class="data-value"><strong>Open:</strong> ${item.open_deals}</div>` : ''}
            ${item.won_deals ? `<div class="data-value"><strong>Won:</strong> ${item.won_deals}</div>` : ''}
            ${item.total_contacts ? `<div class="data-value"><strong>Total Contacts:</strong> ${item.total_contacts}</div>` : ''}
            ${item.with_email ? `<div class="data-value"><strong>With Email:</strong> ${item.with_email}</div>` : ''}
            ${item.completion_rate ? `<div class="data-value"><strong>Completion:</strong> ${item.completion_rate}</div>` : ''}
        `;
    }
    
    // Check if it's pipeline data
    if (item.pipeline || item.stages) {
        return `
            <div class="data-label">${escapeHtml(item.pipeline || item.name || 'Pipeline')}</div>
            ${item.total_stages ? `<div class="data-value"><strong>Total Stages:</strong> ${item.total_stages}</div>` : ''}
            <div class="data-value" style="font-size: 0.8125rem; line-height: 1.8; margin-top: 0.5rem;">
                <strong>Flow:</strong><br>
                ${escapeHtml(item.stages || 'No stages')}
            </div>
        `;
    }
    
    // Generic object display
    return Object.entries(item).map(([key, value]) => 
        `<div class="data-value"><strong>${escapeHtml(key)}:</strong> ${escapeHtml(String(value))}</div>`
    ).join('');
}

// Enhanced loading indicator
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
        loading.style.opacity = '0';
        loading.style.transform = 'translateY(-10px)';
        setTimeout(() => loading.remove(), 300);
    }
}

// Update send button state
function updateSendButton(disabled) {
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = disabled;
    if (disabled) {
        sendButton.style.opacity = '0.5';
    } else {
        sendButton.style.opacity = '1';
    }
}

// Send a suggestion with animation
function sendSuggestion(button) {
    const input = document.getElementById('commandInput');
    
    // Button press animation
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
        button.style.transform = '';
    }, 150);
    
    input.value = button.textContent;
    autoResize();
    
    // Small delay before sending for better UX
    setTimeout(() => {
        sendCommand();
    }, 200);
}

// Quick action shortcuts with enhanced feedback
function quickAction(type) {
    const input = document.getElementById('commandInput');
    const prompts = {
        'contact': 'Create contact ',
        'deal': 'Create opportunity for ',
        'sms': 'Send SMS to ',
        'search': 'Search for ',
        'analytics': 'Show pipeline report'
    };
    
    if (type === 'analytics') {
        input.value = prompts[type];
        sendCommand();
    } else {
        input.value = prompts[type] || '';
        input.focus();
        autoResize();
        
        // Add subtle shake animation to indicate action
        input.style.animation = 'shake 0.3s';
        setTimeout(() => {
            input.style.animation = '';
        }, 300);
    }
}

// Toggle sidebar with animation
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
    
    // Add overlay for mobile
    if (window.innerWidth <= 768) {
        let overlay = document.querySelector('.sidebar-overlay');
        if (sidebar.classList.contains('active')) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                overlay.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.5);
                    backdrop-filter: blur(4px);
                    z-index: 999;
                    animation: fadeIn 0.3s;
                `;
                overlay.onclick = toggleSidebar;
                document.body.appendChild(overlay);
            }
        } else if (overlay) {
            overlay.style.animation = 'fadeOut 0.3s';
            setTimeout(() => overlay.remove(), 300);
        }
    }
}

// Use example command with enhanced interaction
function useExample(element) {
    const command = element.textContent.trim();
    const input = document.getElementById('commandInput');
    
    // Add ripple effect
    const ripple = document.createElement('span');
    ripple.style.cssText = `
        position: absolute;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        background: radial-gradient(circle, rgba(99,102,241,0.4) 0%, transparent 70%);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    `;
    element.style.position = 'relative';
    element.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
    
    input.value = command;
    input.focus();
    autoResize();
    
    // Auto-send on mobile
    if (window.innerWidth <= 768) {
        toggleSidebar();
        setTimeout(() => sendCommand(), 300);
    }
}

// Smooth scroll to bottom
function scrollToBottom() {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show notification (optional enhancement)
function showNotification(message, type = 'info') {
    // Could implement toast notifications here
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Play success sound (subtle, optional)
function playSuccessSound() {
    // Could add a subtle success sound effect
    // For now, just a visual indication
    const statusIndicator = document.getElementById('statusIndicator');
    const originalBg = statusIndicator.style.background;
    statusIndicator.style.background = 'rgba(16, 185, 129, 0.2)';
    setTimeout(() => {
        statusIndicator.style.background = originalBg;
    }, 300);
}

// Handle mobile keyboard
window.addEventListener('resize', function() {
    scrollToBottom();
});

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    const menuToggle = document.querySelector('.menu-toggle');
    
    if (window.innerWidth <= 768 && 
        sidebar.classList.contains('active') &&
        !sidebar.contains(e.target) &&
        !menuToggle.contains(e.target)) {
        toggleSidebar();
    }
});

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Cmd/Ctrl + K to focus input
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('commandInput').focus();
    }
    
    // Escape to close sidebar on mobile
    if (e.key === 'Escape') {
        const sidebar = document.getElementById('sidebar');
        if (sidebar.classList.contains('active')) {
            toggleSidebar();
        }
    }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    @keyframes ripple {
        0% {
            transform: scale(0);
            opacity: 1;
        }
        100% {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    
    @keyframes successPulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
`;
document.head.appendChild(style);
