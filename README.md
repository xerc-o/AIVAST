<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>

<body>

<header>
  <h1>AIVAST</h1>
  <p><strong>AI Powered Assessment and Scanning Tool</strong></p>
</header>

<main>

<section>
  <p>
    <strong>AIVAST</strong> adalah tool scanning keamanan berbasis AI yang
    menggunakan <strong>Groq LLM</strong> untuk menganalisis hasil scanning
    dari <strong>nmap</strong> dan <strong>nikto</strong> secara otomatis.
  </p>
</section>

<section>
  <h2>🚀 Features</h2>
  <ul>
    <li>🤖 <strong>AI-Powered Analysis</strong> — Analisis hasil scan dengan Groq LLM</li>
    <li>🔍 <strong>Multiple Tools</strong> — Mendukung nmap & nikto</li>
    <li>📊 <strong>History Tracking</strong> — Menyimpan riwayat scan ke database</li>
    <li>🛡️ <strong>Security Controls</strong> — Whitelist tools, blacklist arguments, timeout</li>
    <li>📝 <strong>RESTful API</strong> — Endpoint API yang clean</li>
    <li>🔎 <strong>Advanced Filtering</strong> — Filter tool, risk level, pagination</li>
  </ul>
</section>

<section>
  <h2>📋 Requirements</h2>
  <ul>
    <li>Python 3.8+</li>
    <li>nmap (installed on system)</li>
    <li>nikto (installed on system)</li>
    <li>Groq API Key</li>
  </ul>
</section>

<section>
  <h2>🔧 Installation</h2>

  <h3>1. Clone Repository</h3>
  <pre><code>git clone &lt;repository-url&gt;
cd AIVAST</code></pre>

  <h3>2. Create Virtual Environment</h3>
  <pre><code>python3 -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows</code></pre>

  <h3>3. Install Dependencies</h3>
  <pre><code>pip install -r requirements.txt</code></pre>

  <h3>4. Setup Environment Variables</h3>
  <pre><code>cp .env.example .env</code></pre>

  <p>Edit file <code>.env</code>:</p>
  <pre><code>FLASK_ENV=development
DATABASE_URL=sqlite:///AIVAST.db
GROQ_API_KEY=your-groq-api-key</code></pre>
</section>

<section>
  <h2>🎯 Usage</h2>

  <h3>Run Flask App</h3>
  <pre><code>python src/app.py</code></pre>
  <p>Server berjalan di <code>http://127.0.0.1:5000</code></p>

  <h3>Test dengan cURL</h3>

  <h4>Health Check</h4>
  <pre><code>curl http://127.0.0.1:5000/</code></pre>

  <h4>Run Scan</h4>
  <pre><code>curl -X POST http://127.0.0.1:5000/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com"}'</code></pre>

  <h4>List All Scans</h4>
  <pre><code>curl http://127.0.0.1:5000/scans</code></pre>

  <h4>Filter Scans</h4>
  <pre><code>
# By tool
curl http://127.0.0.1:5000/scans?tool=nikto
# By risk level
curl http://127.0.0.1:5000/scans?risk=medium
# Pagination
curl http://127.0.0.1:5000/scans?page=1&per_page=10</code></pre>
</section>

<section>
  <h3>📝 API Endpoints</h4>

  <h4>GET /</h4>
  <p>Health check endpoint.</p>

  <h4>POST /scan</h4>
  <p>Menjalankan scanning keamanan pada target.</p>

  <h4>GET /scans</h4>
  <p>Menampilkan semua scan dengan pagination & filtering.</p>

  <h4>GET /scans/&lt;id&gt;</h4>
  <p>Detail scan tertentu.</p>

  <h4>DELETE /scans/&lt;id&gt;</h4>
  <p>Menghapus scan.</p>
</section>

</body>
</html>
