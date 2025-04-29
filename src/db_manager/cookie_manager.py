from streamlit_cookies_manager import EncryptedCookieManager
import streamlit as st
import json


class CookieMgr:
    
    @staticmethod
    def getUserInfoCookie(cookies):
        user_info_json = cookies.get("user_info", None)
        if user_info_json:
            return json.loads(user_info_json)
        return None

    @staticmethod
    def saveUserInfoCookie(cookies,user_info):
        user_info_json = json.dumps(user_info)
        cookies['user_info'] = user_info_json
        cookies.save()
        return True
    
    @staticmethod
    def removeUserInfoCookie(cookies):
        if 'user_info' in cookies:
            cookies['user_info'] = json.dumps({})
            cookies.save()
        return cookies
