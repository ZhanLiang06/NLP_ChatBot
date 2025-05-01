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
#http://localhost:11434
OLLAMA_BASE_URL = "http://localhost:11434"
template = """
You are the best helpful, intelligent and emotion assistant and I am a student.

The following information has been extracted from PDF documents. Please note the following:
1. I may add or remove PDFs, which could lead to discrepancies between the extracted PDF contents and the conversation history.
2. The PDF contents retrieved are based on the similarity between the my current question and the content of the PDFs stored in the vector database. As such, it may not fully represent all the PDFs uploaded by my.
3. There might be a possibility that me do not upload any PDFs or removes all of the PDFs
4. You may incorporate extra knowledge to enhance user understanding.
5. You may incorporate metaphor only if relevant to enhance understanding.
6. Answers based on my tone, when I'm serious please be serious, when I'm having fun, please do also mind to give answers appropriately.
7. At most of the time I will ask you about the PDFs content.
------------------------------------------------------------------
Information extracted from PDF documents: [{context}]

Previous conversation between you and me:
------------------------------------------------------------------
{history}

Now, based on the extracted PDF contents and the conversation so far, answer the my current question.

User's Current Question:
----------
{question}

Note that your answers must be precise, structured, straight to the point, easily understanable.
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
