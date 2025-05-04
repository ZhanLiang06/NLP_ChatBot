## Title: Interactive PDF Question Answer (QA) Chatbot with Saved Conversation History

**Assignment by**: Lau Zhan Liang, Shino Kee Hui Wuan, Toh Yun Ning

---

### How to Run the Program

1. **Set Up a Python Virtual Environment**  
   Ensure that your environment is using **Python version 3.12.9**.

2. **Install Required Libraries**  
   Use the provided `requirements.txt` file to install all dependencies in your virtual environment:

   ```bash
   pip install -r requirements.txt
   ```
   
   Core libaries used:
   |        |        |
   |--------|--------|
   | streamlit           | chromadb               |
   | pypdf               | streamlit_cookies_manager |
   | langchain           | pymysql                |
   | langchain-community | pymongo                |
   | streamlit_chat      | bcrypt                 |


3. **Install and Run Ollama on Your Local Machine**  
   - Download the **Ollama application** from the official website:  
     [https://ollama.com](https://ollama.com)
   - After installation, launch the Ollama app on the **same PC** where you will run this chatbot.

4. **Pull the Required Models for Ollama**  
   Open **Windows PowerShell** and run the following commands:

   ```bash
   ollama pull llama3
   ollama pull nomic-embed-text
   ```
   _If you have executed the above the command successfully before you can skip 4._

5. **Run the Program**

   **Option 1**: After setting up everything, you can launch the application by running the following command in your **Python command prompt**:

   ```bash
   streamlit run app.py
   ```

  **Option 2**: Using the Batch File (Windows) Run the batch script:
   ```bash
   .\run_app.bat
   ```


#### ⚠️ Cloud Database Error Note:
This application uses Cloud Atlas MongoDB and Amazon RDS (MySQL) for storing conversation history and user credentials.

The database instances may enter an inactive or sleep state due to inactivity.

If you encounter database connection issues, either:
1. Contact the team members for assistance (Lau Zhan Liang), or
2. Modify the connection settings in database_access.py with your own created database on cloud.


