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
    bubble.innerHTML = message; // Use innerHTML to allow for formatted messages

    messageWrapper.appendChild(avatar);
    messageWrapper.appendChild(bubble);
    chatContainer.appendChild(messageWrapper);

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return bubble; // Return the bubble element for later updates
}

// Fungsi untuk polling status scan dari backend
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
                botMessageBubble.innerHTML = summary; // Update existing bubble
                fetchHistory(); // Refresh history once completed
            } else if (data.status === 'failed') {
                clearInterval(pollInterval);
                const error = data.error || "Scan gagal karena kesalahan server.";
                botMessageBubble.innerHTML = `Scan gagal: ${error}`; // Update existing bubble
                fetchHistory();
            } else {
                // Still running, update loading animation if desired
                botMessageBubble.innerHTML = "Scanning... <i class='fa-solid fa-spinner fa-spin'></i>";
            }
        } catch (error) {
            clearInterval(pollInterval);
            console.error("Error polling scan status:", error);
            botMessageBubble.innerHTML = "Maaf, terjadi kesalahan saat memeriksa status scan.";
            fetchHistory();
        }
    }, 3000); // Poll every 3 seconds
}

// New function to handle sending messages
async function sendMessage() {
    const input = document.getElementById('msgInput');
    const message = input.value.trim();

    if (message !== "") {
        displayMessage(message, 'user');
        input.value = '';

        const botMessageBubble = displayMessage("Memulai scan... <i class='fa-solid fa-spinner fa-spin'></i>", 'bot'); // Display initial scanning message

        try {
            const response = await fetch('/api/v1/scans', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target: message, use_ai: true })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            if (data.scan_id) {
                pollScanStatus(data.scan_id, botMessageBubble); // Start polling
            } else {
                botMessageBubble.innerHTML = "Gagal memulai scan: ID scan tidak ditemukan.";
            }

        } catch (error) {
            console.error("Error starting scan:", error);
            botMessageBubble.innerHTML = "Maaf, terjadi kesalahan saat memulai scan.";
        }
    }
}

// Fungsi untuk mengirim pesan ke backend saat menekan Enter
async function handleEnter(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
}

// Fungsi untuk mengambil dan menampilkan riwayat chat
async function fetchHistory() {
    try {
        const response = await fetch('/api/v1/scans');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        const historyList = document.querySelector('.history-list');
        historyList.innerHTML = ''; // Kosongkan list

        if (data.scans && data.scans.length > 0) {
            data.scans.forEach(scan => {
                const item = document.createElement('li');
                item.className = 'history-item';
                item.dataset.scanId = scan.id; // Store scan ID

                // Create container for text content
                const contentDiv = document.createElement('div');
                contentDiv.className = 'history-info';

                const titleSpan = document.createElement('span');
                titleSpan.className = 'history-title';
                titleSpan.textContent = scan.target;

                const badgeSpan = document.createElement('span');
                badgeSpan.className = `badge ${scan.status.toLowerCase()}`;
                badgeSpan.textContent = scan.status;

                contentDiv.appendChild(titleSpan);
                contentDiv.appendChild(badgeSpan);

                item.appendChild(contentDiv);

                // Add click event listener
                item.addEventListener('click', () => loadHistoryScan(scan.id, scan.target));

                historyList.appendChild(item);
            });
        } else {
            const item = document.createElement('li');
            item.className = 'history-item';
            item.textContent = "Tidak ada riwayat scan.";
            historyList.appendChild(item);
        }


    } catch (error) {
        console.error("Error fetching history:", error);
    }
}

// Fungsi untuk memuat dan menampilkan scan dari history
async function loadHistoryScan(scanId, target) {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.innerHTML = ''; // Clear the chat window

    displayMessage(target, 'user');

    const botMessageBubble = displayMessage("Loading history... <i class='fa-solid fa-spinner fa-spin'></i>", 'bot');

    try {
        const response = await fetch(`/api/v1/scans/${scanId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        const summary = data.analysis?.summary || "Analisis selesai. Tidak ada ringkasan yang tersedia.";
        botMessageBubble.innerHTML = summary;
    } catch (error) {
        console.error("Error loading history scan:", error);
        botMessageBubble.innerHTML = "Gagal memuat riwayat scan.";
    }
}


// Fungsi untuk toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const chatMainContent = document.querySelector('.chat-main-content');
    const inputArea = document.querySelector('.input-area');

    sidebar.classList.toggle('active');
    chatMainContent.classList.toggle('sidebar-open');
    inputArea.classList.toggle('sidebar-open');
}

// Fungsi untuk logout
function logout() {
    window.location.href = '/logout';
}


// Event listener untuk dieksekusi setelah DOM dimuat
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('msgInput');
    const sendButton = document.getElementById('sendBtn'); // Get the send button

    if (chatInput) {
        chatInput.addEventListener('keydown', handleEnter);
    }
    if (sendButton) { // Add event listener for the send button
        sendButton.addEventListener('click', sendMessage);
    }

    // Hanya jalankan fetchHistory jika kita berada di halaman chat
    if (document.querySelector('.chat-container')) {
        fetchHistory();

        // Hapus dummy messages
        const dummyUserMsg = document.getElementById('dummyUserMsg');
        if (dummyUserMsg) dummyUserMsg.remove();

        const dummyBotMsg = document.getElementById('dummyBotMsg');
        if (dummyBotMsg) dummyBotMsg.remove();
    }
});
