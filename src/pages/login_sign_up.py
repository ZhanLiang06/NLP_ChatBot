import streamlit as st
from src.db_manager.users_acc_manager import UserAccountManager
from src.db_manager.cookie_manager import CookieMgr
usrAccMgr = UserAccountManager()

def show_login_page():
    st.title("Login")

    email = st.text_input("Email",key='login_email')
    password = st.text_input("Password", type="password", key='login_password')

    if st.button("Login"):
        success, user_info = usrAccMgr.user_login(email=email,password=password)
        if success == True:
            st.session_state['logged_in'] = True
            st.session_state['user_info'] = user_info
            cookies = st.session_state.get('cookie_instance')
            CookieMgr.saveUserInfoCookie(cookies,user_info=user_info)
            st.session_state['curr_page'] = 'chatbox'
            st.rerun()
        elif success == False:
            st.error("Invalid email or password.")
        else:
            st.error("Database Error")

    if st.button("Sign Up"):
        st.session_state['curr_page'] = 'signup'
        st.rerun()

def show_success_logout():
    st.success("Logged Out Successfully")
    show_login_page()
    #set next page prevent keep showing success logout msg
    st.session_state['curr_page'] = 'login'

def show_signup_page():
    st.title("Signup")

    email = st.text_input("Email",key='signup_email')
    username = st.text_input("Username",key='signup_username')
    password = st.text_input("Password", type="password",key='signup_password')
    confirm_password = st.text_input("Confirm Password", type="password", key='signup_confirm_password')

    if st.button("Create Account"):
        if not email or not username or not password or not confirm_password:
            st.warning("Please fill in all fields.")
            st.session_state['curr_page'] = 'signup'
            return
        
        if password != confirm_password:
            st.error("Passwords do not match!")
            st.session_state['curr_page'] = 'signup'
            return
        
        insert_success = usrAccMgr.register_user(email=email, username=username, password=password)
        if(insert_success):
            st.session_state['curr_page'] = 'success_signup'
            st.rerun()

        else:
            st.session_state['curr_page'] = 'signup'
            st.error("Fail to register you on the database. Please Try again")
    
    if st.button("Back to login"):
        st.session_state['curr_page'] = 'login'
        st.rerun()


def show_success_signup():
    st.title("Signup")
    st.success("Successfully Registered Users Please Proceed to Login")
    if st.button("Login Now!"):
        st.session_state['curr_page'] = 'login'
        st.rerun()
