import os
import streamlit as st
from pdf_processing import process_pdf
from chatbot import ask_question

# Streamlit UI Configuration
st.set_page_config(page_title="📄 AI PDF Chatbot", layout="wide")
st.title("📄 AI-Powered PDF Chatbot")

# Sidebar - PDF Upload
st.sidebar.header("📤 Upload a PDF")
uploaded_file = st.sidebar.file_uploader("Upload a PDF file", type=["pdf"])

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if uploaded_file:
    FILEPATH = os.path.join("uploads", uploaded_file.name)

    with open(FILEPATH, "wb") as f:
        f.write(uploaded_file.read())

    st.sidebar.success(f"✅ Uploaded: {uploaded_file.name}")

    # Process PDF & store embeddings
    st.sidebar.info("🔄 Processing PDF...")
    process_pdf(FILEPATH)
    st.sidebar.success("✅ PDF Ready for Chat!")

# User Query Input
query = st.text_input("💬 Ask a question about the PDF")

if st.button("🔍 Get Answer"):
    if query:
        response = ask_question(query)
        st.session_state.chat_history.append(("🧑 You", query))
        st.session_state.chat_history.append(("🤖 AI", response))

        # Display chat history
        st.subheader("📜 Chat History")
        for role, message in st.session_state.chat_history:
            st.markdown(f"**{role}:** {message}")
    else:
        st.warning("⚠️ Please enter a question.")
