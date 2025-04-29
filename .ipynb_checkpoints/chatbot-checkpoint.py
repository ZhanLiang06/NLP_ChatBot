import os
import time
from langchain.chains import RetrievalQA
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.llms import Ollama
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.embeddings.ollama import OllamaEmbeddings

# Configuration
PERSIST_DIR = "data"
LOCAL_MODEL = "llama3"
EMBEDDING_MODEL = "nomic-embed-text"

# Load stored vector embeddings
vectorstore = Chroma(
    persist_directory=PERSIST_DIR,
    collection_name="rag_chroma",
    embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL),
)

retriever = vectorstore.as_retriever()

# Define LLM
llm = Ollama(
    base_url="http://localhost:11434",
    model=LOCAL_MODEL,
    verbose=True,
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
)

# Define prompt
template = """ 
Context: {context}
History: {history}

User: {question}
Chatbot:
"""
prompt = PromptTemplate(
    input_variables=["history", "context", "question"],
    template=template,
)

# Memory for conversation history
memory = ConversationBufferMemory(
    memory_key="history",
    return_messages=True,
    input_key="question"
)

# Define Retrieval-based Q&A chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type='stuff',
    retriever=retriever,
    verbose=True,
    chain_type_kwargs={
        "verbose": True,
        "prompt": prompt,
        "memory": memory,
    }
)

def ask_question(query):
    """Processes a user query and returns an answer from the stored PDF knowledge base."""
    if not query.strip():
        return "Please enter a valid question."

    response = qa_chain.invoke({"query": query})
    return response

# Example Usage
if __name__ == "__main__":
    test_query = "What is classification?"
    print(ask_question(test_query))
