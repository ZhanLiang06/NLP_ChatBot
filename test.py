from src.db_manager.database_access import MongoDB
from datetime import datetime
import uuid
mgr = MongoDB()
# convo_id = "0f9b331e-cb62-4485-ade1-76bd3c4d01fd"
# msg = {
#     "conver_id": convo_id,
#     "content":[
#         {"role":"user","content":"What is this PDF about?","timestamp":datetime.now()},
#         {"role":"assistant","content":"It's about JABIL BootCamp","timestamp":datetime.now()}
#     ],
#     "timestamp":datetime.now()
# }

# mgr.insert_onepair_msg(msg_data=msg)
## that will it return first
curr_convo_data = {
    "id": "str(uuid.uuid4())",
    "title": "new_convo_title.strip()",
    "user_id": "user_info['userId']",  # Add logic to fetch user_id as needed
    "timestamp": datetime.now()  # Add a timestamp or other metadata as needed
}
success_insert_no_dup = mgr.insert_one_conver(curr_convo_data)
while success_insert_no_dup == None:
    curr_convo_data['id'] = str(uuid.uuid4())
    success_insert_no_dup = mgr.insert_one_conver(curr_convo_data)

print(f"{curr_convo_data['id']}")
print(f"{curr_convo_data['title']}")


