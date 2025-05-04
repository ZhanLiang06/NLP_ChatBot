from src.db_manager.database_access import MySqlDB
from src.enums import DB_EXECUTION_STATUS
import uuid
import bcrypt
import re

class UserAccountManager:
    def __init__(self):
        self.sqlDB = MySqlDB()

    def _hash_password(self, password):
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    def _check_password(self, password, hashed):
        try:
            if not isinstance(hashed, bytes):
                hashed = hashed.encode('utf-8')

            if not hashed.startswith(b"$2a$") and not hashed.startswith(b"$2b$") and not hashed.startswith(b"$2y$"):
                print(f"Invalid bcrypt hash format: {hashed}")
                return False

            match = bcrypt.checkpw(password.encode('utf-8'), hashed)
            return match

        except (ValueError, TypeError) as e:
            print(f"Password check failed due to invalid hash: {e}, hash: {hashed}")
            return False

    def _is_valid_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def check_email_exists(self, email):
        query = "SELECT email FROM user_accounts WHERE email = %s"
        result = self.sqlDB.execute_select_one_query(query, (email,))
        return result is not None

    def check_uid_exists(self, userId):
        query = "SELECT userId FROM user_accounts WHERE userId = %s"
        result = self.sqlDB.execute_select_one_query(query, (userId,))
        return result is not None

    def user_login(self, email, password):
        if not self._is_valid_email(email):
            return False, None

        query = "SELECT userId, email, username, password FROM user_accounts WHERE email = %s"
        result = self.sqlDB.execute_select_one_query(query, (email,))
        match_ps = None
        
        if result:
            match_ps = self._check_password(password, result['password'])
            if match_ps:
                del result['password']
                return True, result
            else:
                return False, None
        elif match_ps == False:
            return False, None
        elif result is None:
            return False, None
        else:
            return DB_EXECUTION_STATUS.ERROR, None
    
    def register_user(self, email, username, password):
        if not self._is_valid_email(email):
            return False, "Invalid email format"
        
        if self.check_email_exists(email):
            return False, "Email already exists"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        hashed_password = self._hash_password(password)
        query = "INSERT INTO user_accounts (userId, email, username, password) VALUES (%s, %s, %s, %s)"
        user_id = str(uuid.uuid4())

        ## check user id is unique
        while self.check_uid_exists(user_id):
            user_id = str(uuid.uuid4())
            
        params = (user_id, email, username, hashed_password.decode('utf-8'))
        
        result = self.sqlDB.execute_insert_query(query=query, params=params)
        if result:
            return True, "Registration successful"
        else:
            return False, "Database error during registration"
    
    def update_password(self, email, new_password):
        """
        Update the user's password without verifying the old password.
        Suitable for 'Forgot Password' or OTP reset scenarios.
        """
        if not self._is_valid_email(email):
            return False, "Invalid email format"

        if len(new_password) < 8:
            return False, "Password must be at least 8 characters long"

        # Check if email exists
        query = "SELECT email FROM user_accounts WHERE email = %s"
        result = self.sqlDB.execute_select_one_query(query, (email,))
        if result is None:
            return False, "Email not found"

        # Hash the new password
        hashed_password = self._hash_password(new_password).decode('utf-8')

        # Update password in the database
        update_query = "UPDATE user_accounts SET password = %s WHERE email = %s"
        update_result = self.sqlDB.execute_insert_query(query=update_query, params=(hashed_password, email))

        if update_result:
            return True, "Password updated successfully"
        else:
            return False, "Database error during password update"
