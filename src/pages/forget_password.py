import streamlit as st
from src.db_manager.users_acc_manager import UserAccountManager
import time
import random
import string
from src.services.otp import OTP
from datetime import datetime, timedelta
import streamlit.components.v1 as components

usrAccMgr = UserAccountManager()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def is_otp_expired(otp_time):
    if not otp_time:
        return True
    expiration_time = otp_time + timedelta(minutes=5)
    return datetime.now() > expiration_time

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
    .forget-password-link {
        color: #3b82f6;
        text-decoration: none;
        font-size: 0.9em;
        text-align: right;
        display: block;
        margin-top: 0.5em;
    }
    .forget-password-link:hover {
        text-decoration: underline;
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
    </style>
    """, unsafe_allow_html=True)

def show_forget_password_page():
    apply_custom_styles()
    st.markdown('<h1 class="title">Forgot Password</h1>', unsafe_allow_html=True)
    
    if 'otp_sent' not in st.session_state:
        st.session_state.otp_sent = False
    if 'otp_verified' not in st.session_state:
        st.session_state.otp_verified = False
    if 'email' not in st.session_state:
        st.session_state.email = ""
    if 'otp' not in st.session_state:
        st.session_state.otp = None
    if 'otp_time' not in st.session_state:
        st.session_state.otp_time = None
    if 'resend_cooldown' not in st.session_state:
        st.session_state.resend_cooldown = 0
    
    # Update timer
    
    email_error = None
    otp_error = None
    password_error = None
    confirm_password_error = None
    general_error = None
    
    if not st.session_state.otp_sent:
        email = st.text_input("Email", key='forget_email', placeholder="Enter your email")
        
        if st.button("Send OTP", key="send_otp_btn"):
            if not email:
                email_error = "Email is required"
            else:
                # Check if email exists in database
                if usrAccMgr.check_email_exists(email):
                    st.session_state.email = email
                    st.session_state.otp = generate_otp()
                    st.session_state.otp_time = datetime.now()
                    otp_instance = OTP(otp=st.session_state.otp)
                    otp_instance.send_otp_email(email)
                    st.session_state.otp_sent = True
                    st.session_state.resend_cooldown = 60  # 60 seconds cooldown
                    st.rerun()
                else:
                    general_error = "Email not found in our system"
    
    elif not st.session_state.otp_verified:
        # Show resend OTP button with cooldown
        resend_otp_triggered = st.button("Resend OTP", key="resend_otp_hidden_btn")
        
        if resend_otp_triggered:
            st.session_state.otp = generate_otp()
            st.session_state.otp_time = datetime.now()
            otp_instance = OTP(otp=st.session_state.otp)
            otp_instance.send_otp_email(st.session_state.email)
            st.session_state.resend_cooldown = 60
            st.rerun()
        
        st.info(f"OTP has been sent to {st.session_state.email}")
        otp = st.text_input("Enter OTP", key='verify_otp', placeholder="Enter the 6-digit OTP")
        
        if st.button("Verify OTP", key="verify_otp_btn"):
            if not otp:
                otp_error = "OTP is required"
            elif is_otp_expired(st.session_state.otp_time):
                otp_error = "OTP has expired. Please request a new one."
            elif otp != st.session_state.otp:
                otp_error = "Invalid OTP"
            else:
                st.session_state.otp_verified = True
                st.rerun()
    
    else:
        new_password = st.text_input("New Password", type="password", key='new_password', placeholder="Enter new password")
        confirm_password = st.text_input("Confirm New Password", type="password", key='confirm_password', placeholder="Confirm new password")
        
        if st.button("Reset Password", key="reset_password_btn"):
            if not new_password:
                password_error = "New password is required"
            elif not confirm_password:
                confirm_password_error = "Please confirm your new password"
            elif new_password != confirm_password:
                confirm_password_error = "Passwords do not match"
            else:
                # Update password in database
                if usrAccMgr.update_password(st.session_state.email, new_password):
                    st.session_state.otp_sent = False
                    st.session_state.otp_verified = False
                    st.session_state.email = ""
                    st.session_state.otp = None
                    st.session_state.otp_time = None
                    st.session_state.resend_cooldown = 0
                    st.success("Password has been reset successfully!")
                    time.sleep(2)
                    st.session_state['curr_page'] = 'login'
                    st.rerun()
                else:
                    general_error = "Failed to reset password. Please try again."
    
    # Show errors
    if email_error:
        st.markdown(f'<p class="error-message">{email_error}</p>', unsafe_allow_html=True)
    if otp_error:
        st.markdown(f'<p class="error-message">{otp_error}</p>', unsafe_allow_html=True)
    if password_error:
        st.markdown(f'<p class="error-message">{password_error}</p>', unsafe_allow_html=True)
    if confirm_password_error:
        st.markdown(f'<p class="error-message">{confirm_password_error}</p>', unsafe_allow_html=True)
    if general_error:
        st.markdown(f'<p class="error-message">{general_error}</p>', unsafe_allow_html=True)
    
    if st.button("Back to Login", key="back_to_login_btn"):
        st.session_state['curr_page'] = 'login'
        st.session_state.otp_sent = False
        st.session_state.otp_verified = False
        st.session_state.email = ""
        st.session_state.otp = None
        st.session_state.otp_time = None
        st.session_state.resend_cooldown = 0
        st.rerun() 