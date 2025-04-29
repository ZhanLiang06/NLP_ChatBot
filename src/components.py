import streamlit as st
from src.db_manager.cookie_manager import CookieMgr

def show_header(title):
    # Create a row with buttons
    col1, col2 = st.columns([6, 1])  # Define columns to align buttons

    with col1:
        st.title(title)

    with col2:
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.session_state['user_info'] = None
            cookies = st.session_state.get('cookie_instance')
            CookieMgr.removeUserInfoCookie(cookies)
            st.session_state['curr_page'] = 'success_logout'
            st.rerun()
    st.markdown('-------------------------------------------------')
