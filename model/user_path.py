import os

# ~/.evergnome/resource
# ~/.evergnome/data.db
# ~/.evergnome/archive/<username>

USER_PATH = os.path.expanduser('~/.evergnome/')
RESOURCE_DIR = 'resource'
DB_NAME = 'data.db' 

def get_resource_path():
  return os.path.join(USER_PATH, RESOURCE_DIR)

def get_db_path():
  return os.path.join(USER_PATH, DB_NAME)

def archive_current_user_data(username):
  pass

def unarchive_user_data(username):
  pass