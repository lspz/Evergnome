import os
import zipfile
import shutil
from util import file_util
from model.data_models import UserInfo

# ~/.evergnome/resource
# ~/.evergnome/data.db
# ~/.evergnome/archive/<username>

USER_PATH = os.path.expanduser('~/.evergnome/')
RESOURCE_DIR = 'resource'
DB_NAME = 'data.db' 
ARCHIVE_EXT = '.ega'
ARCHIVE_DIR = 'archive'

def get_resource_path():
  return os.path.join(USER_PATH, RESOURCE_DIR)

def get_db_path():
  return os.path.join(USER_PATH, DB_NAME)

def archive_user_data(username=None):
  if username is None:
    username = get_current_username()
  output_filename = file_util.get_unique_filename(username + ARCHIVE_EXT)
  output_path = os.path.join(USER_PATH, ARCHIVE_DIR) 
  if not os.path.exists(output_path):
    os.makedirs(output_path)
  output_path = os.path.join(output_path, output_filename)

  zip_file = zipfile.ZipFile(output_path, mode='w')
  try:
    for root, dirs, files in os.walk(USER_PATH):
      for file in files:
        abspath = os.path.join(root, file)
        relpath = os.path.relpath(abspath, USER_PATH)
        print os.path.dirname(relpath)
        if (os.path.dirname(relpath) != ARCHIVE_DIR):
          zip_file.write(abspath, relpath)
  finally:
    zip_file.close()

# huh? impl!
def delete_user_data(username=None):
  if username is None:
    username = get_current_username()
  shutil.rmtree(get_resource_path())
  os.remove(get_db_path())

def get_current_username():
  return UserInfo.get_singleton().username
