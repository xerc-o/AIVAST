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

// Session Management & Global State
let currentSessionId = null;
let currentTool = null; // null = direct chat, 'nmap' | 'nikto' | 'gobuster' | 'sqlmap'
let isDeepScan = false;

// UI Logic for Tool Menu
function setupToolMenu() {
    const hackerBtn = document.getElementById('hacker-mode-btn');
    const toolMenu = document.getElementById('tool-menu');
    const inputBox = document.querySelector('.input-box');
    const msgInput = document.getElementById('msgInput');
    const badgeContainer = document.getElementById('tool-badge-container');
    const deepScanToggle = document.getElementById('deep-scan-toggle');
    const deepScanIcon = document.getElementById('deep-scan-icon');

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

    // Handle Deep Scan Toggle
    const deepScanCheckbox = document.getElementById('deep-scan-checkbox');
    if (deepScanCheckbox) {
        const inputBox = document.querySelector('.input-box');
        deepScanCheckbox.addEventListener('change', (e) => {
            isDeepScan = e.target.checked;
            if (isDeepScan) {
                inputBox.classList.add('deep-scan-active');
            } else {
                inputBox.classList.remove('deep-scan-active');
            }
            console.log(`Deep Scan Mode: ${isDeepScan ? 'ON' : 'OFF'}`);
        });
    }

    // Handle tool selection
    document.querySelectorAll('.tool-option').forEach(option => {
        if (option.id === 'deep-scan-toggle') return;

        option.addEventListener('click', () => {
            const tool = option.dataset.tool;
            toolMenu.classList.remove('active');
            toolMenu.classList.add('hidden');

            // Select Tool
            currentTool = tool;
            inputBox.classList.add('tool-active');
            msgInput.placeholder = `Enter target for ${tool.toUpperCase()}...`;

            // Wordlist Toggle Visibility
            const wordlistToggle = document.getElementById('wordlist-toggle-btn');
            if (tool === 'gobuster') {
                wordlistToggle.classList.remove('hidden');
            } else {
                wordlistToggle.classList.add('hidden');
            }

            // Add Badge with Cancel Button
            badgeContainer.innerHTML = `
                <div class="tool-badge">
                    ${tool.charAt(0).toUpperCase() + tool.slice(1)}
                    <span class="cancel-btn" onclick="cancelTool()"><i class="fa-solid fa-xmark"></i></span>
                </div>
            `;
        });
    });

    // Wordlist Toggle click
    const wordlistToggle = document.getElementById('wordlist-toggle-btn');
    if (wordlistToggle) {
        wordlistToggle.addEventListener('click', () => {
            toggleWordlistInput();
        });
    }

    const customWordlistTextarea = document.getElementById('customWordlist');
    if (customWordlistTextarea) {
        customWordlistTextarea.addEventListener('input', () => {
            const status = document.getElementById('wordlist-status');
            const lines = customWordlistTextarea.value.trim().split('\n').filter(l => l.length > 0).length;
            if (lines > 0) {
                status.innerText = `Custom wordlist: ${lines} lines.`;
                status.style.color = 'var(--primary-color)';
            } else {
                status.innerText = "Default wordlist will be used.";
                status.style.color = 'inherit';
            }
        });
    }
}

window.toggleWordlistInput = function () {
    const container = document.getElementById('wordlist-input-container');
    container.classList.toggle('hidden');
};

// Global function to cancel tool (called by inline onclick)
window.cancelTool = function () {
    const inputBox = document.querySelector('.input-box');
    const msgInput = document.getElementById('msgInput');
    const badgeContainer = document.getElementById('tool-badge-container');

    currentTool = null;
    inputBox.classList.remove('tool-active');
    msgInput.placeholder = "Message AIVAST...";
    badgeContainer.innerHTML = '';

    document.getElementById('wordlist-toggle-btn')?.classList.add('hidden');
    const wordlistContainer = document.getElementById('wordlist-input-container');
    if (wordlistContainer) {
        wordlistContainer.classList.add('hidden');
        document.getElementById('customWordlist').value = '';
    }
};

// Helper to safely render Markdown content
function renderMessageContent(element, content) {
    if (!content) {
        element.innerHTML = '';
        return;
    }
    marked.setOptions({
        breaks: true,
        gfm: true
    });
    element.innerHTML = marked.parse(content);
    element.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
}

// Fungsi untuk menampilkan pesan di UI
// Fungsi untuk menampilkan pesan di UI
function displayMessage(message, type) {
    const chatContainer = document.getElementById('chatContainer');
    const welcomeScreen = document.getElementById('welcomeScreen');
    if (welcomeScreen) {
        welcomeScreen.style.display = 'none';
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

    if (message && (message.trim().startsWith('<i ') || message.trim().startsWith('<div '))) {
        bubble.innerHTML = message;
    } else {
        renderMessageContent(bubble, message);
    }

    messageWrapper.appendChild(avatar);
    messageWrapper.appendChild(bubble);
    chatContainer.appendChild(messageWrapper);

    const mainContent = document.querySelector('.chat-main-content');
    if (mainContent) {
        mainContent.scrollTop = mainContent.scrollHeight;
    } else {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    return bubble;
}

// Function to render detailed structured analysis
function renderDetailedAnalysis(container, data) {
    if (!data || typeof data !== 'object') {
        container.innerHTML = '<p>Error rendering analysis data.</p>';
        return;
    }

    const { metadata, analysis, issue, evidence, impact, recommendations, next_actions, summary } = data;

    let html = `
        <div class="analysis-section metadata">
            <div class="section-grid">
                <div class="grid-item"><strong>Confidence:</strong> <span class="badge confidence-${(metadata?.confidence || 'medium').toLowerCase()}">${metadata?.confidence || 'N/A'}</span></div>
                <div class="grid-item"><strong>Severity:</strong> <span class="badge severity-${(issue?.severity || 'info').toLowerCase()}">${issue?.severity || 'N/A'}</span></div>
            </div>
        </div>

        <div class="analysis-section main-analysis">
            <h4 class="section-title text-primary">[ANALYSIS]</h4>
            <div class="section-body">${typeof marked !== 'undefined' ? marked.parse(analysis || 'N/A') : (analysis || 'N/A')}</div>
        </div>

        <div class="analysis-section issue-box">
            <h4 class="section-title">[ISSUE / VULNERABILITY]</h4>
            <div class="issue-details">
                <p><strong>Class:</strong> ${issue?.type || 'N/A'}</p>
                <p><strong>OWASP:</strong> ${issue?.owasp || 'N/A'}</p>
                <p><strong>Location:</strong> <code>${issue?.endpoint || 'N/A'} ${issue?.parameter ? '(Param: ' + issue.parameter + ')' : ''}</code></p>
            </div>
        </div>

        <div class="analysis-section evidence">
            <h4 class="section-title">[EVIDENCE]</h4>
            <div class="evidence-box">
                <p><strong>Payload/Probe:</strong> <code>${evidence?.payload || 'N/A'}</code></p>
                <p><strong>Observation:</strong> ${evidence?.response_behavior || 'N/A'}</p>
            </div>
        </div>

        <div class="analysis-section impact">
            <h4 class="section-title text-danger">[IMPACT]</h4>
            <div class="impact-body">${impact || 'N/A'}</div>
        </div>

        <div class="analysis-section recs">
            <h4 class="section-title">[RECOMMENDATIONS]</h4>
            <ul>
                ${(recommendations || []).map(r => `<li>${r}</li>`).join('') || '<li>No specific recommendations provided.</li>'}
            </ul>
        </div>

        <div class="analysis-section next-actions">
            <h4 class="section-title">[NEXT_ACTIONS]</h4>
            <ul>
                ${(next_actions || []).map(a => `<li>${a}</li>`).join('') || '<li>No strategic next steps identified.</li>'}
            </ul>
        </div>

        <div class="analysis-summary-footer">
            <strong>Summary:</strong> ${summary || 'N/A'}
        </div>
    `;

    container.innerHTML = html;
}

// Fungsi untuk polling status scan
async function pollScanStatus(scanId, botMessageBubble) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/v1/scans/${scanId}/status`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                const analysis = data.analysis || {};

                const scanResultHTML = `
                    <div class="scan-result-container">
                        <div class="scan-summary-header">
                            <div class="status-badge completed">
                                <i class="fa-solid fa-shield-halved"></i> Analysis Report
                            </div>
                            <div class="target-info">${data.target || 'N/A'}</div>
                        </div>
                        
                        <div class="scan-rationale-box">
                            <div class="rationale-header">Strategy Rationale</div>
                            <div class="rationale-content">${data.rationale || 'N/A'}</div>
                        </div>

                        <div class="detailed-analysis-content" id="analysis-content-${scanId}">
                            <!-- Structured analysis will be injected here -->
                        </div>

                        <details class="command-transparency">
                            <summary>View technical command info</summary>
                            <div class="command-box">
                                <code>${(data.command || []).join(' ')}</code>
                            </div>
                        </details>
                    </div>`;

                botMessageBubble.innerHTML = scanResultHTML;
                const analysisContentDiv = botMessageBubble.querySelector(`#analysis-content-${scanId}`);
                if (analysisContentDiv) renderDetailedAnalysis(analysisContentDiv, analysis);

                const isGuest = typeof IS_GUEST !== 'undefined' && IS_GUEST === true;
                if (isGuest) {
                    let guestHistory = JSON.parse(sessionStorage.getItem('guestChatHistory') || '[]');
                    guestHistory.push({
                        role: 'assistant',
                        content: `[SYSTEM] Scan completed for target: ${data.target}. \nSummary: ${analysis.summary || 'Done'}`
                    });
                    sessionStorage.setItem('guestChatHistory', JSON.stringify(guestHistory));
                }
                fetchSessions();
            }
            else if (data.status === 'failed') {
                clearInterval(pollInterval);
                const error = data.error || data.details || "Scan gagal karena kesalahan server.";
                botMessageBubble.innerHTML = `<div class="error-message">Scan gagal: ${error}</div>`;
                fetchSessions();
            } else {
                // Background scan is still running
                // Only update if the indicator isn't there, to avoid resetting collapsible <details>
                if (!botMessageBubble.querySelector('.scanning-indicator')) {
                    botMessageBubble.innerHTML = `
                        <div class="scanning-indicator">
                            <i class='fa-solid fa-spinner fa-spin'></i> Scanning active on <strong>${data.target}</strong>
                            <div style="font-size: 0.8em; color: var(--text-secondary); margin-top: 5px;">
                                Tool: ${data.tool.toUpperCase()}
                            </div>
                            <details class="command-transparency" style="margin-top: 10px;">
                                <summary>View planned command</summary>
                                <div class="command-box">
                                    <code>${(data.command || []).join(' ')}</code>
                                </div>
                            </details>
                        </div>`;
                }
            }
        } catch (error) {
            clearInterval(pollInterval);
            console.error("Error polling scan status:", error);
            botMessageBubble.innerHTML = "Maaf, terjadi kesalahan saat memeriksa status scan.";
            fetchSessions();
        }
    }, 3000);
}

// Helper to extract and trigger autonomous scans
function parseAutonomousScan(text) {
    const scanMatch = text.match(/\[AUTO_SCAN: target=(.*?), mode=(.*?), tool=(.*?)\]/);
    if (scanMatch) {
        const target = scanMatch[1];
        const mode = scanMatch[2];
        const tool = scanMatch[3] === 'auto' ? null : scanMatch[3];
        const isDeep = mode === 'deep';

        console.log(`🤖 AI requested Autonomous Scan: ${target} (${mode})`);
        setTimeout(() => {
            initiateScan(target, tool, isDeep);
        }, 1500);

        return text.replace(/\[AUTO_SCAN:.*?\]/, "").trim();
    }
    return text;
}

// Core scan trigger function
async function initiateScan(target, tool = null, isDeep = false, customWordlist = null) {
    const botMessageBubble = displayMessage(`Initializing ${tool || 'AI planned'} scan... <i class='fa-solid fa-spinner fa-spin'></i>`, 'bot');
    try {
        const body = { target: target, use_ai: true, tool: tool, deep_scan: isDeep, custom_wordlist: customWordlist };
        if (currentSessionId) body.session_id = currentSessionId;

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
    } catch (error) {
        console.error("Error starting scan:", error);
        botMessageBubble.innerHTML = "Error during scan initialization.";
    }
}

// Fungsi mengirim pesan (bisa chat biasa atau perintah scan)
async function sendMessage() {
    const input = document.getElementById('msgInput');
    const message = input.value.trim();

    if (message !== "") {
        displayMessage(message, 'user');
        input.value = '';

        if (currentTool) {
            const wordlist = document.getElementById('customWordlist')?.value;
            initiateScan(message, currentTool, isDeepScan, wordlist);
            cancelTool(); // Close tool mode after starting
        } else {
            const botMessageBubble = displayMessage("<i class='fa-solid fa-spinner fa-spin'></i>", 'bot');
            const isGuest = typeof IS_GUEST !== 'undefined' && IS_GUEST === true;

            if (isGuest) {
                try {
                    let guestHistory = JSON.parse(sessionStorage.getItem('guestChatHistory') || '[]');
                    const response = await fetch('/api/v1/chat/guest', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: message, history: guestHistory })
                    });
                    if (response.status === 429) {
                        renderMessageContent(botMessageBubble, "⚠️ Limit reached. <a href='/' style='color:var(--primary-color)'>Login to continue</a>.");
                        return;
                    }
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const data = await response.json();
                    if (data.ai_response) {
                        const cleanResponse = parseAutonomousScan(data.ai_response);
                        renderMessageContent(botMessageBubble, cleanResponse);
                        guestHistory.push({ role: 'user', content: message });
                        guestHistory.push({ role: 'assistant', content: data.ai_response });
                        sessionStorage.setItem('guestChatHistory', JSON.stringify(guestHistory));
                    }
                } catch (error) {
                    console.error("Error in guest chat:", error);
                    botMessageBubble.innerHTML = "Failed to communicate with AI.";
                }
            } else {
                try {
                    const body = { message: message };
                    if (currentSessionId) body.session_id = currentSessionId;
                    const response = await fetch('/api/v1/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    if (response.status === 429) {
                        renderMessageContent(botMessageBubble, "⚠️ Limit reached. <a href='/' style='color:var(--primary-color)'>Login to continue</a>.");
                        return;
                    }
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    const data = await response.json();
                    if (data.session_id) {
                        currentSessionId = data.session_id;
                        fetchSessions();
                    }
                    if (data.ai_message) {
                        const cleanResponse = parseAutonomousScan(data.ai_message.content);
                        renderMessageContent(botMessageBubble, cleanResponse);
                    }
                } catch (error) {
                    console.error("Error creating chat:", error);
                    botMessageBubble.innerHTML = "Failed to communicate with AI.";
                }
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

    const isGuest = typeof IS_GUEST !== 'undefined' && IS_GUEST === true;
    if (isGuest) sessionStorage.removeItem('guestChatHistory');

    document.getElementById('chatContainer').innerHTML = `
        <div class="welcome-screen" id="welcomeScreen">
             <img src="/static/img/chatbot_icon.png" class="big-robot" alt="Robot AI">
             <p class="welcome-text">welcome back, ready to dive?</p>
        </div>
    `;

    document.querySelectorAll('.history-item').forEach(item => item.classList.remove('active'));
    if (window.innerWidth <= 768) toggleSidebar();
}

async function fetchSessions() {
    const isGuest = typeof IS_GUEST !== 'undefined' && IS_GUEST === true;
    if (isGuest) {
        const historyList = document.getElementById('historyList');
        if (historyList) historyList.innerHTML = '<li style="color:var(--subtitle-color); padding:10px; font-size:0.9em; text-align:center;">Guest mode: No saved history</li>';
        return;
    }

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
    event.stopPropagation();
    const newTitle = prompt("Enter new title:", currentTitle);
    if (newTitle && newTitle.trim() !== "") {
        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle.trim() })
            });
            if (response.ok) fetchSessions();
        } catch (error) {
            console.error("Error renaming session", error);
        }
    }
}

async function deleteSession(sessionId, event) {
    event.stopPropagation();
    if (confirm("Are you sure you want to delete this chat?")) {
        try {
            const response = await fetch(`/api/v1/sessions/${sessionId}`, { method: 'DELETE' });
            if (response.ok) {
                if (currentSessionId === sessionId) startNewChat();
                fetchSessions();
            }
        } catch (error) {
            console.error("Error deleting session", error);
        }
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    currentTool = null;
    document.querySelector('.input-box')?.classList.remove('tool-active');

    try {
        const response = await fetch(`/api/v1/sessions/${sessionId}`);
        const data = await response.json();
        const chatContainer = document.getElementById('chatContainer');
        chatContainer.innerHTML = '';
        fetchSessions();

        if (data.timeline) {
            data.timeline.forEach(item => {
                if (item.type === 'message') {
                    displayMessage(item.content, item.role === 'assistant' ? 'bot' : 'user');
                } else if (item.type === 'scan') {
                    let content = '';
                    if (item.status === 'completed') {
                        const analysis = item.analysis || {};
                        const summary = analysis.summary || 'No summary available.';
                        const summaryId = `history-scan-summary-${item.id}`;
                        content = `<div class="scan-result">
                            <div class="scan-header">
                                <i class="fa-solid fa-check-circle" style="color: var(--badge-text-completed)"></i>
                                <strong>Scan Completed</strong>
                            </div>
                            <div class="scan-details">
                                <p><strong>Target:</strong> ${item.target}</p>
                                <p><strong>Tool:</strong> ${item.tool}</p>
                                <p><strong>Rationale:</strong> ${item.rationale || 'N/A'}</p>
                                <details class="command-transparency">
                                    <summary>Show executed command</summary>
                                    <code>${(item.command || []).join(' ')}</code>
                                </details>
                                <p><strong>Risk:</strong> <span class="badge ${item.risk_level ? item.risk_level.toLowerCase() : 'unknown'}">${item.risk_level || 'Unknown'}</span></p>
                                <div class="summary" id="${summaryId}"></div>
                            </div>
                        </div>`;

                        const bubble = displayMessage(content, 'bot');
                        const summaryEl = bubble.querySelector(`#${summaryId}`);
                        if (summaryEl) renderMessageContent(summaryEl, summary);
                    } else {
                        content = `<div class="error-message">Scan Failed or Pending.</div>`;
                        displayMessage(content, 'bot');
                    }
                }
            });
        }
    } catch (e) {
        console.error("Failed to load session", e);
    }
    if (window.innerWidth <= 768) toggleSidebar();
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
// Tool Information Data
const TOOL_INFO = {
    nmap: {
        title: "Nmap Scanner",
        desc: "Network exploration and security auditing. Identifies open ports, running services, and OS versions on a target host."
    },
    nikto: {
        title: "Nikto Web Vault",
        desc: "Comprehensive web server scanner. Finds dangerous files, outdated software, and misconfigurations on http/https targets."
    },
    gobuster: {
        title: "Gobuster Brute",
        desc: "High-speed directory and file brute-forcer. Discovers hidden paths, sensitive files, and admin panels using wordlists."
    },
    sqlmap: {
        title: "SQLMap Expert",
        desc: "Automatic SQL injection detector and exploiter. Tests parameters for database vulnerabilities and data extraction potential."
    },
    deepscan: {
        title: "⚡ Deep Scan Engine",
        desc: "Advanced Multi-Phase Intelligence. Enforces the Full Cybersecurity Kill Chain (Nmap -A, Gobuster brute-force, and complex VA tools)."
    }
};

const closeDeepOverlay = () => {
    const overlay = document.getElementById('deep-scan-overlay');
    if (overlay) overlay.classList.remove('active');
};

const setupToolInfo = () => {
    const popover = document.getElementById('info-popover');
    const content = document.getElementById('info-content');
    const title = document.getElementById('info-title');
    const closeBtn = popover.querySelector('.info-close');
    const deepOverlay = document.getElementById('deep-scan-overlay');

    const showInfo = (type, x, y) => {
        const info = TOOL_INFO[type];
        const toolMenu = document.getElementById('tool-menu');
        if (!info || !toolMenu) return;

        // If Deep Scan, show the centered overlay instead of popover
        if (type === 'deepscan' && deepOverlay) {
            deepOverlay.classList.add('active');
            toolMenu.classList.add('hidden');
            return;
        }

        title.innerText = info.title;
        content.innerText = info.desc;

        // Get tool menu dimensions
        const menuRect = toolMenu.getBoundingClientRect();
        const popoverWidth = 300;
        const screenWidth = window.innerWidth;

        // Position to the right of the tool menu by default
        let leftPos = menuRect.right + 15;

        // If not enough space on right, show on left of menu
        if (leftPos + popoverWidth > screenWidth) {
            leftPos = menuRect.left - popoverWidth - 15;
        }

        popover.style.left = `${leftPos}px`;
        popover.style.top = `${menuRect.top}px`;

        popover.classList.remove('hidden');
    };

    document.querySelectorAll('.info-icon').forEach(icon => {
        icon.addEventListener('click', (e) => {
            e.stopPropagation();
            const type = icon.getAttribute('data-info');
            const rect = icon.getBoundingClientRect();
            showInfo(type, rect.left, rect.top);
        });
    });

    closeBtn.addEventListener('click', () => {
        popover.classList.add('hidden');
    });

    document.addEventListener('click', (e) => {
        if (!popover.contains(e.target) && !e.target.classList.contains('info-icon')) {
            popover.classList.add('hidden');
        }
    });
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('chatContainer')) {
        fetchSessions();
        setupToolMenu();
        setupToolInfo(); // Initialize info tooltips
        const chatInput = document.getElementById('msgInput');
        const sendButton = document.getElementById('sendBtn');
        if (chatInput) chatInput.addEventListener('keydown', handleEnter);
        if (sendButton) sendButton.addEventListener('click', sendMessage);
    }
});
