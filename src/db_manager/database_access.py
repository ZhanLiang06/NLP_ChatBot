import pymysql
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

class MongoDB:
    _global_instance  = None

    def __new__(cls, host=None, user=None, password=None, database=None, port=3306):
        if cls._global_instance is None:
            cls._global_instance = super(MongoDB, cls).__new__(cls)
            cls._global_instance._connect()
            print("Created MongoDB instance")
        return cls._global_instance

    def _connect(self):
        try:
            uri = "mongodb+srv://admin:admin123@cluster0.a75ng2y.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            self.client = MongoClient(uri, server_api=ServerApi('1'))
            self.client.admin.command('ping')
            self.db = self.client['pdfchatbotDB']
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise
    
    def _retry_on_failure(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ Operation failed: {e}. Retrying after reconnect...")
            try:
                self._connect()
                return func(*args, **kwargs)
            except Exception as retry_e:
                print(f"❌ Retry also failed: {retry_e}")
                raise

    def insert_one_conver(self, convo_data):
        if(next(self.get_conversation_by_id(convo_data['id']),None) != None):
            print("convo ID already exists reinitializing convo ID")
            return None
        return self._retry_on_failure(self.db.conversation.insert_one, convo_data)

    def insert_onepair_msg(self, msg_data):
        print(msg_data)
        return self._retry_on_failure(self.db.message.insert_one, msg_data)

    def get_conversation(self, user_id):
        return self._retry_on_failure(
            lambda: self.db.conversation.find({"user_id": user_id}).sort("timestamp", -1)
        )

    def get_conversation_by_id(self, conver_id):
        return self._retry_on_failure(
            lambda: self.db.conversation.find({"id": conver_id}).limit(1)
        )

    def get_messages(self, conver_id):
        return self._retry_on_failure(
            lambda: self.db.message.find({"conversation_id": conver_id}).sort("timestamp", 1)
        )

    def del_all_conversation(self):
        return self._retry_on_failure(self.db.conversation.delete_many, {})

    def update_conversation_timestamp(self, conversation_id: str, timestamp: datetime):
        """Update the timestamp of a conversation."""
        self.db.conversation.update_one(
            {"id": conversation_id},
            {"$set": {"timestamp": timestamp}}
        )

class MySqlDB:
    _global_instance = None

    def __new__(cls, host=None, user=None, password=None, database=None, port=3306):
        if cls._global_instance is None:
            cls._global_instance = super(MySqlDB, cls).__new__(cls)
            cls._global_instance.connection = cls._connect_db_instance()
            print("✅ Created MySqlDB instance")
        return cls._global_instance

    @staticmethod
    def _connect_db_instance():
        try:
            connection = pymysql.connect(
                host='chatbot-mysql-db.c5g0yaowcv8w.ap-southeast-1.rds.amazonaws.com',
                user='admin',
                password='ilikeNLP',
                database='nlp_chatbot_mysql',
                port=3306,
                cursorclass=pymysql.cursors.DictCursor
            )
            print("✅ Connected to MySQL")
            return connection
        except pymysql.MySQLError as e:
            print(f"❌ Connection Error: {e}")
            return None

    def _reconnect(self):
        self.connection = self._connect_db_instance()

    def execute_query(self, query):
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(query)
                    print(f"✅ Query executed successfully:\n{query}")
                    return True
            except pymysql.MySQLError as e:
                print(f"⚠️ Query error on attempt {attempt + 1}: {e}")
                self._reconnect()
        return False

    def execute_select_one_query(self, query, params):
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone()
            except pymysql.MySQLError as e:
                print(f"⚠️ Select query error on attempt {attempt + 1}: {e}")
                self._reconnect()
        return None

    def execute_insert_query(self, query, params):
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute(query, params)
                    self.connection.commit()
                    print("✅ Inserted row successfully.")
                    return cursor.rowcount
            except pymysql.MySQLError as e:
                print(f"⚠️ Insert query error on attempt {attempt + 1}: {e}")
                self.connection.rollback()
                self._reconnect()
        return 0
            

                
if __name__ == "__main__":
    mySqlDb = MySqlDB()
    # # query = """CREATE TABLE users (
    # #             userId CHAR(36) PRIMARY KEY,
    # #             email VARCHAR(255) NOT NULL UNIQUE,
    # #             username VARCHAR(255) NOT NULL,
    # #             password VARCHAR(255) NOT NULL,
    # #             creation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # #         );
    # #         """
    # # query = 'ALTER TABLE users RENAME TO user_accounts;'
    # # mySqlDb.execute_query(query)
    # # mySqlDb.insert_user("liangzlau@gmail.com","loopZi","password")  
    # email = 'liangzlau@gmail.com'  
    # result = mySqlDb.execute_select_one_query("SELECT * FROM user_accounts WHERE email = %s", (email,))
    # print(result['email'])
