/**
 * Conversation Interface for Aether Desktop Application
 * Handles chat interface, voice capabilities, and conversation management
 */

class ConversationManager {
    constructor() {
        this.conversations = new Map();
        this.currentConversationId = null;
        this.messageHistory = [];
        this.isTyping = false;
        this.voiceEnabled = false;
        this.sttEnabled = false;
        this.ttsEnabled = false;
        this.isListening = false;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.speechSynthesis = window.speechSynthesis;
        this.speechRecognition = null;
        this.contextReferences = new Map();
        
        this.init();
    }

    async init() {
        console.log('Initializing Conversation Manager');
        
        this.setupEventListeners();
        this.initializeVoiceCapabilities();
        await this.loadConversationHistory();
        this.setupAutoSave();
        
        console.log('Conversation Manager initialized');
    }

    setupEventListeners() {
        // Message input and sending
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-message-btn');
        const voiceButton = document.getElementById('voice-input-btn');
        
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            messageInput.addEventListener('input', () => {
                this.handleTypingIndicator();
            });
        }
        
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        if (voiceButton) {
            voiceButton.addEventListener('click', () => this.toggleVoiceInput());
        }
        
        // Conversation controls
        const newConversationBtn = document.getElementById('new-conversation-btn');
        const exportBtn = document.getElementById('export-conversation-btn');
        const searchBtn = document.getElementById('search-conversations-btn');
        const clearBtn = document.getElementById('clear-conversation-btn');
        
        if (newConversationBtn) {
            newConversationBtn.addEventListener('click', () => this.startNewConversation());
        }
        
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportConversation());
        }
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.toggleSearchPanel());
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearCurrentConversation());
        }
        
        // Voice settings
        const ttsToggle = document.getElementById('tts-enabled');
        const sttToggle = document.getElementById('stt-enabled');
        const voiceSelect = document.getElementById('voice-selection');
        
        if (ttsToggle) {
            ttsToggle.addEventListener('change', (e) => {
                this.ttsEnabled = e.target.checked;
                this.saveSettings();
            });
        }
        
        if (sttToggle) {
            sttToggle.addEventListener('change', (e) => {
                this.sttEnabled = e.target.checked;
                this.saveSettings();
            });
        }
        
        if (voiceSelect) {
            voiceSelect.addEventListener('change', (e) => {
                this.selectedVoice = e.target.value;
                this.saveSettings();
            });
        }
    }

    initializeVoiceCapabilities() {
        // Initialize Speech Recognition (STT)
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.speechRecognition = new SpeechRecognition();
            
            this.speechRecognition.continuous = false;
            this.speechRecognition.interimResults = true;
            this.speechRecognition.lang = 'en-US';
            
            this.speechRecognition.onstart = () => {
                this.isListening = true;
                this.updateVoiceButtonState();
                console.log('Speech recognition started');
            };
            
            this.speechRecognition.onresult = (event) => {
                let finalTranscript = '';
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                if (finalTranscript) {
                    this.handleVoiceInput(finalTranscript);
                }
                
                // Show interim results
                if (interimTranscript) {
                    this.showInterimTranscript(interimTranscript);
                }
            };
            
            this.speechRecognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.isListening = false;
                this.updateVoiceButtonState();
                this.showError(`Voice recognition error: ${event.error}`);
            };
            
            this.speechRecognition.onend = () => {
                this.isListening = false;
                this.updateVoiceButtonState();
                console.log('Speech recognition ended');
            };
            
            this.sttEnabled = true;
        } else {
            console.warn('Speech recognition not supported');
            this.sttEnabled = false;
        }
        
        // Initialize Text-to-Speech (TTS)
        if ('speechSynthesis' in window) {
            this.ttsEnabled = true;
            this.loadVoices();
            
            // Load voices when they become available
            if (speechSynthesis.onvoiceschanged !== undefined) {
                speechSynthesis.onvoiceschanged = () => this.loadVoices();
            }
        } else {
            console.warn('Speech synthesis not supported');
            this.ttsEnabled = false;
        }
        
        this.updateVoiceControls();
    }

    loadVoices() {
        const voices = speechSynthesis.getVoices();
        const voiceSelect = document.getElementById('voice-selection');
        
        if (voiceSelect && voices.length > 0) {
            voiceSelect.innerHTML = '';
            voices.forEach((voice, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `${voice.name} (${voice.lang})`;
                if (voice.default) {
                    option.selected = true;
                    this.selectedVoice = index;
                }
                voiceSelect.appendChild(option);
            });
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('message-input');
        const message = messageInput?.value.trim();
        
        if (!message) return;
        
        // Clear input
        messageInput.value = '';
        
        // Add user message to chat
        this.addMessageToChat({
            id: this.generateMessageId(),
            content: message,
            sender: 'user',
            timestamp: new Date(),
            type: 'text'
        });
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send to AI backend
            const response = await this.sendToAI(message);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add AI response to chat
            this.addMessageToChat({
                id: this.generateMessageId(),
                content: response.content,
                sender: 'assistant',
                timestamp: new Date(),
                type: 'text',
                context: response.context,
                memoryReferences: response.memoryReferences
            });
            
            // Speak response if TTS is enabled
            if (this.ttsEnabled && response.content) {
                this.speakText(response.content);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.showError('Failed to send message. Please try again.');
        }
    }

    async sendToAI(message) {
        // Integration with backend API
        if (window.aetherApp) {
            return await window.aetherApp.invokeCommand('send_message', {
                message: message,
                conversationId: this.currentConversationId,
                context: this.getConversationContext()
            });
        }
        
        // Mock response for development
        await this.delay(1000 + Math.random() * 2000);
        
        const mockResponses = [
            {
                content: "I understand what you're saying. Let me help you with that.",
                context: { topic: 'general', confidence: 0.8 },
                memoryReferences: []
            },
            {
                content: "That's an interesting point. I've noted similar ideas in your previous conversations.",
                context: { topic: 'ideas', confidence: 0.9 },
                memoryReferences: [
                    { id: 'mem_1', content: 'Previous idea about productivity', relevance: 0.7 }
                ]
            },
            {
                content: "Based on your task history, I can suggest some next steps for this project.",
                context: { topic: 'tasks', confidence: 0.85 },
                memoryReferences: [
                    { id: 'task_1', content: 'Related project task', relevance: 0.8 }
                ]
            }
        ];
        
        return mockResponses[Math.floor(Math.random() * mockResponses.length)];
    }

    addMessageToChat(message) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        const messageElement = this.createMessageElement(message);
        chatContainer.appendChild(messageElement);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // Add to message history
        this.messageHistory.push(message);
        
        // Save conversation
        this.saveCurrentConversation();
        
        // Animate message appearance
        requestAnimationFrame(() => {
            messageElement.classList.add('message-appear');
        });
    }

    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.sender}`;
        messageDiv.setAttribute('data-message-id', message.id);
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        let contextHtml = '';
        if (message.context) {
            contextHtml = `
                <div class="message-context">
                    <span class="context-topic">${message.context.topic}</span>
                    <span class="context-confidence">${Math.round(message.context.confidence * 100)}%</span>
                </div>
            `;
        }
        
        let referencesHtml = '';
        if (message.memoryReferences && message.memoryReferences.length > 0) {
            referencesHtml = `
                <div class="memory-references">
                    <div class="references-header">Related memories:</div>
                    ${message.memoryReferences.map(ref => `
                        <div class="memory-reference" data-ref-id="${ref.id}">
                            <span class="ref-content">${ref.content}</span>
                            <span class="ref-relevance">${Math.round(ref.relevance * 100)}%</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${message.sender === 'user' ? '👤' : '🤖'}
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">${message.sender === 'user' ? 'You' : 'Aether'}</span>
                    <span class="message-timestamp">${timestamp}</span>
                </div>
                <div class="message-text">${this.formatMessageContent(message.content)}</div>
                ${contextHtml}
                ${referencesHtml}
                <div class="message-actions">
                    <button class="message-action copy-btn" title="Copy message">📋</button>
                    <button class="message-action speak-btn" title="Speak message">🔊</button>
                    ${message.sender === 'assistant' ? '<button class="message-action regenerate-btn" title="Regenerate response">🔄</button>' : ''}
                </div>
            </div>
        `;
        
        // Add event listeners for message actions
        this.setupMessageActions(messageDiv, message);
        
        return messageDiv;
    }

    setupMessageActions(messageElement, message) {
        const copyBtn = messageElement.querySelector('.copy-btn');
        const speakBtn = messageElement.querySelector('.speak-btn');
        const regenerateBtn = messageElement.querySelector('.regenerate-btn');
        
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(message.content);
                this.showToast('Message copied to clipboard');
            });
        }
        
        if (speakBtn) {
            speakBtn.addEventListener('click', () => {
                this.speakText(message.content);
            });
        }
        
        if (regenerateBtn) {
            regenerateBtn.addEventListener('click', () => {
                this.regenerateResponse(message);
            });
        }
        
        // Memory reference click handlers
        const memoryRefs = messageElement.querySelectorAll('.memory-reference');
        memoryRefs.forEach(ref => {
            ref.addEventListener('click', () => {
                const refId = ref.getAttribute('data-ref-id');
                this.showMemoryReference(refId);
            });
        });
    }

    formatMessageContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="message assistant">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="typing-animation">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        chatContainer.appendChild(typingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    toggleVoiceInput() {
        if (!this.sttEnabled) {
            this.showError('Speech recognition is not available');
            return;
        }
        
        if (this.isListening) {
            this.stopVoiceInput();
        } else {
            this.startVoiceInput();
        }
    }

    startVoiceInput() {
        if (!this.speechRecognition) return;
        
        try {
            this.speechRecognition.start();
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.showError('Failed to start voice input');
        }
    }

    stopVoiceInput() {
        if (this.speechRecognition && this.isListening) {
            this.speechRecognition.stop();
        }
    }

    handleVoiceInput(transcript) {
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.value = transcript;
            messageInput.focus();
        }
        
        // Auto-send if enabled
        const autoSendVoice = document.getElementById('auto-send-voice')?.checked;
        if (autoSendVoice) {
            setTimeout(() => this.sendMessage(), 500);
        }
    }

    showInterimTranscript(transcript) {
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.placeholder = `Listening: "${transcript}"`;
        }
    }

    speakText(text) {
        if (!this.ttsEnabled || !this.speechSynthesis) return;
        
        // Cancel any ongoing speech
        this.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Set voice if selected
        if (this.selectedVoice !== undefined) {
            const voices = this.speechSynthesis.getVoices();
            utterance.voice = voices[this.selectedVoice];
        }
        
        // Configure speech parameters
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 0.8;
        
        utterance.onstart = () => {
            console.log('Started speaking');
            this.updateSpeakingState(true);
        };
        
        utterance.onend = () => {
            console.log('Finished speaking');
            this.updateSpeakingState(false);
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event.error);
            this.updateSpeakingState(false);
        };
        
        this.speechSynthesis.speak(utterance);
    }

    updateVoiceButtonState() {
        const voiceButton = document.getElementById('voice-input-btn');
        if (voiceButton) {
            voiceButton.classList.toggle('listening', this.isListening);
            voiceButton.title = this.isListening ? 'Stop listening' : 'Start voice input';
        }
    }

    updateSpeakingState(isSpeaking) {
        const speakButtons = document.querySelectorAll('.speak-btn');
        speakButtons.forEach(btn => {
            btn.classList.toggle('speaking', isSpeaking);
        });
    }

    updateVoiceControls() {
        const sttToggle = document.getElementById('stt-enabled');
        const ttsToggle = document.getElementById('tts-enabled');
        const voiceButton = document.getElementById('voice-input-btn');
        
        if (sttToggle) {
            sttToggle.checked = this.sttEnabled;
            sttToggle.disabled = !this.speechRecognition;
        }
        
        if (ttsToggle) {
            ttsToggle.checked = this.ttsEnabled;
            ttsToggle.disabled = !this.speechSynthesis;
        }
        
        if (voiceButton) {
            voiceButton.disabled = !this.sttEnabled;
        }
    }

    startNewConversation() {
        this.currentConversationId = this.generateConversationId();
        this.messageHistory = [];
        
        // Clear chat display
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            chatContainer.innerHTML = '';
        }
        
        // Add welcome message
        this.addMessageToChat({
            id: this.generateMessageId(),
            content: "Hello! I'm Aether, your AI companion. How can I help you today?",
            sender: 'assistant',
            timestamp: new Date(),
            type: 'text'
        });
        
        this.updateConversationTitle();
        console.log('Started new conversation:', this.currentConversationId);
    }

    async loadConversationHistory() {
        try {
            // Load from backend or localStorage
            const savedConversations = localStorage.getItem('aether-conversations');
            if (savedConversations) {
                const conversations = JSON.parse(savedConversations);
                this.conversations = new Map(Object.entries(conversations));
            }
            
            // Load most recent conversation or start new one
            if (this.conversations.size > 0) {
                const lastConversationId = Array.from(this.conversations.keys()).pop();
                this.loadConversation(lastConversationId);
            } else {
                this.startNewConversation();
            }
            
        } catch (error) {
            console.error('Error loading conversation history:', error);
            this.startNewConversation();
        }
    }

    loadConversation(conversationId) {
        const conversation = this.conversations.get(conversationId);
        if (!conversation) return;
        
        this.currentConversationId = conversationId;
        this.messageHistory = conversation.messages || [];
        
        // Display messages
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            chatContainer.innerHTML = '';
            this.messageHistory.forEach(message => {
                const messageElement = this.createMessageElement(message);
                chatContainer.appendChild(messageElement);
            });
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        this.updateConversationTitle();
    }

    saveCurrentConversation() {
        if (!this.currentConversationId) return;
        
        const conversation = {
            id: this.currentConversationId,
            title: this.generateConversationTitle(),
            messages: this.messageHistory,
            createdAt: this.conversations.get(this.currentConversationId)?.createdAt || new Date(),
            updatedAt: new Date()
        };
        
        this.conversations.set(this.currentConversationId, conversation);
        
        // Save to localStorage
        try {
            const conversationsObj = Object.fromEntries(this.conversations);
            localStorage.setItem('aether-conversations', JSON.stringify(conversationsObj));
        } catch (error) {
            console.error('Error saving conversation:', error);
        }
    }

    setupAutoSave() {
        // Auto-save every 30 seconds
        setInterval(() => {
            if (this.messageHistory.length > 0) {
                this.saveCurrentConversation();
            }
        }, 30000);
    }

    exportConversation() {
        if (!this.currentConversationId || this.messageHistory.length === 0) {
            this.showError('No conversation to export');
            return;
        }
        
        const conversation = this.conversations.get(this.currentConversationId);
        const exportData = {
            title: conversation?.title || 'Untitled Conversation',
            exportedAt: new Date().toISOString(),
            messages: this.messageHistory.map(msg => ({
                sender: msg.sender,
                content: msg.content,
                timestamp: msg.timestamp,
                context: msg.context,
                memoryReferences: msg.memoryReferences
            }))
        };
        
        // Create downloadable file
        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `aether-conversation-${this.currentConversationId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast('Conversation exported successfully');
    }

    clearCurrentConversation() {
        if (confirm('Are you sure you want to clear this conversation? This action cannot be undone.')) {
            this.messageHistory = [];
            const chatContainer = document.getElementById('chat-messages');
            if (chatContainer) {
                chatContainer.innerHTML = '';
            }
            this.saveCurrentConversation();
            this.showToast('Conversation cleared');
        }
    }

    toggleSearchPanel() {
        const searchPanel = document.getElementById('search-panel');
        if (searchPanel) {
            searchPanel.classList.toggle('open');
            if (searchPanel.classList.contains('open')) {
                const searchInput = document.getElementById('search-input');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        }
    }

    // Utility methods
    generateConversationId() {
        return 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    generateMessageId() {
        return 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    generateConversationTitle() {
        if (this.messageHistory.length === 0) return 'New Conversation';
        
        const firstUserMessage = this.messageHistory.find(msg => msg.sender === 'user');
        if (firstUserMessage) {
            return firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '');
        }
        
        return 'Conversation ' + new Date().toLocaleDateString();
    }

    updateConversationTitle() {
        const titleElement = document.getElementById('conversation-title');
        if (titleElement) {
            titleElement.textContent = this.generateConversationTitle();
        }
    }

    getConversationContext() {
        return {
            conversationId: this.currentConversationId,
            messageCount: this.messageHistory.length,
            recentMessages: this.messageHistory.slice(-5),
            timestamp: new Date()
        };
    }

    handleTypingIndicator() {
        // Show typing indicator to other users (if multi-user)
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            // Hide typing indicator
        }, 1000);
    }

    showMemoryReference(refId) {
        console.log('Showing memory reference:', refId);
        // Implementation for showing detailed memory reference
        this.showToast(`Memory reference: ${refId}`);
    }

    regenerateResponse(message) {
        console.log('Regenerating response for message:', message.id);
        // Implementation for regenerating AI response
        this.showToast('Response regeneration not yet implemented');
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'conversation-error';
        errorDiv.innerHTML = `
            <div class="error-content">
                <span class="error-icon">⚠️</span>
                <span class="error-message">${message}</span>
                <button class="error-close">×</button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorDiv.classList.add('fade-out');
            setTimeout(() => errorDiv.remove(), 500);
        }, 5000);
        
        // Close button
        errorDiv.querySelector('.error-close').addEventListener('click', () => {
            errorDiv.remove();
        });
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'conversation-toast';
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    saveSettings() {
        const settings = {
            ttsEnabled: this.ttsEnabled,
            sttEnabled: this.sttEnabled,
            selectedVoice: this.selectedVoice
        };
        
        localStorage.setItem('aether-conversation-settings', JSON.stringify(settings));
    }

    loadSettings() {
        try {
            const saved = localStorage.getItem('aether-conversation-settings');
            if (saved) {
                const settings = JSON.parse(saved);
                this.ttsEnabled = settings.ttsEnabled !== false;
                this.sttEnabled = settings.sttEnabled !== false;
                this.selectedVoice = settings.selectedVoice;
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    destroy() {
        // Cleanup
        if (this.speechRecognition) {
            this.speechRecognition.stop();
        }
        
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }
        
        clearTimeout(this.typingTimeout);
        this.saveCurrentConversation();
    }
}

// Export for use in main application
window.ConversationManager = ConversationManager;Voice
: this.selectedVoice,
            autoSendVoice: document.getElementById('auto-send-voice')?.checked || false
        };
        
        localStorage.setItem('aether-conversation-settings', JSON.stringify(settings));
    }

    loadSettings() {
        try {
            const saved = localStorage.getItem('aether-conversation-settings');
            if (saved) {
                const settings = JSON.parse(saved);
                this.ttsEnabled = settings.ttsEnabled !== false;
                this.sttEnabled = settings.sttEnabled !== false;
                this.selectedVoice = settings.selectedVoice;
                
                // Update UI
                const ttsToggle = document.getElementById('tts-enabled');
                const sttToggle = document.getElementById('stt-enabled');
                const voiceSelect = document.getElementById('voice-selection');
                const autoSendToggle = document.getElementById('auto-send-voice');
                
                if (ttsToggle) ttsToggle.checked = this.ttsEnabled;
                if (sttToggle) sttToggle.checked = this.sttEnabled;
                if (voiceSelect && this.selectedVoice !== undefined) {
                    voiceSelect.value = this.selectedVoice;
                }
                if (autoSendToggle) autoSendToggle.checked = settings.autoSendVoice;
            }
        } catch (error) {
            console.error('Error loading conversation settings:', error);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    destroy() {
        // Clean up resources
        if (this.speechRecognition) {
            this.speechRecognition.stop();
        }
        
        if (this.speechSynthesis) {
            this.speechSynthesis.cancel();
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        // Clear intervals
        clearTimeout(this.typingTimeout);
        
        console.log('Conversation Manager destroyed');
    }
}

// Advanced Conversation Features
class ConversationSearch {
    constructor(conversationManager) {
        this.conversationManager = conversationManager;
        this.searchIndex = new Map();
        this.init();
    }

    init() {
        this.setupSearchEventListeners();
        this.buildSearchIndex();
    }

    setupSearchEventListeners() {
        const searchInput = document.getElementById('search-input');
        const searchBtn = document.getElementById('search-conversations-btn');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.performSearch(e.target.value);
            });
            
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch(e.target.value);
                }
            });
        }
        
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.toggleSearchPanel();
            });
        }
    }

    buildSearchIndex() {
        // Build search index from all conversations
        this.searchIndex.clear();
        
        for (const [conversationId, conversation] of this.conversationManager.conversations) {
            const searchableText = conversation.messages
                .map(msg => msg.content)
                .join(' ')
                .toLowerCase();
            
            this.searchIndex.set(conversationId, {
                conversation,
                searchableText,
                title: conversation.title || 'Untitled Conversation'
            });
        }
    }

    performSearch(query) {
        if (!query || query.length < 2) {
            this.clearSearchResults();
            return;
        }
        
        const results = [];
        const searchTerm = query.toLowerCase();
        
        for (const [conversationId, data] of this.searchIndex) {
            if (data.searchableText.includes(searchTerm) || 
                data.title.toLowerCase().includes(searchTerm)) {
                
                // Find specific message matches
                const messageMatches = data.conversation.messages.filter(msg => 
                    msg.content.toLowerCase().includes(searchTerm)
                );
                
                results.push({
                    conversationId,
                    title: data.title,
                    matches: messageMatches,
                    relevance: this.calculateRelevance(searchTerm, data)
                });
            }
        }
        
        // Sort by relevance
        results.sort((a, b) => b.relevance - a.relevance);
        
        this.displaySearchResults(results, query);
    }

    calculateRelevance(searchTerm, data) {
        let relevance = 0;
        
        // Title match gets higher score
        if (data.title.toLowerCase().includes(searchTerm)) {
            relevance += 10;
        }
        
        // Count occurrences in content
        const matches = (data.searchableText.match(new RegExp(searchTerm, 'gi')) || []).length;
        relevance += matches;
        
        return relevance;
    }

    displaySearchResults(results, query) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;
        
        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="search-no-results">
                    <div class="no-results-icon">🔍</div>
                    <div class="no-results-text">No results found for "${query}"</div>
                </div>
            `;
            return;
        }
        
        resultsContainer.innerHTML = results.map(result => `
            <div class="search-result" data-conversation-id="${result.conversationId}">
                <div class="search-result-title">${result.title}</div>
                <div class="search-result-snippet">
                    ${result.matches.slice(0, 2).map(match => 
                        this.highlightSearchTerm(match.content.substring(0, 100) + '...', query)
                    ).join('<br>')}
                </div>
                <div class="search-result-meta">
                    ${result.matches.length} message${result.matches.length !== 1 ? 's' : ''} found
                </div>
            </div>
        `).join('');
        
        // Add click handlers
        resultsContainer.querySelectorAll('.search-result').forEach(result => {
            result.addEventListener('click', () => {
                const conversationId = result.getAttribute('data-conversation-id');
                this.conversationManager.loadConversation(conversationId);
                this.toggleSearchPanel();
            });
        });
    }

    highlightSearchTerm(text, term) {
        const regex = new RegExp(`(${term})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    clearSearchResults() {
        const resultsContainer = document.getElementById('search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
    }

    toggleSearchPanel() {
        const searchPanel = document.getElementById('search-panel');
        if (searchPanel) {
            searchPanel.classList.toggle('open');
            if (searchPanel.classList.contains('open')) {
                const searchInput = document.getElementById('search-input');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        }
    }
}

// Conversation Export/Import Manager
class ConversationExportManager {
    constructor(conversationManager) {
        this.conversationManager = conversationManager;
    }

    exportConversation(conversationId = null) {
        const targetId = conversationId || this.conversationManager.currentConversationId;
        if (!targetId) {
            throw new Error('No conversation to export');
        }
        
        const conversation = this.conversationManager.conversations.get(targetId);
        if (!conversation) {
            throw new Error('Conversation not found');
        }
        
        const exportData = {
            version: '1.0',
            exportedAt: new Date().toISOString(),
            conversation: {
                id: conversation.id,
                title: conversation.title,
                createdAt: conversation.createdAt,
                updatedAt: conversation.updatedAt,
                messages: conversation.messages.map(msg => ({
                    id: msg.id,
                    sender: msg.sender,
                    content: msg.content,
                    timestamp: msg.timestamp,
                    type: msg.type,
                    context: msg.context,
                    memoryReferences: msg.memoryReferences
                }))
            }
        };
        
        return exportData;
    }

    exportAllConversations() {
        const exportData = {
            version: '1.0',
            exportedAt: new Date().toISOString(),
            conversations: Array.from(this.conversationManager.conversations.values()).map(conversation => ({
                id: conversation.id,
                title: conversation.title,
                createdAt: conversation.createdAt,
                updatedAt: conversation.updatedAt,
                messageCount: conversation.messages.length,
                messages: conversation.messages.map(msg => ({
                    id: msg.id,
                    sender: msg.sender,
                    content: msg.content,
                    timestamp: msg.timestamp,
                    type: msg.type,
                    context: msg.context,
                    memoryReferences: msg.memoryReferences
                }))
            }))
        };
        
        return exportData;
    }

    downloadExport(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    importConversation(jsonData) {
        try {
            const data = typeof jsonData === 'string' ? JSON.parse(jsonData) : jsonData;
            
            if (data.version !== '1.0') {
                throw new Error('Unsupported export version');
            }
            
            if (data.conversation) {
                // Single conversation import
                const conversation = data.conversation;
                this.conversationManager.conversations.set(conversation.id, conversation);
                this.conversationManager.saveCurrentConversation();
                return 1;
            } else if (data.conversations) {
                // Multiple conversations import
                let importCount = 0;
                for (const conversation of data.conversations) {
                    this.conversationManager.conversations.set(conversation.id, conversation);
                    importCount++;
                }
                this.conversationManager.saveCurrentConversation();
                return importCount;
            } else {
                throw new Error('Invalid export format');
            }
        } catch (error) {
            console.error('Import error:', error);
            throw new Error(`Failed to import conversation: ${error.message}`);
        }
    }
}

// Voice Command Processor
class VoiceCommandProcessor {
    constructor(conversationManager) {
        this.conversationManager = conversationManager;
        this.commands = new Map();
        this.setupCommands();
    }

    setupCommands() {
        // Basic navigation commands
        this.commands.set(/^(new|start) conversation$/i, () => {
            this.conversationManager.startNewConversation();
            return 'Started a new conversation';
        });
        
        this.commands.set(/^clear conversation$/i, () => {
            this.conversationManager.clearCurrentConversation();
            return 'Conversation cleared';
        });
        
        this.commands.set(/^export conversation$/i, () => {
            this.conversationManager.exportConversation();
            return 'Conversation exported';
        });
        
        this.commands.set(/^search (.+)$/i, (match) => {
            const query = match[1];
            this.conversationManager.searchManager?.performSearch(query);
            return `Searching for "${query}"`;
        });
        
        // Voice settings commands
        this.commands.set(/^(enable|disable) voice$/i, (match) => {
            const enable = match[1].toLowerCase() === 'enable';
            this.conversationManager.ttsEnabled = enable;
            this.conversationManager.saveSettings();
            return `Voice ${enable ? 'enabled' : 'disabled'}`;
        });
        
        this.commands.set(/^(stop|pause) speaking$/i, () => {
            this.conversationManager.speechSynthesis?.cancel();
            return 'Stopped speaking';
        });
    }

    processCommand(text) {
        const normalizedText = text.trim();
        
        for (const [pattern, handler] of this.commands) {
            const match = normalizedText.match(pattern);
            if (match) {
                try {
                    const result = handler(match);
                    return { success: true, message: result };
                } catch (error) {
                    return { success: false, message: `Command failed: ${error.message}` };
                }
            }
        }
        
        return null; // No command matched
    }
}

// Initialize conversation system
window.ConversationManager = ConversationManager;
window.ConversationSearch = ConversationSearch;
window.ConversationExportManager = ConversationExportManager;
window.VoiceCommandProcessor = VoiceCommandProcessor;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('conversations-page')) {
        window.conversationManager = new ConversationManager();
        window.conversationSearch = new ConversationSearch(window.conversationManager);
        window.conversationExportManager = new ConversationExportManager(window.conversationManager);
        window.voiceCommandProcessor = new VoiceCommandProcessor(window.conversationManager);
        
        // Add voice command processing to conversation manager
        const originalHandleVoiceInput = window.conversationManager.handleVoiceInput;
        window.conversationManager.handleVoiceInput = function(transcript) {
            // Check for voice commands first
            const commandResult = window.voiceCommandProcessor.processCommand(transcript);
            if (commandResult) {
                if (commandResult.success) {
                    this.showToast(commandResult.message);
                } else {
                    this.showError(commandResult.message);
                }
                return;
            }
            
            // If no command matched, proceed with normal voice input
            originalHandleVoiceInput.call(this, transcript);
        };
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.conversationManager) {
        window.conversationManager.destroy();
    }
});