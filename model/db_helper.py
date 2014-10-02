from peewee import SqliteDatabase
from data_models import *

def recreate_schema():
  if not UserInfo.table_exists():
    UserInfo.create_table()
  if not SyncState.table_exists():
    SyncState.create_table()
  if not Notebook.table_exists():
    Notebook.create_table()
  if not Note.table_exists():
    Note.create_table()
  if not SyncedNoteSnapshot.table_exists():
    SyncedNoteSnapshot.create_table()
  if not Tag.table_exists():
    Tag.create_table()
  if not TagLink.table_exists():
    TagLink.create_table()
  if not Resource.table_exists():
    Resource.create_table()

def init_db(path):
  is_first_time = not os.path.exists(path)
  path_dir = os.path.split(path)[0]
  if is_first_time and (not os.path.exists(path_dir)):
    os.makedirs(path_dir)
  db = SqliteDatabase(path, check_same_thread=False, autocommit=True)
  db_proxy.initialize(db)
  if is_first_time:
      recreate_schema()
  return db


# Handle DB connection and caching
# class LocalStore:
  # notebooks = {}
  # notes = {}
  # tags = {}
  # resources = {}
  # syncstate = None



    # self.recreate_schema() # huh? this is temp
    


  # def load(self):
  #   # huh? we probly dont need thsese?
  #   for notebook in Notebook.select():
  #     self.notebooks[notebook.guid] = notebook
  #   for note in Note.select():
  #     self.notes[note.guid] = note
  #   for tag in Tag.select():
  #     self.tags[tag.guid] = tag
  #   for resource in Resource.select():
  #     self.resources[resource.guid] = resource
  #   query = SyncState.select().limit(1)
  #   if query.exists():
  #     self.syncstate = query.get()
  #   else:
  #     self.syncstate = SyncState.create(update_count=0, sync_time=0)    

  # def add_from_api(self, classtype, api_object):
  #   obj = classtype()
  #   obj.assign_from_api(api_object)
  #   obj.save()
    
  #   if classtype == Notebook:
  #     self.notebooks.append(obj)
  #   if classtype == Note:
  #     self.notes.append(obj)
  #   if classtype == Tag:
  #     self.tags.append(obj)
