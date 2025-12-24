from .nmap import NmapAnalyzer
from .nikto import NiktoAnalyzer
from .llm.groq import call_groq  # Changed from .llm import call_llm
import json

ANALYZERS = {
    "nmap": NmapAnalyzer(),
    "nikto": NiktoAnalyzer(),
}

# Jika masih ada fungsi yang menggunakan call_llm, ganti ke call_groq
# Tapi karena analyze_output sudah dihapus, file ini mungkin tidak digunakan lagi