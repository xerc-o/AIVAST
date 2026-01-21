# AIVAST - AI-Powered Assessment and Scanning Tool

AIVAST is a security scanning tool that integrates traditional security tools like `nmap` and `nikto` with the power of LLMs (Groq) for automated results analysis.

## 🚀 Features

- 🤖 **AI-Powered Analysis**: Uses Groq LLM to automatically analyze scan results.
- 🔍 **Tool Integration**: Built-in support for `nmap` and `nikto`.
- 📊 **History Tracking**: Saves all scan results and analyses to a SQLite database.
- 🛡️ **Security Controls**: Argument blacklisting, whitelist-only tool execution, and timeout protection.
- 📝 **RESTful API**: Clean API endpoints for integration with other tools.
- 🔎 **Advanced Filtering**: Filter scan history by tool type, risk level, and pagination.

## 📋 Requirements

- Python 3.8+
- `nmap` (installed on system)
- `nikto` (installed on system)
- Groq API Key

## 🔧 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AIVAST_CLEAN
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Recommended: install in editable mode to handle imports correctly
   pip install -e .
   ```

4. **Setup environment variables:**
   Copy `.env.example` to `.env` and configure your keys:
   ```bash
   cp .env.example .env
   # Edit .env and add your GROQ_API_KEY
   ```

## 🎯 Usage

### Start the Application
Since the source code is in the `src` directory, you can run the app using:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python src/app.py
```
Or if you installed it in editable mode:
```bash
flask run
```
The server will run at `http://127.0.0.1:5000`.

### API Endpoints

#### Health Check
`GET /`
```bash
curl http://127.0.0.1:5000/
```

#### Start a Scan
`POST /scan`
```bash
curl -X POST http://127.0.0.1:5000/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "https://example.com"}'
```

#### List Scans
`GET /scans`
```bash
curl http://127.0.0.1:5000/scans
```
*Optional parameters: `tool`, `risk`, `page`, `per_page`*

#### Get Scan Detail
`GET /scans/<id>`

#### Delete Scan
`DELETE /scans/<id>`

## 🏗️ Project Structure

- `src/`: Main source code
  - `ai/`: LLM integration and parsing logic
  - `routes/`: Flask API endpoints
  - `models/`: Database models
- `templates/`: HTML templates (if applicable)
- `static/`: Static assets
- `tests/`: Project test suite

## 🛡️ Security
AIVAST implements several security measures:
- **Argument Blacklisting**: Prevents execution of dangerous arguments like `--script` in `nmap`.
- **Timeout Protection**: `nmap` (180s) and `nikto` (300s) have hard execution limits.
- **Output Limit**: Results are truncated at 20,000 characters to prevent overflow.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License.
