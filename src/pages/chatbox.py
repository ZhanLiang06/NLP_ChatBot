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
                    curr_convo_data = {
                        "id": str(uuid.uuid4()),
                        "title": new_convo_title.strip(),
                        "user_id": user_info['userId'],  # Add logic to fetch user_id as needed
                        "timestamp": datetime.now()  # Add a timestamp or other metadata as needed
                    }
                    mongo_db.insert_one_conver(curr_convo_data)
                    st.success(f"New conversation titled '{curr_convo_data['title']}' has been created!")
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
        # Don't show chat box if processing files
        if st.session_state.get("processing_state") == "starting":
            return

        # Load conversation history only when needed
        if 'curr_conver_id' not in st.session_state or st.session_state['curr_conver_id'] != curr_convo_data['id']:
            st.session_state['curr_conver_id'] = curr_convo_data['id']
            str_hist, parsed_hist = _load_history_from_mongo(curr_convo_data['id'])
            st.session_state['str_hist'] = str_hist
            st.session_state['parsed_hist'] = parsed_hist
        else:
            str_hist = st.session_state['str_hist']
            parsed_hist = st.session_state['parsed_hist']
        
        display_main_chat_box(curr_convo_data)

def get_unique_filename(folder_path, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    while os.path.exists(os.path.join(folder_path, unique_filename)):
        unique_filename = f"{base} ({counter}){ext}"
        counter += 1
    return unique_filename

def display_pdf_upload(curr_convo_data):
    docProcessor = DocumentProcessor(curr_convo_data['id'])
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.header("📤 Upload a PDF")
    if "processing_state" not in st.session_state:
        st.session_state["processing_state"] = "idle"
        st.session_state["files_to_process"] = None
        st.session_state["processed_count"] = 0
        st.session_state["total_files"] = 0
        st.session_state["processed_files"] = []

    # Only show file uploader when not processing files
    if st.session_state["processing_state"] == "idle":
        if "uploaded_pdf_file_key" not in st.session_state:
            st.session_state.uploaded_pdf_file_key = "pdf_uploader_a_0"
        uploaded_files = st.file_uploader("Upload a PDF file", type=["pdf"], key=st.session_state.uploaded_pdf_file_key, accept_multiple_files=True)
        
        # If files are uploaded, set state and rerun immediately
        if uploaded_files:
            st.session_state["processing_state"] = "starting"
            st.session_state["files_to_process"] = uploaded_files
            st.session_state["total_files"] = len(uploaded_files)
            st.session_state["processed_count"] = 0
            st.session_state["processed_files"] = []
            st.rerun()
    else:
        st.info("⏳ Processing files... Please wait.")
        uploaded_files = None

    uploads_folder = f"pdf_store/{curr_convo_data['id']}/"
    os.makedirs(uploads_folder, exist_ok=True)

    def process_one_file(uploaded_file, processing_progress, global_status_msg):
        processing_msg = st.sidebar.empty()
        processing_msg.info(f"{processing_progress} file(s) processed")
        with st.spinner(f"Processing: {uploaded_file.name}"):
            unique_filename = get_unique_filename(uploads_folder, uploaded_file.name)
            file_path = os.path.join(uploads_folder, unique_filename)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            status_msg = st.sidebar.empty()

            vec = docProcessor.process_pdf(file_path)
            if vec:
                st.session_state["processed_files"].append(unique_filename)
                global_status_msg.success("✅ Processed files:\n" + "\n".join([f"- {f}" for f in st.session_state["processed_files"]]))
            else:
                status_msg.error(f"❌ Failed: {unique_filename}")
            status_msg.empty()

            ## save conversation
            if 'need_save_conver' in st.session_state and st.session_state['need_save_conver'] == True:
                mongo_db = MongoDB()
                mongo_db.insert_one_conver(curr_convo_data)
                st.session_state['need_save_conver'] = False
        processing_msg.empty()

    # Process files if in starting state
    if st.session_state["processing_state"] == "starting" and st.session_state["files_to_process"]:
        global_status_msg = st.sidebar.empty()
        try:
            files_to_process = st.session_state["files_to_process"]
            for uploaded_file in files_to_process:
                processing_progress = f"{st.session_state['processed_count']}/{st.session_state['total_files']}"
                process_one_file(uploaded_file, processing_progress, global_status_msg)
                st.session_state["processed_count"] += 1
            
            global_status_msg.empty()
            if st.session_state["processed_files"]:
                st.sidebar.success("✅ Successfully processed files:\n" + "\n".join([f"- {f}" for f in st.session_state["processed_files"]]))
            else:
                st.sidebar.warning("No files were successfully processed")
        finally:
            # Reset all processing states
            st.session_state["processing_state"] = "idle"
            st.session_state["files_to_process"] = None
            st.session_state["processed_count"] = 0
            st.session_state["total_files"] = 0
            st.session_state["processed_files"] = []
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
                            success = docProcessor.delete_pdf_from_vectorstore(filename)
                            if(success):
                                os.remove(file_path)
                            st.rerun()
                        except Exception as e:
                            print(f"Exception in removing files: {e}")
                            st.error(f"Failed to remove {filename}: {e}")


def display_main_chat_box(curr_convo_data):
    # Double-check we're not processing files
    if st.session_state.get("processing_state") == "starting":
        return

    components.show_header("Start of Conversation")
    
    str_hist, parsed_hist = st.session_state['str_hist'], st.session_state['parsed_hist']
    
    ## Display History
    count = 0
    for msg in str_hist:
        if msg['role'] == 'human':
            # Format timestamp
            timestamp = msg['timestamp'].strftime("%I:%M %p")  # Format: 03:45 PM
            display_chat_dialogue(f"{msg['content']}\n\n<small style='color: #6b7280;'>{timestamp}</small>", 
                                is_user=True, 
                                key=str(count),
                                allow_html=True)
            count += 1
        else:
            # Format timestamp
            timestamp = msg['timestamp'].strftime("%I:%M %p")  # Format: 03:45 PM
            display_chat_dialogue(f"{msg['content']}\n\n<small style='color: #6b7280;'>{timestamp}</small>", 
                                key=str(count),
                                allow_html=True)
            count += 1

    # Show inference time for the last message if it exists
    if len(str_hist) >= 2 and str_hist[-1]['role'] == 'AI' and str_hist[-2]['role'] == 'human':
        inference_time = (str_hist[-1]['timestamp'] - str_hist[-2]['timestamp']).total_seconds()
        st.markdown(f"<small style='color: #6b7280;'>Response time: {inference_time:.2f} seconds</small>", 
                   unsafe_allow_html=True)

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
            # Add CSS to hide form border
            st.markdown("""
                <style>
                    div[data-testid="stForm"] {
                        border: none;
                        padding: 0;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            with st.form("chat_form", clear_on_submit=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    
                    query = st.text_input(
                        f"Current Conversation: {curr_convo_data['title']}", 
                        key="user_query_input",
                        value="",
                        placeholder="💬 Ask a question about the PDF",
                        label_visibility="hidden",
                        autocomplete="off"
                    )
                with col2:
                    submit_clicked = st.form_submit_button("🔍 Get Answer")
                
                if submit_clicked and query and query.strip():
                    st.session_state["pending_input"] = query
                    st.session_state["user_submit_query"] = True
                    input_col.empty()
                    st.rerun()
                elif submit_clicked:
                    st.warning("Please enter a question.")

            # Add JavaScript to focus input
            html("""
                <script>
                    setTimeout(() => {
                        const input = window.parent.document.querySelector('input[aria-label*="Current Conversation"]');
                        if (input) {
                            input.focus();
                        }
                    }, 100);
                </script>
            """, height=0)

    if st.session_state["pending_input"] is not None and st.session_state.get("user_submit_query", False):
        query = st.session_state["pending_input"]
        user_query_dict = {"role":"human","content":query,"timestamp":datetime.now()}
        user_query_langchain_msg = HumanMessage(content=query)
        # Format timestamp for user query
        timestamp = user_query_dict['timestamp'].strftime("%I:%M %p")
        display_chat_dialogue(f"{query}\n\n<small style='color: #6b7280;'>{timestamp}</small>", 
                            is_user=True, 
                            key=str(count),
                            allow_html=True)
        count += 1
        with st.spinner('🤔 Thinking...'):
            start_time = time.time()
            ai_response_dict = chatbot.ask_question(user_query_dict)
            inference_time = time.time() - start_time
            ai_response_langchain_msg = AIMessage(content=ai_response_dict['content'])
        # Format timestamp for AI response
        timestamp = ai_response_dict['timestamp'].strftime("%I:%M %p")
        display_chat_dialogue(f"{ai_response_dict['content']}\n\n<small style='color: #6b7280;'>{timestamp}</small>", 
                            key=str(count),
                            allow_html=True)

        ##update session
        st.session_state['str_hist'].append(user_query_dict)
        st.session_state['str_hist'].append(ai_response_dict)
        st.session_state['parsed_hist'].append(user_query_langchain_msg)
        st.session_state['parsed_hist'].append(ai_response_langchain_msg)
        st.session_state["pending_input"] = None
        st.session_state["user_submit_query"] = False  # Reset submission flag

        ##If this is a new conversation save it
        if 'need_save_conver' in st.session_state and st.session_state['need_save_conver'] == True:
            mongo_db = MongoDB()
            mongo_db.insert_one_conver(curr_convo_data)
            st.session_state['need_save_conver'] = False
        
        # Store the inference time in session state before rerun
        st.session_state['last_inference_time'] = inference_time
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
