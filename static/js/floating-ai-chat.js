/**
 * Floating AI Chat Bubble Component
 * Global AI assistance accessible from any page
 */

(function() {
    'use strict';
    
    // Prevent multiple initializations
    if (window.FloatingAIChatLoaded) {
        return;
    }
    window.FloatingAIChatLoaded = true;

    // Global state variables
    if (!window.hasOwnProperty('aiChatOpen')) {
        window.aiChatOpen = false;
    }
    if (!window.hasOwnProperty('aiMessageHistory')) {
        window.aiMessageHistory = [];
    }
    if (!window.hasOwnProperty('aiIsProcessing')) {
        window.aiIsProcessing = false;
    }

async function checkAIChatFeatureEnabled() {
    try {
        const response = await fetch('/api/features/status');
        const data = await response.json();
        return data.success && data.features && data.features.ai_chatbot;
    } catch (error) {
        return true; // Default to enabled if check fails
    }
}

function initializeFloatingAIChat() {
    // Prevent multiple initializations
    if (window.aiChatInitialized) {
        return;
    }
    window.aiChatInitialized = true;
    
    // Check if AI chatbot feature is enabled
    checkAIChatFeatureEnabled().then(enabled => {
        if (!enabled) {
            window.aiChatInitialized = false; // Reset if feature is disabled
            return;
        }
        
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
            <div id="ai-chat-toggle" class="ai-chat-toggle">
                <i class="material-icons" id="chat-toggle-icon">auto_awesome</i>
            </div>

            <!-- Chat Window -->
            <div id="ai-chat-window" class="ai-chat-window">
                <div class="ai-chat-header">
                    <div class="ai-chat-title">
                        <i class="material-icons">lightbulb</i>
                        <span>AI Pump Expert</span>
                    </div>
                    <button class="ai-chat-close">
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
                                <button class="ai-quick-btn" data-query='1781 @ 24'>
                                    💧 Quick: "1781 @ 24"
                                </button>
                                <button class="ai-quick-btn" data-query='1500 m³/hr at 25 meters'>
                                    📊 Full: "1500 m³/hr at 25m"
                                </button>
                                <button class="ai-quick-btn" data-query='800 30 HSC'>
                                    🏭 Type: "800 30 HSC"
                                </button>
                            </div>
                            <p style="font-size: 0.75rem; color: #94a3b8; margin-top: 0.75rem;">💡 Type @ to search pump names (e.g., "@12 WLN" or "@12 WLN 14A 1400 30")</p>
                        </div>
                    </div>
                </div>

                <div class="ai-chat-input-area">
                    <div class="ai-input-wrapper">
                        <textarea 
                            id="ai-chat-input" 
                            class="ai-chat-input" 
                            placeholder="Try: 1781 @ 24 or @12 WLN for pump lookup"
                            rows="1"
                            maxlength="1000"></textarea>
                        <button id="ai-send-button" class="ai-send-button">
                            <i class="material-icons">send</i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

        // Add to body
        document.body.insertAdjacentHTML('beforeend', floatingChatHTML);

        // Bind events without inline handlers
        const toggleBtn = document.getElementById('ai-chat-toggle');
        if (toggleBtn) toggleBtn.addEventListener('click', window.toggleAIChat);
        const closeBtn = document.querySelector('.ai-chat-close');
        if (closeBtn) closeBtn.addEventListener('click', window.closeAIChat);
        const sendBtn = document.getElementById('ai-send-button');
        if (sendBtn) sendBtn.addEventListener('click', window.sendAIMessage);
        document.querySelectorAll('.ai-quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const q = btn.getAttribute('data-query') || '';
                window.sendQuickQuery(q);
            });
        });
        
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
        
        // Setup pump autocomplete
        setupPumpAutocomplete();
    });
}

window.toggleAIChat = function() {
    const chatWindow = document.getElementById('ai-chat-window');
    const toggleIcon = document.getElementById('chat-toggle-icon');
    
    if (window.aiChatOpen) {
        window.closeAIChat();
    } else {
        window.openAIChat();
    }
};

window.openAIChat = function() {
    const chatWindow = document.getElementById('ai-chat-window');
    const toggleIcon = document.getElementById('chat-toggle-icon');
    
    chatWindow.classList.add('open');
    toggleIcon.textContent = 'close';
    window.aiChatOpen = true;
    
    // Focus on input
    setTimeout(() => {
        const input = document.getElementById('ai-chat-input');
        if (input) input.focus();
    }, 300);
};

window.closeAIChat = function() {
    const chatWindow = document.getElementById('ai-chat-window');
    const toggleIcon = document.getElementById('chat-toggle-icon');
    
    chatWindow.classList.remove('open');
    toggleIcon.textContent = 'auto_awesome';
    window.aiChatOpen = false;
};

window.sendQuickQuery = function(query) {
    const input = document.getElementById('ai-chat-input');
    if (input) {
        input.value = query;
        window.sendAIMessage();
    }
};

window.sendAIMessage = async function() {
    const input = document.getElementById('ai-chat-input');
    const message = input.value.trim();
    
    if (!message || window.aiIsProcessing) return;
    
    // Clear input and reset height
    input.value = '';
    input.style.height = 'auto';
    
    // Add user message
    addAIMessage('user', message);
    showAITypingIndicator();
    
    window.aiIsProcessing = true;
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
                history: window.aiMessageHistory.slice(-10)
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
    
    window.aiIsProcessing = false;
    if (sendButton) sendButton.disabled = false;
    if (input) input.focus();
};

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
    window.aiMessageHistory.push({
        sender: sender,
        content: content,
        timestamp: new Date().toISOString()
    });
    
    // Render LaTeX if this is an assistant message
    if (sender === 'assistant' && window.MathJax && MathJax.typesetPromise) {
        setTimeout(() => {
            MathJax.typesetPromise([messageDiv]).then(() => {
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
        
        // Send message on Enter (but not Shift+Enter) - but only if autocomplete is not active
        aiChatInput.addEventListener('keydown', function(e) {
            // Check if autocomplete is visible
            const autocompleteDiv = document.getElementById('pump-autocomplete');
            const isAutocompleteActive = autocompleteDiv && autocompleteDiv.style.display !== 'none';
            
            if (e.key === 'Enter' && !e.shiftKey && !isAutocompleteActive) {
                e.preventDefault();
                window.sendAIMessage();
            }
        });
    }
}

// Helper function for pump comparison from chat
window.addToComparison = function(pumpCode, el) {
    // Store in session storage for comparison page
    let comparisonPumps = JSON.parse(sessionStorage.getItem('comparisonPumps') || '[]');
    if (!comparisonPumps.includes(pumpCode)) {
        comparisonPumps.push(pumpCode);
        sessionStorage.setItem('comparisonPumps', JSON.stringify(comparisonPumps));
        
        // Show feedback
        const target = el || (typeof event !== 'undefined' ? event.target : null);
        const button = target && target.closest ? target.closest('.compare-btn') : null;
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
};

// Function to setup pump autocomplete
function setupPumpAutocomplete() {
    const input = document.getElementById('ai-chat-input');
    if (!input) return;
    
    let pumpNames = [];
    let autocompleteActive = false;
    let selectedIndex = -1;
    
    // Fetch pump names from API
    fetch('/api/pump_list')
        .then(response => response.json())
        .then(data => {
            // Extract pump codes from the objects
            if (data.pumps && Array.isArray(data.pumps)) {
                pumpNames = data.pumps.map(pump => {
                    // Handle different pump object structures
                    if (typeof pump === 'string') {
                        return pump;
                    } else if (pump.pump_code) {
                        return pump.pump_code;
                    } else if (pump.pump_name) {
                        return pump.pump_name;
                    }
                    return '';
                }).filter(name => name); // Remove empty strings
            } else {
                pumpNames = [];
            }
        })
        .catch(error => console.error('Error loading pump names:', error));
    
    // Create autocomplete dropdown
    const autocompleteDiv = document.createElement('div');
    autocompleteDiv.id = 'pump-autocomplete';
    autocompleteDiv.style.cssText = `
        position: absolute;
        bottom: 100%;
        left: 0;
        right: 0;
        max-height: 200px;
        overflow-y: auto;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        display: none;
        z-index: 1000;
        box-shadow: 0 -4px 6px rgba(0,0,0,0.1);
        margin-bottom: 5px;
    `;
    
    const inputWrapper = input.parentElement;
    inputWrapper.style.position = 'relative';
    inputWrapper.appendChild(autocompleteDiv);
    
    // Handle input events
    input.addEventListener('input', function(e) {
        const value = e.target.value;
        const atIndex = value.lastIndexOf('@');
        
        if (atIndex !== -1) {
            const searchTerm = value.substring(atIndex + 1).toLowerCase();
            showPumpSuggestions(searchTerm);
        } else {
            hideAutocomplete();
        }
    });
    
    // Handle keyboard navigation
    input.addEventListener('keydown', function(e) {
        if (!autocompleteActive) return;
        
        const items = autocompleteDiv.querySelectorAll('.pump-suggestion');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, 0);
            updateSelection(items);
        } else if (e.key === 'Enter' && selectedIndex >= 0) {
            e.preventDefault();
            selectPump(items[selectedIndex].textContent);
        } else if (e.key === 'Escape') {
            hideAutocomplete();
        }
    });
    
    function showPumpSuggestions(searchTerm) {
        const matches = pumpNames.filter(name => 
            name && name.toLowerCase && name.toLowerCase().includes(searchTerm)
        ).slice(0, 10);
        
        if (matches.length === 0) {
            hideAutocomplete();
            return;
        }
        
        autocompleteDiv.innerHTML = matches.map((pump, index) => `
            <div class="pump-suggestion" style="
                padding: 8px 12px;
                cursor: pointer;
                font-size: 0.875rem;
                border-bottom: 1px solid #f3f4f6;
                ${index === selectedIndex ? 'background: #eff6ff;' : ''}
            " onmouseover="this.style.background='#eff6ff'" 
               onmouseout="this.style.background='${index === selectedIndex ? '#eff6ff' : 'white'}'"
               onclick="window.selectPumpFromClick('${pump.replace(/'/g, "\\'")}')">${pump}</div>
        `).join('');
        
        autocompleteDiv.style.display = 'block';
        autocompleteActive = true;
        selectedIndex = -1;
    }
    
    function updateSelection(items) {
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.style.background = '#eff6ff';
            } else {
                item.style.background = 'white';
            }
        });
    }
    
    window.selectPumpFromClick = function(pumpName) {
        selectPump(pumpName);
    };
    
    function selectPump(pumpName) {
        const value = input.value;
        const atIndex = value.lastIndexOf('@');
        
        if (atIndex !== -1) {
            input.value = value.substring(0, atIndex) + '@' + pumpName + ' ';
            hideAutocomplete();
            input.focus();
        }
    }
    
    function hideAutocomplete() {
        autocompleteDiv.style.display = 'none';
        autocompleteActive = false;
        selectedIndex = -1;
    }
    
    // Hide on click outside
    document.addEventListener('click', function(e) {
        if (!inputWrapper.contains(e.target)) {
            hideAutocomplete();
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFloatingAIChat();
});

})();