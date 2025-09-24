import os
import time
import requests
import docx
import fitz  # PyMuPDF
from dotenv import load_dotenv
import streamlit as st
from deepgram import DeepgramClient, PrerecordedOptions

# ---------------- Load API Keys ----------------
load_dotenv()
HF_API_KEY = os.getenv("HUGGINGFACEHUB_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Use faster Hugging Face model
HF_MODEL = "sshleifer/distilbart-cnn-12-6"

# ---------------- Summarizers ----------------
def summarize_with_hf(text, length="medium", retries=3, delay=2):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    if len(text.split()) < 5:
        return None, None

    if length == "small":
        min_len, max_len = 20, 80
    elif length == "medium":
        min_len, max_len = 50, 150
    else:
        min_len, max_len = 100, 250

    for attempt in range(retries):
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{HF_MODEL}",
                headers=headers,
                json={"inputs": text, "parameters": {"min_length": min_len, "max_length": max_len}}
            )
            if response.status_code == 200:
                return response.json()[0]['summary_text'], "Hugging Face"
            else:
                time.sleep(delay)
        except Exception:
            time.sleep(delay)

    return None, None

def summarize_with_gemini(text, length="medium"):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"Summarize this text in a {length} length:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text, "Gemini"
    except Exception:
        return None, None

# ---------------- Summarize text ----------------
def summarize_text(text, model_choice, length):
    if model_choice == "Hugging Face":
        summary, used_model = summarize_with_hf(text, length)
        if summary is None:
            return "❌ Hugging Face summarization failed. Check API key or input length.", "Hugging Face"

    elif model_choice == "Gemini":
        summary, used_model = summarize_with_gemini(text, length)
        if summary is None:
            return "❌ Gemini summarization failed. Check API key or input.", "Gemini"

    else:  # Auto fallback
        summary, used_model = summarize_with_hf(text, length)
        if summary is None:
            summary, used_model = summarize_with_gemini(text, length)
        if summary is None:
            return "❌ Both Hugging Face and Gemini summarization failed.", None

    return summary, used_model

# ---------------- Deepgram Audio ----------------
def transcribe_audio(file_path):
    try:
        dg = DeepgramClient(DEEPGRAM_API_KEY)
        with open(file_path, "rb") as audio_file:
            payload = {"buffer": audio_file, "mimetype": "audio/*"}
            options = PrerecordedOptions(model="nova-2", smart_format=True)
            response = dg.listen.prerecorded.v("1").transcribe_file(payload, options)
        return response["results"]["channels"][0]["alternatives"][0]["transcript"]
    except Exception as e:
        return f"Deepgram error: {str(e)}"

# ---------------- File Readers ----------------
def read_pdf(file) -> str:
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text("text")
    return text

def read_docx(file) -> str:
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def read_txt(file) -> str:
    return file.read().decode("utf-8")

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="AI Summariser Chatbot", layout="wide")
st.title("📝 AI Summariser Chatbot")

# Sidebar Settings
st.sidebar.header("⚙️ Settings")
input_type = st.sidebar.radio("Choose Input Type", ["Text", "Audio", "Document"])
model_choice = st.sidebar.radio("Choose Model", ["Auto", "Hugging Face", "Gemini"])
length = st.sidebar.radio("Summary Length", ["small", "medium", "large"])

# Session state for history
if "history" not in st.session_state:
    st.session_state.history = []

# ---- TEXT ----
if input_type == "Text":
    text_input = st.text_area("✍️ Enter text to summarize", height=200)
    if st.button("Summarize Text"):
        if text_input.strip():
            summary, used_model = summarize_text(text_input, model_choice, length)
            st.subheader("✅ Summary")
            st.write(summary)
            if used_model:
                st.success(f"🔍 Model Used: {used_model}")
            st.session_state.history.append(
                {"input": text_input[:100] + "...", "summary": summary, "model": used_model}
            )
        else:
            st.warning("⚠️ Please enter some text.")

# ---- AUDIO ----
elif input_type == "Audio":
    uploaded_audio = st.file_uploader("🎤 Upload audio file", type=["mp3", "wav", "m4a", "ogg", "flac"])
    if uploaded_audio and st.button("Transcribe & Summarize"):
        with open("temp_audio", "wb") as f:
            f.write(uploaded_audio.read())
        transcript = transcribe_audio("temp_audio")
        st.subheader("Transcript")
        st.write(transcript)
        if transcript and not transcript.startswith("Deepgram error"):
            summary, used_model = summarize_text(transcript, model_choice, length)
            st.subheader("✅ Summary")
            st.write(summary)
            if used_model:
                st.success(f"🔍 Model Used: {used_model}")
            st.session_state.history.append(
                {"input": transcript[:100] + "...", "summary": summary, "model": used_model}
            )

# ---- DOCUMENT ----
elif input_type == "Document":
    uploaded_doc = st.file_uploader("📄 Upload a document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    if uploaded_doc and st.button("Summarize Document"):
        if uploaded_doc.type == "application/pdf":
            extracted_text = read_pdf(uploaded_doc)
        elif uploaded_doc.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            extracted_text = read_docx(uploaded_doc)
        elif uploaded_doc.type == "text/plain":
            extracted_text = read_txt(uploaded_doc)
        else:
            extracted_text = ""

        if extracted_text.strip():
            st.subheader("Extracted Text")
            st.write(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)
            summary, used_model = summarize_text(extracted_text, model_choice, length)
            st.subheader("✅ Summary")
            st.write(summary)
            if used_model:
                st.success(f"🔍 Model Used: {used_model}")
            st.session_state.history.append(
                {"input": extracted_text[:100] + "...", "summary": summary, "model": used_model}
            )
        else:
            st.warning("⚠️ Could not extract text from the document.")

# ---- History in Sidebar ----
st.sidebar.markdown("---")
st.sidebar.subheader("🕑 Summary History")
if st.session_state.history:
    for i, item in enumerate(reversed(st.session_state.history), 1):
        st.sidebar.write(f"**{i}. Input:** {item['input']}")
        st.sidebar.write(f"**Model:** {item['model']}")
        st.sidebar.write(f"**Summary:** {item['summary']}")
        st.sidebar.markdown("---")
else:
    st.sidebar.info("No summaries yet. Start by adding some text, audio, or a document.")
