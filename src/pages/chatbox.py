import os
import streamlit as st
from src.services.document_processing import DocumentProcessor
from src.services.chatbot import ChatBot
from src import components
from src.db_manager.database_access import MongoDB
import uuid
from datetime import datetime
from streamlit_chat import message as display_chat_dialogue
from langchain.schema import HumanMessage, AIMessage
from streamlit.components.v1 import html
from src.db_manager.cookie_manager import CookieMgr
import time

def show_chatbox_ui(user_info):
    mongo_db = MongoDB()
    #get number of conversations
    conversations = mongo_db.get_conversation(user_id=user_info['userId'])

    # Sidebar - PDF Upload
    selected_convo = None
    curr_convo_data = None
    with st.sidebar:
        # Account Section
        with st.expander(f"Account ({user_info['username']})", expanded=False):
            if st.button("Log Out", key="logout_btn", help="Click to log out of your account"):
                st.session_state['logged_in'] = False
                st.session_state['user_info'] = None
                cookies = st.session_state.get('cookie_instance')
                CookieMgr.removeUserInfoCookie(cookies)
                st.session_state['curr_page'] = 'success_logout'
                st.rerun()
                
        ##Show all conversations
        first_conver = next(conversations, None)
        if first_conver:
            first_conver_title = [f"{first_conver['title']} (ID: {first_conver['id']})"]
        else:
            first_conver_title = [f"Your First Conversation with chatbot"]
        
        convo_titles = ['Create New Conversation'] + first_conver_title + [f"{convo['title']} (ID: {convo['id']})" for convo in conversations]


        if 'convo_selection' not in st.session_state:
            st.session_state['convo_selection'] = convo_titles[1]  
        
        if 'need_save_conver' in st.session_state and st.session_state['need_save_conver'] == False and st.session_state['convo_selection'] == 'Your First Conversation with chatbot':
            st.session_state['convo_selection'] = convo_titles[1]

        
        if 'have_new_convo' in st.session_state:
            if st.session_state['have_new_convo'] == True:
                st.session_state['convo_selection'] = convo_titles[1]
                st.session_state['have_new_convo'] = False

        selected_convo = st.selectbox(
            "Select a conversation",
            convo_titles,
            index=convo_titles.index(st.session_state['convo_selection']),
            key='convo_selection'
        )
        
        ##Create new conversation
        if selected_convo == 'Create New Conversation':
            new_convo_title = st.text_input("Enter title for new conversation", "New Conversation")
            if st.button("Create Conversation"):
                if new_convo_title.strip(): 
                    # Insert new conversation into the database
                    new_convo_data = {
                        "id": str(uuid.uuid4()),
                        "title": new_convo_title.strip(),
                        "user_id": user_info['userId'],  # Add logic to fetch user_id as needed
                        "timestamp": datetime.now()  # Add a timestamp or other metadata as needed
                    }
                    mongo_db.insert_one_conver(new_convo_data)
                    st.success(f"New conversation titled '{new_convo_title}' has been created!")
                    st.session_state['have_new_convo'] = True
                    st.rerun()
                else:
                    st.error("Please enter a valid title for the new conversation.")
        elif selected_convo == 'Your First Conversation with chatbot':
            curr_convo_data = {
                "id": str(uuid.uuid4()),
                "title": selected_convo.strip(),
                "user_id": user_info['userId'],  # Add logic to fetch user_id as needed
                "timestamp": datetime.now()  # Add a timestamp or other metadata as needed
            }
            st.session_state['need_save_conver'] = True
            display_pdf_upload(curr_convo_data)
        else:
            selected_convo_id = selected_convo.split(" (ID: ")[1].split(")")[0]
            curr_convo_data = next(mongo_db.get_conversation_by_id(selected_convo_id))
            display_pdf_upload(curr_convo_data)

    ## Display Main ChatBox
    if selected_convo != 'Create New Conversation':
        display_main_chat_box(curr_convo_data)

def get_unique_filename(folder_path, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    while os.path.exists(os.path.join(folder_path, unique_filename)):
        print("What the")
        unique_filename = f"{base} ({counter}){ext}"
        counter += 1
    return unique_filename

def display_pdf_upload(curr_convo_data):
    docProcessor = DocumentProcessor(curr_convo_data['id'])
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.header("📤 Upload a PDF")
    if "uploaded_pdf_file_key" not in st.session_state:
        st.session_state.uploaded_pdf_file_key = "pdf_uploader_a_0"
    uploaded_files = st.file_uploader("Upload a PDF file", type=["pdf"], key=st.session_state.uploaded_pdf_file_key)
    uploads_folder = f"pdf_store/{curr_convo_data['id']}/"
    os.makedirs(uploads_folder, exist_ok=True)

    def process_one_file(uploaded_file):
        unique_filename = get_unique_filename(uploads_folder, uploaded_file.name)
        file_path = os.path.join(uploads_folder, unique_filename)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        status_msg = st.sidebar.empty()
        status_msg.success(f"✅ Uploaded: {unique_filename}")
        status_msg.info(f"🔄 Processing: {unique_filename}")

        vec = docProcessor.process_pdf(file_path)
        if vec:
            status_msg.success(f"✅ Processed: {unique_filename}")
        else:
            status_msg.error(f"❌ Failed: {unique_filename}")
        status_msg.empty()

        ## save conversation
        if 'need_save_conver' in st.session_state and st.session_state['need_save_conver'] == True:
            mongo_db = MongoDB()
            mongo_db.insert_one_conver(curr_convo_data)
            st.session_state['need_save_conver'] = False

    if uploaded_files:
        small_global_status_msg = st.sidebar.empty()
        if isinstance(uploaded_files, list): 
            small_global_status_msg.info(f"Processing {len(uploaded_files)} file(s).")
            for uploaded_file in uploaded_files:
                process_one_file(uploaded_file)
            st.sidebar.success(f"✅ Successfully Processed all files Number of files {len(uploaded_files)}")
        else:
            small_global_status_msg.info(f"Processing 1 file.")
            process_one_file(uploaded_files)
            st.sidebar.success(f"✅ Successfully Processed Uploaded File")

        small_global_status_msg.empty()
        
        st.session_state.uploaded_pdf_file_key = f"pdf_uploader_a_{int(st.session_state.uploaded_pdf_file_key.split('_')[-1]) + 1}"
        st.rerun()


    # Show list of uploaded PDF filenames
    if os.path.exists(uploads_folder):
        uploaded_files = os.listdir(uploads_folder)
        if uploaded_files:
            st.markdown("### 📄 Uploaded PDFs:")
            for filename in uploaded_files:
                file_path = os.path.join(uploads_folder, filename)
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(f"- {filename}")
                with col2:
                    if st.button("❌", key=f"remove_{filename}"):
                        try:
                            # st.info(f"Removing {filename} from vector database")
                            success = docProcessor.delete_pdf_from_vectorstore(filename)
                            if(success):
                                # st.success(f"Removed: {filename} from vector database")
                                os.remove(file_path)
                            st.rerun()
                        except Exception as e:
                            print(f"Exception in removing files: {e}")
                            st.error(f"Failed to remove {filename}: {e}")


def display_main_chat_box(curr_convo_data):
    components.show_header("Start of Conversation")
    # if 1st run
    if 'curr_conver_id' not in st.session_state:
        st.session_state['curr_conver_id'] = curr_convo_data['id']
        str_hist, parsed_hist = _load_history_from_mongo(curr_convo_data['id'])
        st.session_state['str_hist'] = str_hist
        st.session_state['parsed_hist'] = parsed_hist
    # if change conversation
    elif st.session_state['curr_conver_id'] != curr_convo_data['id']:
        st.session_state['curr_conver_id'] = curr_convo_data['id']
        str_hist, parsed_hist = _load_history_from_mongo(curr_convo_data['id'])
        st.session_state['str_hist'] = str_hist
        st.session_state['parsed_hist'] = parsed_hist

    str_hist, parsed_hist = st.session_state['str_hist'], st.session_state['parsed_hist']
    ## Display History
    count = 0
    for msg in str_hist:
        if msg['role'] == 'human':
            display_chat_dialogue(msg['content'],is_user=True,key=str(count))
            count += 1
        else:
            display_chat_dialogue(msg['content'],key=str(count))
            count += 1

    ## Initialize Chatbot
    if 'chat_bot_instance' not in st.session_state:
        st.session_state['chat_bot_instance'] = ChatBot(curr_convo_data['id'],parsed_hist)
    elif st.session_state['chat_bot_instance'].conversation_id != curr_convo_data['id']:
        st.session_state['chat_bot_instance'] = ChatBot(curr_convo_data['id'],parsed_hist)

    chatbot = st.session_state['chat_bot_instance']

    if "pending_input" not in st.session_state:
        st.session_state["pending_input"] = None
    
    if "user_query_input" not in st.session_state:
        st.session_state["user_query_input"] = ''

    
    # Get input
    if st.session_state["pending_input"] is None:
        input_col = st.empty()
        with input_col.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                query = st.text_input(
                    f"Current Conversation: {curr_convo_data['title']}", 
                    key="user_query_input",
                    value=st.session_state["user_query_input"],
                    placeholder="💬 Ask a question about the PDF",
                    on_change=lambda: setattr(st.session_state, "pending_input", st.session_state.user_query_input),
                )
            with col2:
                st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
                if st.button("🔍 Get Answer", key="get_answer_btn"):
                    if st.session_state.user_query_input and st.session_state.user_query_input.strip():
                        st.session_state["pending_input"] = st.session_state.user_query_input
                        st.session_state.user_query_input = ""  # Clear the input
                        input_col.empty()
                        st.rerun()
                    else:
                        st.warning("Please enter a question.")
            
            html("""
            <script>
            setTimeout(() => {
                const input = window.parent.document.querySelector('input[aria-label*="Current Conversation"]');
                if (input) {
                    input.focus();
                    //-----------
                    // Function to check if user is at bottom
                    function isAtBottom() {
                        return window.parent.scrollY + window.parent.innerHeight >= document.body.scrollHeight - 50;
                    }
                    
                    // Scroll to bottom when typing starts
                    input.addEventListener('input', function() {
                        if (!isAtBottom()) {
                            window.parent.scrollTo(-10, document.body.scrollHeight);
                        }
                    });
                    //--------------
                    // Handle Enter key
                    input.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            window.parent.document.querySelector('button[data-testid="stButton"]').click();
                            setTimeout(() => {
                                window.parent.scrollTo(0, document.body.scrollHeight);
                            }, 100);
                        }
                    });
                }
            }, 100);
            </script>
            """, height=0)
    
    if st.session_state["pending_input"] is not None:
        query = st.session_state["pending_input"]
        user_query_dict = {"role":"human","content":query,"timestamp":datetime.now()}
        user_query_langchain_msg = HumanMessage(content=query)
        display_chat_dialogue(query,is_user=True,key=str(count))
        count += 1
        with st.spinner('🤔 Thinking...'):
            html("""
            <script>
            setTimeout(() => {
                const scrollContainer = window.parent.document.querySelector('.main .block-container');
                if (scrollContainer) {
                    scrollContainer.scrollTop = scrollContainer.scrollHeight;
                }
            }, 100);
            </script>
            """, height=0)
            start_time = time.time()
            ai_response_dict = chatbot.ask_question(user_query_dict)
            inference_time = time.time() - start_time
            ai_response_langchain_msg = AIMessage(content=ai_response_dict['content'])
        display_chat_dialogue(ai_response_dict['content'],key=str(count))
        st.write(f"Response time: {inference_time:.2f} seconds")

        
        ##update session
        st.session_state['str_hist'].append(user_query_dict)
        st.session_state['str_hist'].append(ai_response_dict)
        st.session_state['parsed_hist'].append(user_query_langchain_msg)
        st.session_state['parsed_hist'].append(ai_response_langchain_msg)
        st.session_state["pending_input"] = None

        ##If this is a new conversation save it
        if 'need_save_conver' in st.session_state and st.session_state['need_save_conver'] == True:
            mongo_db = MongoDB()
            mongo_db.insert_one_conver(curr_convo_data)
            st.session_state['need_save_conver'] = False
        
        st.rerun()



def _load_history_from_mongo(conver_id):
    parsed_history = []
    str_history = []
    mongo_mgr = MongoDB()
    result = mongo_mgr.get_messages(conver_id)
    for conver in result:
        msg_pair = conver['content']
        for msg in msg_pair:
            str_history.append(msg)
            if msg['role'] == 'human':
                parsed_history.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'AI':
                parsed_history.append(AIMessage(content=msg['content']))
    return str_history, parsed_history

