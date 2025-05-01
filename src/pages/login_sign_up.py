import streamlit as st
from src.db_manager.users_acc_manager import UserAccountManager
from src.db_manager.cookie_manager import CookieMgr
import time

usrAccMgr = UserAccountManager()

def apply_custom_styles():
    st.markdown("""
    <style>
    .stApp {
        background-color: #1a1a1a;
    }
    .main {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 2.8em;
        font-weight: 600;
        margin-top: 1.2em;
        background-color: #3b82f6;
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    /* Base input field styling */
    .stTextInput>div>div>input {
        border-radius: 8px;
        height: 2.8em;
        border: 1px solid #4b5563;
        padding: 0.5em 1em;
        font-size: 0.95em;
        transition: all 0.3s ease;
        background-color: #111827;
        color: #e5e5e5;
        width: 100%;
        box-sizing: border-box;
    }
    /* Password input specific styling */
    div[data-baseweb="input"] {
        background-color: #111827;
        border-radius: 8px;
        border: 1px solid #4b5563;
    }
    div[data-baseweb="input"]:hover {
        border-color: #6b7280;
        background-color: #1f2937;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        background-color: #1f2937;
    }
    /* Style the eye icon */
    button[data-baseweb="button"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 10px !important;
        color: #6b7280 !important;
    }
    button[data-baseweb="button"]:hover {
        color: #e5e5e5 !important;
    }
    /* Container for password input */
    div[data-baseweb="input"] {
        display: flex;
        align-items: center;
    }
    div[data-baseweb="input"] input {
        border: none !important;
        background: transparent !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3b82f6;
        box-shadow: none;
        outline: none;
        background-color: #1f2937;
    }
    .stTextInput>div>div>input:hover {
        border-color: #6b7280;
        background-color: #1f2937;
    }
    .stTextInput>div>div>input::placeholder {
        color: #6b7280;
    }
    .title {
        text-align: center;
        color: #f3f4f6;
        margin-bottom: 1.5em;
        font-size: 2em;
        font-weight: 700;
    }
    .error-message {
        color: #ef4444;
        font-size: 0.9em;
        margin-top: 0.3em;
        margin-bottom: 0.5em;
        font-weight: 500;
    }
    .success-message {
        color: #22c55e;
        text-align: center;
        margin: 1em 0;
        font-size: 1em;
        font-weight: 500;
    }
    .form-group {
        margin-bottom: 1em;
    }
    .block-container {
        padding-top: 2em;
        padding-bottom: 2em;
        max-width: 500px;
        margin: 0 auto;
        background-color: #262626;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        padding: 2.5em;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }
    .stTextInput>div>div>label {
        color: #e5e5e5;
        font-weight: 500;
        font-size: 0.95em;
        margin-bottom: 0.5em;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.8em;
    }

    /* For laptop/desktop screens */
    @media (min-width: 1024px) {
        .block-container {
            width: 50%;
        }
    }

    /* For tablet screens in landscape */
    @media (min-width: 768px) and (orientation: landscape) {
        .block-container {
            width: 50%;
        }
    }

    /* For mobile screens in portrait */
    @media (max-width: 767px) {
        .block-container {
            width: 90%;
            padding: 1.5em;
        }
        .title {
            font-size: 1.8em;
            margin-bottom: 1.2em;
        }
    }

    /* For very small screens */
    @media (max-width: 320px) {
        .block-container {
            padding: 1.2em;
        }
        .title {
            font-size: 1.6em;
        }
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def show_login_page():
    apply_custom_styles()
    
    st.markdown('<h1 class="title">Login</h1>', unsafe_allow_html=True)
    
    email_error = None
    password_error = None
    general_error = None
    
    # Show all form fields first
    email = st.text_input("Email", key='login_email', placeholder="Enter your email")
    password = st.text_input("Password", type="password", key='login_password', placeholder="Enter your password")
    
    # Handle validation and errors after showing all fields
    if st.button("Login", key="login_btn"):
        if not email:
            email_error = "Email is required"
        if not password:
            password_error = "Password is required"
        
        if not email_error and not password_error:
            with st.spinner('Logging in...'):
                success, user_info = usrAccMgr.user_login(email=email, password=password)
                if success == True:
                    st.session_state['logged_in'] = True
                    st.session_state['user_info'] = user_info
                    cookies = st.session_state.get('cookie_instance')
                    CookieMgr.saveUserInfoCookie(cookies, user_info=user_info)
                    st.session_state['curr_page'] = 'chatbox'
                    st.rerun()
                elif success == False:
                    general_error = "Invalid email or password"
                else:
                    general_error = "Database Error"
    
    # Show errors after the button
    if email_error:
        st.markdown(f'<p class="error-message">{email_error}</p>', unsafe_allow_html=True)
    if password_error:
        st.markdown(f'<p class="error-message">{password_error}</p>', unsafe_allow_html=True)
    if general_error:
        st.markdown(f'<p class="error-message">{general_error}</p>', unsafe_allow_html=True)
    
    if st.button("Sign Up", key="signup_btn"):
        st.session_state['curr_page'] = 'signup'
        st.rerun()

def show_signup_page():
    apply_custom_styles()
    
    st.markdown('<h1 class="title">Sign Up</h1>', unsafe_allow_html=True)
    
    email_error = None
    username_error = None
    password_error = None
    confirm_password_error = None
    general_error = None
    
    # Show all form fields first
    email = st.text_input("Email", key='signup_email', placeholder="Enter your email")
    username = st.text_input("Username", key='signup_username', placeholder="Choose a username")
    password = st.text_input("Password", type="password", key='signup_password', placeholder="Create a password")
    confirm_password = st.text_input("Confirm Password", type="password", key='signup_confirm_password', placeholder="Confirm your password")
    
    # Handle validation and errors after showing all fields
    if st.button("Create Account", key="create_account_btn"):
        with st.spinner('Checking account details...'):
            if not email:
                email_error = "Email is required"
            elif not usrAccMgr._is_valid_email(email):
                email_error = "Invalid email format"
            elif usrAccMgr._check_email_exists(email):
                email_error = "Email already exists"
                
            if not username:
                username_error = "Username is required"
                
            if not password:
                password_error = "Password is required"
            elif len(password) < 8:
                password_error = "Password must be at least 8 characters long"
                
            if password and confirm_password and password != confirm_password:
                confirm_password_error = "Passwords do not match"
        
        if not any([email_error, username_error, password_error, confirm_password_error]):
            with st.spinner('Creating account...'):
                success, message = usrAccMgr.register_user(email=email, username=username, password=password)
                if success:
                    st.markdown(f'<p class="success-message">{message}</p>', unsafe_allow_html=True)
                else:
                    general_error = message
    
    # Show errors after the button
    if email_error:
        st.markdown(f'<p class="error-message">{email_error}</p>', unsafe_allow_html=True)
    if username_error:
        st.markdown(f'<p class="error-message">{username_error}</p>', unsafe_allow_html=True)
    if password_error:
        st.markdown(f'<p class="error-message">{password_error}</p>', unsafe_allow_html=True)
    if confirm_password_error:
        st.markdown(f'<p class="error-message">{confirm_password_error}</p>', unsafe_allow_html=True)
    if general_error:
        st.markdown(f'<p class="error-message">{general_error}</p>', unsafe_allow_html=True)
    
    if st.button("Back to Login", key="back_to_login_btn"):
        st.session_state['curr_page'] = 'login'
        st.rerun()

def show_success_logout():
    apply_custom_styles()
    
    st.markdown('<p class="success-message">Logged Out Successfully</p>', unsafe_allow_html=True)
    show_login_page()
    st.session_state['curr_page'] = 'login'

def show_success_signup():
    apply_custom_styles()
    
    st.markdown('<h1 class="title">Sign Up</h1>', unsafe_allow_html=True)
    st.markdown('<p class="success-message">Successfully Registered! Please Proceed to Login</p>', unsafe_allow_html=True)
    if st.button("Login Now!", key="login_now_btn"):
        st.session_state['curr_page'] = 'login'
        st.rerun()
