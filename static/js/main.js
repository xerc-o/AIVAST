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
    icon.classList.add('fa-regular', type === 'user' ? 'fa-user' : 'fa-solid fa-robot');
    avatar.appendChild(icon);

    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    bubble.textContent = message;

    messageWrapper.appendChild(avatar);
    messageWrapper.appendChild(bubble);
    chatContainer.appendChild(messageWrapper);

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Fungsi untuk mengirim pesan ke backend saat menekan Enter
async function handleEnter(e) {
    if (e.key === 'Enter') {
        const input = document.getElementById('msgInput');
        const message = input.value.trim();

        if (message !== "") {
            displayMessage(message, 'user');
            input.value = '';

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
                const summary = data.analysis?.summary || "Tidak ada ringkasan yang tersedia.";
                displayMessage(summary, 'bot');
                
                // Refresh history
                fetchHistory();

            } catch (error) {
                console.error("Error sending message:", error);
                displayMessage("Maaf, terjadi kesalahan saat menghubungi server.", 'bot');
            }
        }
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

        data.scans.forEach(scan => {
            const item = document.createElement('li');
            item.className = 'history-item';
            
            const icon = document.createElement('i');
            icon.className = 'fa-regular fa-message';
            
            item.appendChild(icon);
            item.append(` ${scan.target}`); // Tambahkan target ke item
            historyList.appendChild(item);
        });

    } catch (error) {
        console.error("Error fetching history:", error);
    }
}

// Fungsi untuk toggle sidebar
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
}

// Fungsi untuk logout
function logout() {
    window.location.href = '/logout';
}


// Event listener untuk dieksekusi setelah DOM dimuat
document.addEventListener('DOMContentLoaded', () => {
    // Hanya jalankan fetchHistory jika kita berada di halaman chat
    if (document.querySelector('.chat-container')) {
        fetchHistory();
    }
});
