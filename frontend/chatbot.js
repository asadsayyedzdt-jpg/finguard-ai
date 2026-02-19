// ============================================
// CHATBOT FUNCTIONALITY
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    setupChatbot();
});

function setupChatbot() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-message');
    const quickButtons = document.querySelectorAll('.quick-btn');
    
    // Handle form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        chatInput.value = '';
        
        // Send to backend
        await sendChatMessage(message);
    });
    
    // Handle quick action buttons
    quickButtons.forEach(btn => {
        btn.addEventListener('click', async function() {
            const question = this.getAttribute('data-question');
            addMessage(question, 'user');
            await sendChatMessage(question);
        });
    });
}

async function sendChatMessage(message) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Add bot response
            setTimeout(() => {
                addMessage(data.data.response, 'bot');
            }, 500);
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
        
    } catch (error) {
        console.error('Chat error:', error);
        addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'bot');
    }
}

function addMessage(text, sender) {
    const messagesContainer = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'bot' ? 
        '<i class="fas fa-robot"></i>' : 
        '<i class="fas fa-user"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    // Parse text for lists
    if (text.includes('•') || text.includes('\n')) {
        const parts = text.split('\n');
        let html = '';
        let inList = false;
        
        parts.forEach(part => {
            if (part.trim().startsWith('•')) {
                if (!inList) {
                    html += '<ul>';
                    inList = true;
                }
                html += `<li>${part.replace('•', '').trim()}</li>`;
            } else {
                if (inList) {
                    html += '</ul>';
                    inList = false;
                }
                if (part.trim()) {
                    html += `<p>${part}</p>`;
                }
            }
        });
        
        if (inList) {
            html += '</ul>';
        }
        
        content.innerHTML = html;
    } else {
        content.innerHTML = `<p>${text}</p>`;
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}