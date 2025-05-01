import os
from langchain.chains import RetrievalQA
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.manager import CallbackManager
from langchain.llms import Ollama
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.embeddings.ollama import OllamaEmbeddings
from src.db_manager.database_access import MongoDB
from datetime import datetime


# === Configuration Constants === #
PERSIST_DIR = "vector_data"
LOCAL_MODEL = "llama3"
EMBEDDING_MODEL = "nomic-embed-text" 
#https://typical-shel-tarumt-a31d548a.koyeb.app/
#http://localhost:11434
OLLAMA_BASE_URL = "http://localhost:11434"
template = """
You are an intelligent, emotionally aware, and context-sensitive assistant helping a student.
You are expected to interpret and respond using extracted content from uploaded PDF documents, along with optional external knowledge when relevant. Follow these strict guidelines:

1. PDFs may be uploaded, replaced, or deleted at any time.
2. All extracted content is presented in this format:
   '''
   PDF source: <filename>
   <extracted_content>
   '''
   Multiple entries with the same filename indicate different content chunks from that file.
3. If extracted content is empty (`[]`), no PDF data is currently available.
4. Always prioritize **content from the PDFs** when answering questions, even if it conflicts with earlier discussion.
5. Use **external knowledge only** to clarify, supplement, or bridge content gaps in the PDFs.
6. If multiple PDFs are relevant, clearly indicate which PDF(s) you're referencing by filename.
7. Match my tone and style: serious if I'm serious, casual if I'm playful.
8. Use metaphors only when they enhance clarity — avoid overuse.
9. Focus strictly on my **current query** and the **relevant PDF content**.
10. Refer to previous conversation messages **only** when essential.
11. Most of my questions will involve interpreting or analyzing PDF contents.
12. Clearly indicate which PDFs your response is based on.
13. If no PDFs are present, provide a concise response using general knowledge.
14. Never fabricate PDF content — only use what's actually extracted.
15. Be concise but complete. Use bullet points or structured lists when helpful.
16. Avoid unnecessary repetition or elaboration unless I explicitly request it.
17. If I ask you to generate a **test sheet** based on the PDFs:
    - Extract key facts, concepts, or definitions from the relevant PDF(s).
    - Structure the test sheet into sections (e.g., Multiple Choice, True/False, Short Answer).
    - Include an optional answer key at the end if requested.

You are now ready. All further content is presented below in the standard format.

------------------------------------------------------------------
Extracted PDF Contents: [{context}]
------------------------------------------------------------------

------------------------------------------------------------------
Previous Conversation (light context only): {history}
------------------------------------------------------------------

Now, based on the extracted PDF contents and my current question, provide your response.

My Current Question: {question}

Focus only on my **current query** and its **related PDF content**.
"""




class ChatBot:
    def __init__(self, conversation_id,past_hist):
        self.conversation_id = conversation_id
        self.past_hist = past_hist
        self.retriever = self._get_retriever()
        self.llm = self._get_llm()
        self.prompt = self._get_prompt()
        self.memory = self._get_memory()
        self.qa_chain = self._get_qa_chain()
        self.mongo_mgr = MongoDB()

    def ask_question(self,query_dict):
        """Retrieve an answer from the AI based on the PDF content."""
        response = self.qa_chain.invoke({"query": query_dict['content']})
        response = response['result'] if isinstance(response, dict) and 'result' in response else str(response)
        response_dict = {"role":"AI","content":response,"timestamp":datetime.now()}
        self.save_msg_to_mongo(query_dict=query_dict,response_dict=response_dict)
        # Update conversation timestamp
        self.mongo_mgr.update_conversation_timestamp(self.conversation_id, datetime.now())
        # Ensure we return only the AI's answer, not the full dictionary
        return response_dict

    def save_msg_to_mongo(self,query_dict,response_dict):
        data_to_save = {
            "conversation_id": self.conversation_id,
            "content":[
                query_dict,
                response_dict
            ],
            "timestamp":datetime.now()
        }
        self.mongo_mgr.insert_onepair_msg(data_to_save)


    def _get_qa_chain(self):
        return RetrievalQA.from_chain_type(
        llm=self.llm,
        chain_type='stuff',
        retriever=self.retriever,
        verbose=True,
        chain_type_kwargs={
            "verbose": True,
            "prompt": self.prompt,
            "memory": self.memory,
        }
    )

    def _get_prompt(self):
        return PromptTemplate(
            input_variables=["history", "context", "question"],
            template=template,
        )
    
    def _get_memory(self):
        memory = ConversationBufferMemory(
            memory_key="history",
            return_messages=True,
            input_key="question"
        )
        memory.chat_memory.messages.extend(self.past_hist)
        return memory

    def _get_llm(self):
        return Ollama(
            base_url=OLLAMA_BASE_URL,
            model=LOCAL_MODEL,
            verbose=True,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
        )

    def _get_retriever(self):
        vectorstore = Chroma(
            persist_directory=PERSIST_DIR,
            collection_name=f"conver_{self.conversation_id}_collection",
            embedding_function=OllamaEmbeddings(model=EMBEDDING_MODEL)
        )

        return vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 15, 'fetch_k': 50})
