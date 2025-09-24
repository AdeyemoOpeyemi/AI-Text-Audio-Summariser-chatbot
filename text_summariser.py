import os
import fitz  # PyMuPDF
import docx
from dotenv import load_dotenv
import google.generativeai as genai
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

# 🔑 Load API Keys from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# ✅ Initialize Gemini Client
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        print("✅ Gemini key works!")
    except Exception as e:
        print(f"❌ Gemini key failed: {e}")
else:
    print("❌ Gemini API key not configured. Please add it to your .env file.")

# ✅ Initialize Deepgram Client
dg_client = None
if DEEPGRAM_API_KEY:
    try:
        dg_client = DeepgramClient(DEEPGRAM_API_KEY)
        print("✅ Deepgram key works!")
    except Exception as e:
        print(f"❌ Deepgram key failed: {e}")
else:
    print("❌ Deepgram API key not configured. Please add it to your .env file.")

# --- Document Readers ---
def read_pdf(file_path):
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        return f"❌ Error reading PDF: {e}"

def read_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"❌ Error reading DOCX: {e}"

def read_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"❌ Error reading TXT: {e}"

# --- Core Summarization Function ---
def summarize_text(text, length="medium"):
    if not gemini_model:
        return "❌ Gemini API not configured. Cannot summarize."
    
    # Check if the text is long enough for a meaningful summary.
    if not text.strip() or len(text.split()) < 20:
        return "⚠️ Text is too short to summarize effectively."

    try:
        prompt = f"Summarize this text in a {length} detail. The summary should be concise and capture the key information."
        response = gemini_model.generate_content(prompt + "\n\nText:\n" + text)
        return f"[Gemini] {response.text}"
    except Exception as e:
        return f"[Gemini ERROR] {e}"

# --- Audio Transcription + Summarization ---
def transcribe_and_summarize(file_path, length):
    if not dg_client:
        return "❌ Deepgram API not configured. Cannot transcribe audio."
    if not os.path.exists(file_path):
        return "❌ Audio file not found at the specified path."

    try:
        with open(file_path, "rb") as audio_file:
            source: FileSource = {"buffer": audio_file, "mimetype": "audio/*"}
            options = PrerecordedOptions(model="nova-2")
            response = dg_client.listen.prerecorded.v("1").transcribe_file(source, options)
            transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
            
        if not transcript.strip():
            return "⚠️ No speech detected in audio."

        return summarize_text(transcript, length)
    except Exception as e:
        return f"Deepgram error: {e}"

# --- Document Reading + Summarization ---
def read_and_summarize_doc(file_path, length):
    if not os.path.exists(file_path):
        return "❌ Document file not found at the specified path."
    
    file_ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    if file_ext == ".pdf":
        text = read_pdf(file_path)
    elif file_ext == ".docx":
        text = read_docx(file_path)
    elif file_ext == ".txt":
        text = read_txt(file_path)
    else:
        return "❌ Unsupported document type. Please use PDF, DOCX, or TXT."
    
    # Check for errors from the reading functions
    if "❌ Error" in text:
        return text
    if not text.strip():
        return "⚠️ Could not extract text from the document."
        
    return summarize_text(text, length)

# --- MAIN LOOP ---
def main():
    print("\n🚀 AI Summarizer Ready! (Text + Audio + Document)\n")
    while True:
        choice = input("Enter choice: 1 (Text) / 2 (Audio) / 3 (Document) / q (Quit): ").strip()
        
        if choice.lower() == "q":
            print("👋 Exiting summarizer. Goodbye!")
            break
            
        if choice == "1":
            text = input("\n✍️ Enter text to summarize:\n")
            length = input("Choose summary length (Small / Medium / Large): ").lower()
            summary = summarize_text(text, length)
            print("\n--- Summary ---")
            print(summary)
            
        elif choice == "2":
            file_path = input("\n🎵 Enter full path to your audio file (mp3, wav, m4a, etc.): ")
            length = input("Choose summary length (Small / Medium / Large): ").lower()
            summary = transcribe_and_summarize(file_path, length)
            print("\n--- Audio Summary ---")
            print(summary)

        elif choice == "3":
            file_path = input("\n📄 Enter full path to your document (PDF, DOCX, or TXT): ")
            length = input("Choose summary length (Small / Medium / Large): ").lower()
            summary = read_and_summarize_doc(file_path, length)
            print("\n--- Document Summary ---")
            print(summary)
        else:
            print("❌ Invalid choice, try again.")

if __name__ == "__main__":
    main()