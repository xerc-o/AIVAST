<h2>
  AIVAST
</h2>
<h5>
  AI Powered Assesment and Scanning Tool
</h5>


<body>
AIVAST adalah tool scanning keamanan berbasis AI yang menggunakan Groq LLM untuk menganalisis hasil scanning dari nmap dan nikto secara otomatis.

## 🚀 Features

- 🤖 **AI-Powered Analysis**: Menggunakan Groq LLM untuk analisis hasil scan
- 🔍 **Multiple Tools**: Support untuk nmap dan nikto
- 📊 **History Tracking**: Menyimpan semua scan history ke database
- 🛡️ **Security Controls**: Whitelist tools, blacklist arguments, timeout protection
- 📝 **RESTful API**: Clean API endpoints untuk integrasi
- 🔎 **Advanced Filtering**: Filter by tool, risk level, pagination

## 📋 Requirements

- Python 3.8+
- nmap (installed on system)
- nikto (installed on system)
- Groq API Key

## 🔧 Installation

1. Clone repository:sh
git clone <repository-url>
cd AIVAST2. Create virtual environment:ash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows3. Install dependencies:
pip install -r requirements.txt4. Setup environment variables:
cp .env.example .env
# Edit .env dan masukkan GROQ_API_KEY5. Initialize database (otomatis saat first run)

## 🎯 Usage

### Run Flask App
python src/app.pyServer akan berjalan di `http://127.0.0.1:5000`

### Test dengan Python Script
python test.py
### Test dengan cURL

#### Health Check
curl http://127.0.0.1:5000/#### Run Scan
curl -X POST http://127.0.0.1:5000/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com"}'#### List All Scans
curl http://127.0.0.1:5000/scans#### Filter Scans
# By tool
curl http://127.0.0.1:5000/scans?tool=nikto

# By risk level
curl http://127.0.0.1:5000/scans?risk=medium

# Pagination
curl http://127.0.0.1:5000/scans?page=1&per_page=10
#### Get Scan Detail
curl http://127.0.0.1:5000/scans/1#### Delete Scan
curl -X DELETE http://127.0.0.1:5000/scans/1## 📡 API Endpoints

### `GET /`
Health check endpoint.

**Response:**
{
  "status": "AIVAST running"
}### `POST /scan`
Run security scan pada target.

**Request:**son
{
  "target": "https://example.com"
}**Response:**
{
  "target": "https://example.com",
  "tool": "nikto",
  "command": "nikto -h https://example.com",
  "execution": {
    "ok": true,
    "tool": "nikto",
    "returncode": 1,
    "stdout": "...",
    "stderr": "..."
  },
  "analysis": {
    "risk": "medium",
    "summary": "...",
    "issues": [...],
    "recommendations": [...]
  }
}### `GET /scans`
List semua scan history dengan pagination dan filtering.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20)
- `tool` (string): Filter by tool (nmap/nikto)
- `risk` (string): Filter by risk level (info/low/medium/high)

**Response:**
{
  "scans": [...],
  "total": 10,
  "page": 1,
  "per_page": 20,
  "pages": 1
}### `GET /scans/<id>`
Get detail scan tertentu.

### `DELETE /scans/<id>`
Delete scan tertentu.

## 🏗️ Project Structure

</body>
