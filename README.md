#  AI Summariser Chatbot

An **AI-powered summariser** built with **Streamlit**, **Hugging Face**, **Gemini**, and **Deepgram**.  
It can summarise **text, audio, and documents (PDF, DOCX, TXT)** into concise outputs using state-of-the-art models.

---

##  Features
-  Summarise **raw text input**
-  Transcribe & summarise **audio files** (mp3, wav, etc.)
-  Summarise **documents** (PDF, DOCX, TXT)
-  Choose models:
  - Hugging Face (`distilbart-cnn-12-6`)
  - Google Gemini
  - Auto fallback
-  History tracking in the sidebar

---

##  Files
- `app.py` → Main Streamlit app
- `requirements.txt` → Python dependencies
- `.env.example` → Example environment variables
- `.gitignore` → Ignore secrets & junk files
- `README.md` → Documentation

---

## ⚙️ Prerequisites
- Python 3.9+
- API Keys:
  - Hugging Face Hub → [Get key](https://huggingface.co/settings/tokens)
  - Google Gemini → [Get key](https://aistudio.google.com/app/apikey)
  - Deepgram → [Get key](https://console.deepgram.com/)

---

## 🚀 Setup Guide

1. **Clone repo**
   ```bash
   git clone https://github.com/your-AdeyemoOpeyemi/ai-summariser-chatbot.git
   cd ai-summariser-chatbot

