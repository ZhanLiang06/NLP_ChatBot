## Title: Interactive PDF Question Answer (QA) Chatbot with Saved Conversation History
Assignment by Lau Zhan Liang, Shino Kee Hui Wuan, Toh Yun Ning
### To run the program:
1. Have a python virtual envirnonemnt with Python 3.12.9
2. Make Sure you have all the libaries listed in requirements.txt in your python virtual environment
The core libaries that will be used are
---------------------------------------
streamlit
pypdf
langchain
langchain-community
streamlit_chat
chromadb
streamlit_cookies_manager
pymysql
pymongo
bcrypt
2. Starts the Ollama application (downloaded from https://ollama.com/)
run the following command in your powershell
------------------------------------------
ollama pull llama3
ollama pull nomic-embed-text
