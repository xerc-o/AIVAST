from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def ai_chat_response(user_input, session_history=None):
    """
    Generates a response from the AI using a cybersecurity persona.
    """
    system_prompt = """You are AIVAST, an elite cybersecurity AI assistant. 
    Your goal is to assist users with penetration testing, vulnerability analysis, and security auditing.
    
    GUIDELINES:
    1. **Format**: Use Markdown purely. Use headings, bullet points, and bold text for readability.
    2. **Code**: ALWAYS use Markdown code blocks (```language ... ```) for any commands, scripts, or output.
    3. **Tone**: Professional, concise, technical, and slightly "hacker-ish" but clear.
    4. **Safety**: Adhere strictly to ethical hacking guidelines. Only assist with authorized targets.
    
    Do not print raw unformatted text blocks. Structure your response to be easily scannable.
    """
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Ideally, append session_history here
    # for msg in session_history:
    #     messages.append({"role": msg['role'], "content": msg['content']})
        
    messages.append({"role": "user", "content": user_input})
    
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"
