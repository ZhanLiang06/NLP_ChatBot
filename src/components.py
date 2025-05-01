import streamlit as st
from src.db_manager.cookie_manager import CookieMgr

def show_header(title):
    st.title(title) 
    st.markdown('-------------------------------------------------')
