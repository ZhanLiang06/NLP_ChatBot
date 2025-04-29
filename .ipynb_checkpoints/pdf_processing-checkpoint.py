import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.embeddings.ollama import OllamaEmbeddings

# Configuration
UPLOAD_FOLDER = "uploads"
PERSIST_DIR = "data"
EMBEDDING_MODEL = "nomic-embed-text"

def process_pdf(file_path):
    """Loads a PDF, splits text, and stores vector embeddings."""
    print(f"📄 Processing PDF: {file_path}")

    # Load PDF
    loader = PyPDFLoader(file_path)
    data = loader.load()

    # Text Splitting
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
    all_splits = text_splitter.split_documents(data)

    # Store as Vector Embeddings
    vectorstore = Chroma.from_documents(
        documents=all_splits,
        collection_name="rag_chroma",
        embedding=OllamaEmbeddings(model=EMBEDDING_MODEL),
        persist_directory=PERSIST_DIR
    )
    
    print("✅ PDF Processed & Vector Store Updated")
    return vectorstore

# Example Usage
if __name__ == "__main__":
    test_pdf = os.path.join(UPLOAD_FOLDER, "ml.pdf")  # Change this to your file
    process_pdf(test_pdf)
