// Axis AI Frontend Application
class AxisAI {
    constructor() {
        this.currentSession = null;
        this.currentUser = null;
        this.websocket = null;
        this.selectedFiles = [];
        this.isRecording = false;
        this.mediaRecorder = null;
        
        this.init();
    }

    async init() {
        console.log('Initializing Axis AI application...');
        this.setupEventListeners();
        this.setupWebSocket();
        await this.loadUserSession();
        this.loadAnalytics();
        this.initializeCharts();
        console.log('Axis AI application initialized');
    }

    setupEventListeners() {
        // Navigation
        document.getElementById('userMenu').addEventListener('click', this.toggleUserDropdown);
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        // File upload
        document.getElementById('mediaUpload').addEventListener('change', this.handleFileUpload.bind(this));

        // Tab switching
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.textContent.toLowerCase().trim();
                this.switchTab(tab);
            });
        });
    }

    setupWebSocket() {
        const wsUrl = `ws://${window.location.host}/api/chat/ws`;
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            // Attempt to reconnect
            setTimeout(() => this.setupWebSocket(), 3000);
        };
    }

    handleWebSocketMessage(data) {
        if (data.type === 'message') {
            this.displayMessage(data.content, 'assistant');
        } else if (data.type === 'status') {
            this.updateStatus(data.content);
        }
    }

    async loadUserSession() {
        try {
            const token = localStorage.getItem('token');
            console.log('Token from localStorage:', token ? 'exists' : 'not found');
            
            // Pause here so user can see console messages
            debugger;
            
            if (!token) {
                console.log('No token found, redirecting to login');
                this.redirectToLogin();
                return;
            }
            
            console.log('Making request to /api/auth/me');
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            console.log('Response status:', response.status);
            
            if (response.ok) {
                this.currentUser = await response.json();
                console.log('User loaded:', this.currentUser);
                this.loadChatHistory();
            } else {
                console.log('Auth failed, clearing token and redirecting');
                localStorage.removeItem('token');
                this.redirectToLogin();
            }
        } catch (error) {
            console.error('Failed to load user session:', error);
            localStorage.removeItem('token');
            this.redirectToLogin();
        }
    }

    async loadChatHistory() {
        try {
            const response = await fetch('/api/chat/sessions', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const sessions = await response.json();
                if (sessions.length > 0) {
                    this.currentSession = sessions[0].id;
                    this.loadMessages(this.currentSession);
                }
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    async loadMessages(sessionId) {
        try {
            const response = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const messages = await response.json();
                const chatContainer = document.getElementById('chatMessages');
                chatContainer.innerHTML = '';
                
                messages.forEach(msg => {
                    this.displayMessage(msg.content, msg.role, false);
                });
            }
        } catch (error) {
            console.error('Failed to load messages:', error);
        }
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        input.value = '';
        this.displayMessage(message, 'user');
        
        try {
            const response = await fetch('/api/chat/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    content: message,
                    role: 'user'
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayMessage(result.response, 'assistant');
            } else {
                console.error('Failed to send message:', response.status, await response.text());
                this.displayMessage('Sorry, there was an error sending your message.', 'error');
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            this.displayMessage('Sorry, there was an error sending your message.', 'error');
        }
    }

    displayMessage(content, role, animate = true) {
        const chatContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message flex ${role === 'user' ? 'justify-end' : 'justify-start'}`;
        
        const messageBubble = document.createElement('div');
        messageBubble.className = `max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
            role === 'user' 
                ? 'bg-indigo-600 text-white' 
                : role === 'assistant'
                    ? 'bg-gray-200 text-gray-800'
                    : 'bg-red-100 text-red-800'
        }`;
        
        messageBubble.textContent = content;
        messageDiv.appendChild(messageBubble);
        chatContainer.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async newSession() {
        try {
            const response = await fetch('/api/chat/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    session_type: 'chat'
                })
            });
            
            if (response.ok) {
                const session = await response.json();
                this.currentSession = session.id;
                document.getElementById('chatMessages').innerHTML = '';
                this.displayMessage('New session started!', 'system');
            }
        } catch (error) {
            console.error('Failed to create new session:', error);
        }
    }

    async saveSession() {
        if (!this.currentSession) return;
        
        try {
            const response = await fetch(`/api/chat/sessions/${this.currentSession}/save`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                this.showNotification('Session saved successfully!', 'success');
            }
        } catch (error) {
            console.error('Failed to save session:', error);
        }
    }

    async exportSession() {
        if (!this.currentSession) return;
        
        try {
            const response = await fetch(`/api/chat/sessions/${this.currentSession}/export`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `session_${this.currentSession}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Failed to export session:', error);
        }
    }

    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.add('hidden');
        });
        
        // Show selected tab
        const targetTab = document.getElementById(`${tabName}Tab`);
        if (targetTab) {
            targetTab.classList.remove('hidden');
        }
        
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('text-indigo-600', 'bg-indigo-50');
            btn.classList.add('text-gray-600');
        });
        
        event.target.closest('.nav-btn').classList.add('text-indigo-600', 'bg-indigo-50');
        
        // Load tab-specific data
        switch(tabName) {
            case 'memory':
                this.loadMemories();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
            case 'code':
                this.initCodeEditor();
                break;
            case 'media':
                this.loadMediaFiles();
                break;
        }
    }

    async loadMemories() {
        try {
            const response = await fetch('/api/memory/list', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const memories = await response.json();
                this.displayMemories(memories);
                this.updateMemoryStats(memories);
            }
        } catch (error) {
            console.error('Failed to load memories:', error);
        }
    }

    displayMemories(memories) {
        const container = document.getElementById('memoryList');
        container.innerHTML = '';
        
        memories.forEach(memory => {
            const memoryDiv = document.createElement('div');
            memoryDiv.className = 'border border-gray-200 rounded-lg p-4 hover:bg-gray-50';
            memoryDiv.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <p class="text-sm text-gray-600">${new Date(memory.timestamp).toLocaleDateString()}</p>
                        <p class="mt-1">${memory.content.substring(0, 200)}${memory.content.length > 200 ? '...' : ''}</p>
                        ${memory.tags ? `<div class="mt-2">
                            ${memory.tags.map(tag => `<span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-1">${tag}</span>`).join('')}
                        </div>` : ''}
                    </div>
                    <div class="ml-4 flex space-x-2">
                        <button onclick="editMemory(${memory.id})" class="text-blue-600 hover:text-blue-800">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteMemory(${memory.id})" class="text-red-600 hover:text-red-800">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(memoryDiv);
        });
    }

    updateMemoryStats(memories) {
        document.getElementById('totalMemories').textContent = memories.length;
        
        const thisWeek = memories.filter(m => {
            const memoryDate = new Date(m.timestamp);
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            return memoryDate > weekAgo;
        });
        
        document.getElementById('weekMemories').textContent = thisWeek.length;
        
        const totalSize = memories.reduce((sum, m) => sum + m.content.length, 0);
        document.getElementById('storageUsed').textContent = `${Math.round(totalSize / 1024)} KB`;
    }

    async searchMemories() {
        const query = document.getElementById('memorySearchInput').value.trim();
        if (!query) return;
        
        try {
            const response = await fetch(`/api/memory/search?query=${encodeURIComponent(query)}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const results = await response.json();
                this.displayMemories(results);
            }
        } catch (error) {
            console.error('Failed to search memories:', error);
        }
    }

    async loadAnalytics() {
        try {
            const response = await fetch('/api/analytics/overview', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            
            if (response.ok) {
                const analytics = await response.json();
                this.updateAnalyticsDashboard(analytics);
            }
        } catch (error) {
            console.error('Failed to load analytics:', error);
        }
    }

    updateAnalyticsDashboard(analytics) {
        document.getElementById('totalSessions').textContent = analytics.sessions?.total || '0';
        document.getElementById('totalMessages').textContent = analytics.messages?.total || '0';
        document.getElementById('totalCodeFiles').textContent = analytics.code_files || '0';
        document.getElementById('activePlugins').textContent = analytics.plugins?.active || '0';
        
        // Update recent activity
        const activityContainer = document.getElementById('recentActivity');
        activityContainer.innerHTML = '';
        
        if (analytics.recent_activity) {
            analytics.recent_activity.forEach(activity => {
                const activityDiv = document.createElement('div');
                activityDiv.className = 'flex items-center space-x-3 text-sm';
                activityDiv.innerHTML = `
                    <div class="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span class="flex-1">${activity.description}</span>
                    <span class="text-gray-500">${new Date(activity.timestamp).toLocaleTimeString()}</span>
                `;
                activityContainer.appendChild(activityDiv);
            });
        }
    }

    initializeCharts() {
        const ctx = document.getElementById('usageChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Messages',
                        data: [12, 19, 3, 5, 2, 3, 7],
                        borderColor: 'rgb(99, 102, 241)',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    }, {
                        label: 'Code Analysis',
                        data: [2, 3, 20, 5, 1, 4, 8],
                        borderColor: 'rgb(16, 185, 129)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    async analyzeCode() {
        const code = document.getElementById('codeEditor').value;
        if (!code.trim()) return;
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/code/analyze/file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    filename: 'editor.py',
                    content: code
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayCodeAnalysis(result);
            }
        } catch (error) {
            console.error('Failed to analyze code:', error);
        } finally {
            this.hideLoading();
        }
    }

    displayCodeAnalysis(analysis) {
        const container = document.getElementById('codeAnalysis');
        container.innerHTML = `
            <div class="space-y-4">
                <div class="bg-blue-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-blue-800">Metrics</h4>
                    <div class="mt-2 grid grid-cols-2 gap-4 text-sm">
                        <div>Lines of Code: ${analysis.metrics.lines_of_code}</div>
                        <div>Complexity: ${analysis.metrics.cyclomatic_complexity}</div>
                        <div>Maintainability: ${analysis.metrics.maintainability_index.toFixed(1)}</div>
                        <div>Analysis Time: ${analysis.analysis_time.toFixed(3)}s</div>
                    </div>
                </div>
                
                ${analysis.issues.length > 0 ? `
                <div class="bg-yellow-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-yellow-800">Issues Found</h4>
                    <div class="mt-2 space-y-2">
                        ${analysis.issues.map(issue => `
                            <div class="text-sm">
                                <span class="font-medium">Line ${issue.line}:</span> ${issue.message}
                                <span class="ml-2 px-2 py-1 text-xs rounded ${
                                    issue.severity === 'high' ? 'bg-red-100 text-red-800' :
                                    issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-blue-100 text-blue-800'
                                }">${issue.severity}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${analysis.suggestions.length > 0 ? `
                <div class="bg-green-50 p-4 rounded-lg">
                    <h4 class="font-semibold text-green-800">Suggestions</h4>
                    <ul class="mt-2 space-y-1 text-sm">
                        ${analysis.suggestions.map(suggestion => `<li>• ${suggestion}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        `;
    }

    async startVoiceRecording() {
        if (this.isRecording) {
            this.stopVoiceRecording();
            return;
        }
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                await this.processAudioRecording(audioBlob);
            };
            
            this.mediaRecorder.start();
            this.isRecording = true;
            
            // Update UI
            const btn = event.target;
            btn.innerHTML = '<i class="fas fa-stop"></i>';
            btn.classList.add('text-red-500');
            
        } catch (error) {
            console.error('Failed to start recording:', error);
        }
    }

    stopVoiceRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Update UI
            const btn = event.target;
            btn.innerHTML = '<i class="fas fa-microphone"></i>';
            btn.classList.remove('text-red-500');
        }
    }

    async processAudioRecording(audioBlob) {
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.wav');
        
        try {
            const response = await fetch('/api/audio/transcribe', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                document.getElementById('messageInput').value = result.transcript;
            }
        } catch (error) {
            console.error('Failed to transcribe audio:', error);
        }
    }

    handleFileUpload(event) {
        this.selectedFiles = Array.from(event.target.files);
        // Process files based on type
        this.selectedFiles.forEach(file => {
            if (file.type.startsWith('image/')) {
                this.processImageFile(file);
            } else if (file.type.startsWith('audio/')) {
                this.processAudioFile(file);
            }
        });
    }

    async processImageFile(file) {
        const formData = new FormData();
        formData.append('image_file', file);
        
        try {
            const response = await fetch('/api/image/analyze', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayMessage(`Image analysis: ${result.description}`, 'assistant');
            }
        } catch (error) {
            console.error('Failed to process image:', error);
        }
    }

    showLoading() {
        document.getElementById('loadingOverlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }

    showNotification(message, type = 'info') {
        // Create and show notification
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${
            type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
            'bg-blue-500'
        }`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    toggleUserDropdown() {
        const dropdown = document.getElementById('userDropdown');
        dropdown.classList.toggle('hidden');
    }

    redirectToLogin() {
        window.location.href = '/login';
    }

    async logout() {
        localStorage.removeItem('token');
        this.redirectToLogin();
    }
}

// Global functions for HTML onclick handlers
function switchTab(tabName) {
    window.axisAI.switchTab(tabName);
}

function sendMessage() {
    window.axisAI.sendMessage();
}

function newSession() {
    window.axisAI.newSession();
}

function saveSession() {
    window.axisAI.saveSession();
}

function exportSession() {
    window.axisAI.exportSession();
}

function searchMemories() {
    window.axisAI.searchMemories();
}

function analyzeCode() {
    window.axisAI.analyzeCode();
}

function startVoiceRecording() {
    window.axisAI.startVoiceRecording();
}

function openFileUpload() {
    document.getElementById('mediaUpload').click();
}

function logout() {
    window.axisAI.logout();
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.axisAI = new AxisAI();
}); 