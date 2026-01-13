// Fungsi untuk beralih antara tampilan login, signup, dan forgot password
function switchView(viewName) {
    document.querySelectorAll('.auth-section').forEach(el => el.classList.remove('active'));
    const section = document.getElementById(viewName + 'Section');
    if (section) {
        section.classList.add('active');
    }
}

// Fungsi untuk menampilkan/menyembunyikan password
document.querySelectorAll('.toggle-password').forEach(icon => {
    icon.addEventListener('click', function () {
        const input = this.parentElement.querySelector('input');
        if (input.getAttribute('type') === 'password') {
            input.setAttribute('type', 'text');
            this.classList.remove('fa-eye');
            this.classList.add('fa-eye-slash');
        } else {
            input.setAttribute('type', 'password');
            this.classList.remove('fa-eye-slash');
            this.classList.add('fa-eye');
        }
    });
});

// --- FUNGSI HALAMAN CHAT ---

// Session Management
let currentSessionId = null;
let currentTool = null; // null = direct chat, 'nmap' | 'nikto' = tool mode

// UI Logic for Tool Menu
function setupToolMenu() {
    const hackerBtn = document.getElementById('hacker-mode-btn');
    const toolMenu = document.getElementById('tool-menu');
    const inputBox = document.querySelector('.input-box');
    const msgInput = document.getElementById('msgInput');
    const badgeContainer = document.getElementById('tool-badge-container');

    if (!hackerBtn || !toolMenu) return;

    // Toggle menu
    hackerBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toolMenu.classList.toggle('hidden');
        toolMenu.classList.toggle('active');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!toolMenu.contains(e.target) && e.target !== hackerBtn) {
            toolMenu.classList.remove('active');
            toolMenu.classList.add('hidden');
        }
    });

    // Handle tool selection
    document.querySelectorAll('.tool-option').forEach(option => {
        option.addEventListener('click', () => {
            const tool = option.dataset.tool;
            toolMenu.classList.remove('active');
            toolMenu.classList.add('hidden');

            // Select Tool
            currentTool = tool;
            inputBox.classList.add('tool-active');
            msgInput.placeholder = "Enter target IP or Domain...";

            // Add Badge with Cancel Button
            badgeContainer.innerHTML = `
                <div class="tool-badge">
                    ${tool.charAt(0).toUpperCase() + tool.slice(1)}
                    <span class="cancel-btn" onclick="cancelTool()"><i class="fa-solid fa-xmark"></i></span>
                </div>
            `;
        });
    });
}

// Global function to cancel tool (called by inline onclick)
window.cancelTool = function () {
    const inputBox = document.querySelector('.input-box');
    const msgInput = document.getElementById('msgInput');
    const badgeContainer = document.getElementById('tool-badge-container');

    currentTool = null;
    inputBox.classList.remove('tool-active');
    msgInput.placeholder = "Message AIVAST...";
    badgeContainer.innerHTML = '';
};

// Helper to safely render Markdown content
function renderMessageContent(element, content) {
    if (!content) {
        element.innerHTML = '';
        return;
    }
    // Configure marked for GFM breaks
    marked.setOptions({
        breaks: true, // Convert \n to <br>
        gfm: true
    });

    element.innerHTML = marked.parse(content);
    element.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Fungsi untuk menampilkan pesan di UI
function displayMessage(message, type) {
    const chatContainer = document.getElementById('chatContainer');
    const welcomeScreen = document.getElementById('welcomeScreen');
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none'; // Ensure welcome screen is hidden when chatting acts
    }

    const messageWrapper = document.createElement('div');
    messageWrapper.classList.add('message-wrapper', type, 'show');

    const avatar = document.createElement('div');
    avatar.classList.add('avatar');
    const icon = document.createElement('i');
    icon.classList.add(type === 'user' ? 'fa-regular' : 'fa-solid', type === 'user' ? 'fa-user' : 'fa-robot');
    avatar.appendChild(icon);

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');

    // Check if message is already HTML (e.g., spinner or scan result) or Markdown text
    // We assume if it starts with < it is likely HTML we constructed, otherwise Markdown.
    // However, it's safer to always render markdown for user/bot text, and treat constructed HTML differently or bypass.
    // For now, if we pass HTML strings (like spinner), marked might escape them.
    // Let's rely on caller or handle spinner specifically.

    // Only render markdown if it's NOT a structured HTML scan result or spinner
    if (message && (message.trim().startsWith('<i ') || message.trim().startsWith('<div '))) {
        bubble.innerHTML = message;
    } else {
        renderMessageContent(bubble, message);
    }

    messageWrapper.appendChild(avatar);
    messageWrapper.appendChild(bubble);
    chatContainer.appendChild(messageWrapper);

    // Scroll to bottom (Scroll parent container .chat-main-content)
    const mainContent = document.querySelector('.chat-main-content');
    if (mainContent) {
        mainContent.scrollTop = mainContent.scrollHeight;
    } else {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    return bubble;
}

// Fungsi untuk polling status scan
async function pollScanStatus(scanId, botMessageBubble) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/scans/${scanId}/status`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                const summary = data.analysis?.summary || "Analisis selesai. Tidak ada ringkasan yang tersedia.";

                // Construct HTML for scan result, render summary as markdown
                const scanResultHTML = `
                    <div class="scan-result">
                        <div class="scan-header">
                            <i class="fa-solid fa-check-circle" style="color: var(--badge-text-completed)"></i>
                            <strong>Scan Completed</strong>
                        </div>
                        <div class="scan-details">
                            <p>Target: ${data.target || 'Unknown'}</p>
                            <p>Tool: ${data.tool || 'Unknown'}</p>
                            <div class="summary" id="scan-summary-${scanId}"></div>
                        </div>
                    </div>`;

                botMessageBubble.innerHTML = scanResultHTML;

                // Render markdown summary into the specific div
                const summaryDiv = botMessageBubble.querySelector(`#scan-summary-${scanId}`);
                if (summaryDiv) {
                    renderMessageContent(summaryDiv, summary);
                }

                fetchSessions(); // Refresh session list
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                const error = data.error || "Scan gagal karena kesalahan server.";
                botMessageBubble.innerHTML = `<div class="error-message">Scan gagal: ${error}</div>`;
                fetchSessions();
            } else {
                // Still running
                botMessageBubble.innerHTML = `Scanning target with ${data.tool || 'tool'}... <i class='fa-solid fa-spinner fa-spin'></i>`;
            }
        } catch (error) {
            clearInterval(pollInterval);
            console.error("Error polling scan status:", error);
            botMessageBubble.innerHTML = "Maaf, terjadi kesalahan saat memeriksa status scan.";
            fetchSessions();
        }
    }, 3000);
}

// Fungsi mengirim pesan (bisa chat biasa atau perintah scan)
async function sendMessage() {
    const input = document.getElementById('msgInput');
    const message = input.value.trim();

    if (message !== "") {
        displayMessage(message, 'user');
        input.value = '';

        // MODE 1: Tool Scan Mode
        if (currentTool) {
            const botMessageBubble = displayMessage(`Initializing ${currentTool} scan... <i class='fa-solid fa-spinner fa-spin'></i>`, 'bot');
            try {
                const body = { target: message, use_ai: true, tool: currentTool };
                if (currentSessionId) {
                    body.session_id = currentSessionId;
                }

                const response = await fetch('/api/v1/scans', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();

                if (data.session_id) {
                    currentSessionId = data.session_id;
                    fetchSessions();
                }

                if (data.scan_id) {
                    pollScanStatus(data.scan_id, botMessageBubble);
                } else {
                    botMessageBubble.innerHTML = "Gagal memulai scan.";
                }

                // Reset tool mode after sending? Maybe keep it active for repeated scans?
                // Let's keep it active for now, user can deselect manually.

            } catch (error) {
                console.error("Error starting scan:", error);
                botMessageBubble.innerHTML = "Error during scan initialization.";
            }

            // MODE 2: Direct Chat Mode
        } else {
            const botMessageBubble = displayMessage("<i class='fa-solid fa-spinner fa-spin'></i>", 'bot');
            try {
                const body = { message: message };
                if (currentSessionId) {
                    body.session_id = currentSessionId;
                }

                const response = await fetch('/api/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();

                if (data.session_id) {
                    currentSessionId = data.session_id;
                    fetchSessions();
                }

                if (data.ai_message) {
                    // Update content with markdown rendering
                    renderMessageContent(botMessageBubble, data.ai_message.content);
                }

            } catch (error) {
                console.error("Error creating chat:", error);
                botMessageBubble.innerHTML = "Failed to communicate with AI.";
            }
        }
    }
}

async function handleEnter(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}

// Session Management Functions
async function startNewChat() {
    currentSessionId = null;
    currentTool = null;
    document.querySelector('.input-box')?.classList.remove('tool-active');
    document.getElementById('msgInput').placeholder = "Message AIVAST...";

    document.getElementById('chatContainer').innerHTML = `
        <div class="welcome-screen" id="welcomeScreen">
             <img src="/static/img/chatbot_icon.png" class="big-robot" alt="Robot AI">
             <p class="welcome-text">welcome back, ready to dive?</p>
        </div>
    `;

    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));

    if (window.innerWidth <= 768) {
        toggleSidebar();
    }
}

async function fetchSessions() {
    try {
        const response = await fetch('/api/v1/sessions');
        const data = await response.json();
        const historyList = document.getElementById('historyList');
        if (!historyList) return;
        historyList.innerHTML = '';

        if (data.sessions && data.sessions.length > 0) {
            data.sessions.forEach(session => {
                const li = document.createElement('li');
                li.className = 'history-item';
                if (session.id === currentSessionId) li.classList.add('active');

                li.innerHTML = `
                    <div class="history-info" onclick="loadSession(${session.id})">
                        <span class="history-title">${session.title}</span>
                        <span style="font-size: 0.7em; color: var(--subtitle-color);">${new Date(session.updated_at).toLocaleDateString()}</span>
                    </div>
                    <div class="history-actions">
                        <button class="action-btn" onclick="renameSession(${session.id}, '${session.title.replace(/'/g, "\\'")}', event)"><i class="fa-solid fa-pen"></i></button>
                        <button class="action-btn" onclick="deleteSession(${session.id}, event)"><i class="fa-solid fa-trash"></i></button>
                    </div>
                `;


                historyList.appendChild(li);
            });
        } else {
            historyList.innerHTML = '<li class="history-item" style="cursor:default;">No conversations yet.</li>';
        }
    } catch (error) {
        console.error('Error fetching sessions:', error);
    }
}

async function renameSession(sessionId, currentTitle, event) {
    event.stopPropagation(); // Prevent loading session
    const newTitle = prompt("Enter new title:", currentTitle);
    if (newTitle && newTitle.trim() !== "") {
        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle.trim() })
            });
            if (response.ok) {
                fetchSessions();
            }
        } catch (error) {
            console.error("Error renaming session", error);
        }
    }
}

async function deleteSession(sessionId, event) {
    event.stopPropagation();
    if (confirm("Are you sure you want to delete this chat?")) {
        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                if (currentSessionId === sessionId) {
                    startNewChat();
                }
                fetchSessions();
            }
        } catch (error) {
            console.error("Error deleting session", error);
        }
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    currentTool = null; // Reset tool mode when loading history
    document.querySelector('.input-box')?.classList.remove('tool-active');

    try {
        const response = await fetch(`/api/v1/sessions/${sessionId}`);
        const data = await response.json();

        const chatContainer = document.getElementById('chatContainer');
        chatContainer.innerHTML = '';

        fetchSessions();

        // Check if we have a unified timeline
        if (data.timeline) {
            data.timeline.forEach(item => {
                if (item.type === 'message') {
                    // It's a chat message
                    displayMessage(item.content, item.role === 'assistant' ? 'bot' : 'user');
                } else if (item.type === 'scan') {
                    // It's a scan result
                    let content = '';
                    if (item.status === 'completed') {
                        const analysis = item.analysis || {};
                        const summary = analysis.summary || 'No summary available.';
                        // Use a placeholder div for the summary to render markdown into
                        const summaryId = `history-scan-summary-${item.id}`;
                        content = `<div class="scan-result">
                            <div class="scan-header">
                                <i class="fa-solid fa-check-circle" style="color: var(--badge-text-completed)"></i>
                                <strong>Scan Completed</strong>
                            </div>
                            <div class="scan-details">
                                <p>Target: ${item.target}</p>
                                <p>Tool: ${item.tool}</p>
                                <p>Risk: <span class="badge ${item.risk_level ? item.risk_level.toLowerCase() : 'unknown'}">${item.risk_level || 'Unknown'}</span></p>
                                <div class="summary" id="${summaryId}"></div>
                            </div>
                        </div>`;

                        const bubble = displayMessage(content, 'bot');
                        const summaryEl = bubble.querySelector(`#${summaryId}`);
                        if (summaryEl) {
                            renderMessageContent(summaryEl, summary);
                        }

                    } else {
                        content = `<div class="error-message">Scan Failed or Pending.</div>`;
                        displayMessage(content, 'bot');
                    }
                }
            });
        }
        // Fallback for old sessions (though timeline should cover it)
        else if (data.scans) {
            data.scans.forEach(scan => {
                displayMessage(`Scan Target: ${scan.target}`, 'user');
                // ... render scan ...
                displayMessage('Legacy scan view support limited.', 'bot');
            });
        }

    } catch (e) {
        console.error("Failed to load session", e);
    }

    if (window.innerWidth <= 768) {
        toggleSidebar();
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const chatMainContent = document.querySelector('.chat-main-content');
    const inputArea = document.querySelector('.input-area');

    sidebar.classList.toggle('active');
    chatMainContent.classList.toggle('sidebar-open');
    inputArea.classList.toggle('sidebar-open');
}

function logout() {
    window.location.href = '/logout';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Only fetch sessions if we are on the chat page
    if (document.getElementById('chatContainer')) {
        fetchSessions();
        setupToolMenu(); // Initialize tool menu

        const chatInput = document.getElementById('msgInput');
        const sendButton = document.getElementById('sendBtn');

        if (chatInput) {
            chatInput.addEventListener('keydown', handleEnter);
        }
        if (sendButton) {
            sendButton.addEventListener('click', sendMessage);
        }
    }
});
