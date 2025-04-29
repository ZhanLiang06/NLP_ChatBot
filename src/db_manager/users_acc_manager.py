from src.db_manager.database_access import MySqlDB
from src.enums import DB_EXECUTION_STATUS
import uuid
class UserAccountManager:
    def __init__(self):
        self.sqlDB = MySqlDB()

    def user_login(self, email, password):
        query = "SELECT userId, email, username FROM user_accounts WHERE email = %s AND password = %s"
        params = (email,password)
        result = self.sqlDB.execute_select_one_query(query,params)
        if result:
            return True, result
        elif result == None:
            return False, result
        else:
            return DB_EXECUTION_STATUS.ERROR, result
    
    def register_user(self,email,username,password):
        query = "INSERT INTO user_accounts (userId, email, username, password) VALUES (%s, %s, %s, %s)"
        user_id = str(uuid.uuid4()) 
        params = (user_id,email,username,password)
        result = self.sqlDB.execute_insert_query(query=query,params=params)
        if result:
            return True
        else:
            return False
