from peewee import SqliteDatabase
from data_models import *
from user_helper import get_db_path

ALL_TABLE = [UserInfo, SyncState, Notebook, Note, Resource, Tag, TagLink]
SYNCABLE_MODEL = [Notebook, Note, Resource, Tag, TagLink]

def recreate_schema():
  for table in ALL_TABLE:
    if not table.table_exists():
      table.create_table()

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

def clean_cache():
  init_db(user_helper.get_db_path())
  for model in SYNCABLE_MODEL:
    query = model.delete().where(model.object_status != ObjectStatus.SYNCED)
    count = query.execute() 
    print 'Deleted ' + str(count) + ' ' + model.__name__

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
