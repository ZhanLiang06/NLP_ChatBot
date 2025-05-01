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
        # Check if the provided password matches the hashed password
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    def _is_valid_email(self, email):
        # Basic email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _check_email_exists(self, email):
        query = "SELECT email FROM user_accounts WHERE email = %s"
        result = self.sqlDB.execute_select_one_query(query, (email,))
        return result is not None

    def user_login(self, email, password):
        if not self._is_valid_email(email):
            return False, None

        query = "SELECT userId, email, username, password FROM user_accounts WHERE email = %s"
        result = self.sqlDB.execute_select_one_query(query, (email,))
        
        if result and self._check_password(password, result['password'].encode('utf-8')):
            # Remove password from result before returning
            del result['password']
            return True, result
        elif result is None:
            return False, None
        else:
            return DB_EXECUTION_STATUS.ERROR, None
    
    def register_user(self, email, username, password):
        if not self._is_valid_email(email):
            return False, "Invalid email format"
        
        if self._check_email_exists(email):
            return False, "Email already exists"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        hashed_password = self._hash_password(password)
        query = "INSERT INTO user_accounts (userId, email, username, password) VALUES (%s, %s, %s, %s)"
        user_id = str(uuid.uuid4())
        params = (user_id, email, username, hashed_password.decode('utf-8'))
        
        result = self.sqlDB.execute_insert_query(query=query, params=params)
        if result:
            return True, "Registration successful"
        else:
            return False, "Database error during registration"
