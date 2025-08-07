/**
 * Floating AI Chat Bubble Component
 * Global AI assistance accessible from any page
 */

let aiChatOpen = false;
let aiMessageHistory = [];
let aiIsProcessing = false;

function initializeFloatingAIChat() {
    // Remove any existing chat elements first
    const existingChat = document.getElementById('floating-ai-chat');
    if (existingChat) {
        existingChat.remove();
    }
    
    // Add floating chat HTML to body
    const floatingChatHTML = `
        <!-- Floating AI Chat Bubble -->
        <div id="floating-ai-chat" class="floating-ai-chat">
            <!-- Chat Toggle Button -->
            <div id="ai-chat-toggle" class="ai-chat-toggle" onclick="toggleAIChat()">
                <i class="material-icons" id="chat-toggle-icon">auto_awesome</i>
            </div>

            <!-- Chat Window -->
            <div id="ai-chat-window" class="ai-chat-window">
                <div class="ai-chat-header">
                    <div class="ai-chat-title">
                        <i class="material-icons">lightbulb</i>
                        <span>AI Pump Expert</span>
                    </div>
                    <button class="ai-chat-close" onclick="closeAIChat()">
                        <i class="material-icons">close</i>
                    </button>
                </div>

                <div class="ai-chat-messages" id="ai-chat-messages">
                    <div class="ai-welcome-message">
                        <div class="ai-avatar">
                            <i class="material-icons">lightbulb</i>
                        </div>
                        <div class="ai-message-content">
                            <p><strong>APE Pumps AI Assistant</strong></p>
                            <p style="font-size: 0.85rem; color: #64748b;">Find your perfect pump. Try:</p>
                            <div class="ai-quick-actions">
                                <button class="ai-quick-btn" onclick="sendQuickQuery('I need pumps for 1500 m³/hr at 25 meters')">
                                    💧 "1500 m³/hr at 25 meters"
                                </button>
                                <button class="ai-quick-btn" onclick="sendQuickQuery('Find pumps for 800 m³/hr at 30m')">
                                    🏭 "800 m³/hr at 30m"
                                </button>
                                <button class="ai-quick-btn" onclick="sendQuickQuery('What pumps work for 2000 m³/hr at 15 meters?')">
                                    📊 "2000 m³/hr at 15 meters"
                                </button>
                            </div>
                            <p style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.75rem;">💡 I work with metric units (m³/hr, meters)</p>
                        </div>
                    </div>
                </div>

                <div class="ai-chat-input-area">
                    <div class="ai-input-wrapper">
                        <textarea 
                            id="ai-chat-input" 
                            class="ai-chat-input" 
                            placeholder="Type flow & head (e.g., 500 m³/hr at 40m)"
                            rows="1"
                            maxlength="1000"></textarea>
                        <button id="ai-send-button" class="ai-send-button" onclick="sendAIMessage()">
                            <i class="material-icons">send</i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Add to body
    document.body.insertAdjacentHTML('beforeend', floatingChatHTML);
    
    // Force lightbulb icon immediately to override browser cache
    setTimeout(() => {
        const toggleIcon = document.getElementById('chat-toggle-icon');
        if (toggleIcon) {
            toggleIcon.textContent = 'lightbulb';
            toggleIcon.innerHTML = 'lightbulb';
            toggleIcon.className = 'material-icons';
        }
    }, 10);
    
    // Setup input handlers
    setupAIChatInput();
}

function toggleAIChat() {
    const chatWindow = document.getElementById('ai-chat-window');
    const toggleIcon = document.getElementById('chat-toggle-icon');
    
    if (aiChatOpen) {
        closeAIChat();
    } else {
        openAIChat();
    }
}

function openAIChat() {
    const chatWindow = document.getElementById('ai-chat-window');
    const toggleIcon = document.getElementById('chat-toggle-icon');
    
    chatWindow.classList.add('open');
    toggleIcon.textContent = 'close';
    aiChatOpen = true;
    
    // Focus on input
    setTimeout(() => {
        const input = document.getElementById('ai-chat-input');
        if (input) input.focus();
    }, 300);
}

function closeAIChat() {
    const chatWindow = document.getElementById('ai-chat-window');
    const toggleIcon = document.getElementById('chat-toggle-icon');
    
    chatWindow.classList.remove('open');
    toggleIcon.textContent = 'auto_awesome';
    aiChatOpen = false;
}

function sendQuickQuery(query) {
    const input = document.getElementById('ai-chat-input');
    if (input) {
        input.value = query;
        sendAIMessage();
    }
}

async function sendAIMessage() {
    const input = document.getElementById('ai-chat-input');
    const message = input.value.trim();
    
    if (!message || aiIsProcessing) return;
    
    // Clear input and reset height
    input.value = '';
    input.style.height = 'auto';
    
    // Add user message
    addAIMessage('user', message);
    showAITypingIndicator();
    
    aiIsProcessing = true;
    const sendButton = document.getElementById('ai-send-button');
    if (sendButton) sendButton.disabled = true;
    
    try {
        const response = await fetch('/api/chat/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: message,
                history: aiMessageHistory.slice(-10)
            })
        });
        
        const data = await response.json();
        
        hideAITypingIndicator();
        
        if (data.error) {
            addAIMessage('assistant', `I apologize, but I encountered an error: ${data.error}`);
        } else {
            addAIMessage('assistant', data.response, data.processing_time, data.confidence_score, data.source_documents || [], data.is_html || false);
        }
        
    } catch (error) {
        console.error('Error sending AI message:', error);
        hideAITypingIndicator();
        addAIMessage('assistant', 'I apologize, but I\'m having trouble connecting to the knowledge base. Please try again in a moment.');
    }
    
    aiIsProcessing = false;
    if (sendButton) sendButton.disabled = false;
    if (input) input.focus();
}

function addAIMessage(sender, content, processingTime = null, confidence = null, sources = [], isHtml = false) {
    const messagesContainer = document.getElementById('ai-chat-messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-message ${sender}`;
    
    // Process content for LaTeX if it's an assistant message and not already HTML
    let processedContent = content;
    if (sender === 'assistant' && !isHtml) {
        processedContent = parseMarkdownContentForAI(content);
    }
    
    const avatarHTML = sender === 'assistant' 
        ? '<div class="ai-avatar"><i class="material-icons">lightbulb</i></div>'
        : '<div class="ai-avatar" style="background: linear-gradient(135deg, #10b981, #059669);"><i class="material-icons">person</i></div>';
    
    let metaHTML = '';
    if (sender === 'assistant' && (processingTime || confidence || sources.length > 0)) {
        metaHTML = '<div style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.7;">';
        if (processingTime) metaHTML += `Response time: ${processingTime.toFixed(2)}s`;
        if (confidence !== null) metaHTML += ` • Confidence: ${Math.round(confidence * 100)}%`;
        if (sources.length > 0) metaHTML += ` • Sources: ${sources.join(', ')}`;
        metaHTML += '</div>';
    }
    
    // Create safe structure first
    messageDiv.innerHTML = avatarHTML + '<div class="ai-message-content"></div>';
    
    // Safely add processed content and metadata
    const contentDiv = messageDiv.querySelector('.ai-message-content');
    if (contentDiv) {
        // Use insertAdjacentHTML for processed content (still allows legitimate HTML from markdown)
        // but ensure it's properly sanitized by the parseMarkdownContentForAI function
        contentDiv.insertAdjacentHTML('beforeend', processedContent);
        if (metaHTML) {
            contentDiv.insertAdjacentHTML('beforeend', metaHTML);
        }
    }
    
    // Append message at the end
    messagesContainer.appendChild(messageDiv);
    // Scroll to bottom to show newest message
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // Store in history
    aiMessageHistory.push({
        sender: sender,
        content: content,
        timestamp: new Date().toISOString()
    });
    
    // Render LaTeX if this is an assistant message
    if (sender === 'assistant' && window.MathJax && MathJax.typesetPromise) {
        setTimeout(() => {
            MathJax.typesetPromise([messageDiv]).then(() => {
                console.log('LaTeX rendering completed for AI message');
            }).catch((err) => console.warn('MathJax rendering error in AI chat:', err));
        }, 100);
    }
}

function parseMarkdownContentForAI(content) {
    if (!content) return '';
    
    // First, escape any HTML entities to prevent XSS
    const escapeHTML = (str) => {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };
    
    // Escape the content first
    let protectedContent = escapeHTML(content);
    
    // Protect LaTeX expressions from markdown processing
    const latexPlaceholders = [];
    
    // Protect display math expressions \\[ ... \\]
    protectedContent = protectedContent.replace(/\\\[([\s\S]*?)\\\]/g, (match, latex) => {
        const placeholder = `LATEX_DISPLAY_${latexPlaceholders.length}`;
        latexPlaceholders.push({ type: 'display', content: match });
        return placeholder;
    });
    
    // Protect inline math expressions \\( ... \\)
    protectedContent = protectedContent.replace(/\\\(([\s\S]*?)\\\)/g, (match, latex) => {
        const placeholder = `LATEX_INLINE_${latexPlaceholders.length}`;
        latexPlaceholders.push({ type: 'inline', content: match });
        return placeholder;
    });
    
    // Comprehensive markdown formatting (consistent with main report page)
    protectedContent = protectedContent
        // Convert headers (#### to h5, ### to h4, ## to h3, # to h2)
        .replace(/^#### (.+)$/gm, '<h5 style="color: #1976d2; margin: 12px 0 6px 0; font-weight: 600; font-size: 0.85rem;">$1</h5>')
        .replace(/^### (.+)$/gm, '<h4 style="color: #1976d2; margin: 15px 0 8px 0; font-weight: 600; font-size: 0.9rem;">$1</h4>')
        .replace(/^## (.+)$/gm, '<h3 style="color: #1976d2; margin: 15px 0 8px 0; font-weight: 600; font-size: 1rem;">$1</h3>')
        .replace(/^# (.+)$/gm, '<h2 style="color: #1976d2; margin: 15px 0 8px 0; font-weight: 600; font-size: 1.1rem;">$1</h2>')
        // Convert bold text (double asterisks)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Convert italic text (single asterisks)
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Convert inline code
        .replace(/`(.*?)`/g, '<code style="background: #f1f5f9; padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.8rem;">$1</code>')
        // Convert numbered lists
        .replace(/^(\d+)\.\s(.+)$/gm, '<div style="margin: 8px 0;"><strong style="color: #1976d2;">$1.</strong> $2</div>')
        // Convert bullet points
        .replace(/^-\s(.+)$/gm, '<div style="margin: 6px 0; padding-left: 16px;">• $1</div>')
        // Convert line breaks
        .replace(/\n/g, '<br>');
    
    // Restore LaTeX expressions
    if (Array.isArray(latexPlaceholders)) {
        latexPlaceholders.forEach((latex, index) => {
            if (latex.type === 'display') {
                protectedContent = protectedContent.replace(`LATEX_DISPLAY_${index}`, latex.content);
            } else {
                protectedContent = protectedContent.replace(`LATEX_INLINE_${index}`, latex.content);
            }
        });
    }
    
    return protectedContent;
}

function showAITypingIndicator() {
    const messagesContainer = document.getElementById('ai-chat-messages');
    if (!messagesContainer) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-typing-indicator';
    typingDiv.id = 'ai-typing-indicator';
    typingDiv.innerHTML = `
        <div class="ai-avatar"><i class="material-icons">auto_awesome</i></div>
        <div class="ai-typing-dots">
            <div class="ai-typing-dot"></div>
            <div class="ai-typing-dot"></div>
            <div class="ai-typing-dot"></div>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function hideAITypingIndicator() {
    const typingIndicator = document.getElementById('ai-typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

function setupAIChatInput() {
    const aiChatInput = document.getElementById('ai-chat-input');
    if (aiChatInput) {
        // Auto-resize textarea
        aiChatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });
        
        // Send message on Enter (but not Shift+Enter)
        aiChatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendAIMessage();
            }
        });
    }
}

// Helper function for pump comparison from chat
function addToComparison(pumpCode) {
    // Store in session storage for comparison page
    let comparisonPumps = JSON.parse(sessionStorage.getItem('comparisonPumps') || '[]');
    if (!comparisonPumps.includes(pumpCode)) {
        comparisonPumps.push(pumpCode);
        sessionStorage.setItem('comparisonPumps', JSON.stringify(comparisonPumps));
        
        // Show feedback
        const button = event.target.closest('.compare-btn');
        if (button) {
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="material-icons">check</i> Added';
            button.style.background = '#10b981';
            button.style.color = 'white';
            setTimeout(() => {
                button.innerHTML = originalText;
                button.style.background = '';
                button.style.color = '';
            }, 2000);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFloatingAIChat();
});