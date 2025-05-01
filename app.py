import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from src.pages.chatbox import show_chatbox_ui
from src.pages.login_sign_up import show_login_page,show_signup_page,show_success_signup,show_success_logout
from src.db_manager.cookie_manager import CookieMgr
from src.db_manager.database_access import MongoDB
from streamlit.components.v1 import html
MongoDB()

# Streamlit UI Configuration
st.set_page_config(page_title="📄 AI PDF Chatbot", layout="wide")


# Check got user login or not since streamlit keep reruning
cookies = EncryptedCookieManager(
    prefix="pdfChatbot", 
    password="PLACEHOLDER_ONLY_REPLACE_DURING_PRODUCTION"
)

if not cookies.ready():
    st.stop()

st.session_state['cookie_instance'] = cookies


if 'curr_page' not in st.session_state:
    current_user = CookieMgr.getUserInfoCookie(cookies)

    if current_user:
        st.session_state['curr_page'] = 'chatbox'
        st.session_state['user_info'] = current_user
    else:
        st.session_state['curr_page'] = 'login'

curr_page = st.session_state.get('curr_page')
match curr_page:
    case None:
        show_login_page()
    case 'signup':
        show_signup_page()
    case 'success_signup':
        show_success_signup()
    case 'login':
        show_login_page()
    case 'success_logout':
        show_success_logout()
    case 'chatbox':
        cookies = st.session_state.get('cookie_instance')
        user_info = st.session_state.get('user_info')
        show_chatbox_ui(user_info)
