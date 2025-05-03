import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.embeddings.ollama import OllamaEmbeddings

# Configuration
UPLOAD_FOLDER = "uploads"
PERSIST_DIR = "vector_data"
EMBEDDING_MODEL = "nomic-embed-text"

class DocumentProcessor():
    def __init__(self,conver_id):
        self.conver_id = conver_id
        self.conver_collection_name = f"conver_{self.conver_id}_collection"
        
    def process_pdf(self, file_path):
        """Loads a PDF, splits text, and stores vector embeddings."""
        print(f"Processing PDF: {file_path}")

        # Load PDF
        loader = PyPDFLoader(file_path)
        data = loader.load()

        filename = os.path.basename(file_path)

        for doc in data:
            doc.metadata["source"] = filename
        
        
        # Text Splitting
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
        all_splits = text_splitter.split_documents(data)

        for doc in all_splits:
            doc.page_content = f"Source PDF: {filename}\n Content: [{doc.page_content}] \nEnd of Content for this chunk."

        print(f"Using Chroma collection: {self.conver_collection_name}")

        ## Append
        vectorstore = Chroma(
            collection_name=self.conver_collection_name,
            persist_directory=PERSIST_DIR,
            embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL)
        )
        vectorstore.add_documents(all_splits)
        
        print("PDF Processed & Vector Store Updated")
        return vectorstore
    
    def delete_pdf_from_vectorstore(self, filename):
        """Delete all vector entries related to a specific PDF from Chroma."""
        print(f"🗑️ Deleting vectors for PDF: {filename}")

        # Reconnect to vectorstore
        vectorstore = Chroma(
            collection_name=self.conver_collection_name,
            persist_directory=PERSIST_DIR,
            embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL)
        )

        # Fetch all documents and filter those belonging to this PDF
        all_docs = vectorstore.get(include=["metadatas", "documents"])
        matching_ids = [
            doc_id for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas'])
            if metadata.get("source") == filename
        ]

        if matching_ids:
            vectorstore.delete(ids=matching_ids)
            print(f"✅ Deleted {len(matching_ids)} vector(s) for {filename}")
            return True
        else:
            print(f"⚠️ No vectors found for: {filename}")
            return False
