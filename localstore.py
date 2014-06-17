from data_models import *

# Handle DB connection and caching
class LocalStore:
  notebooks = {}
  notes = {}
  tags = {}
  resources = {}
  syncstate = None
  
  last_sync_result = None # huh? might need to save this to db later for robust purposes

  def __init__(self, path):
    self._db = SqliteDatabase(path, check_same_thread=False, autocommit=False)
    db_proxy.initialize(self._db)

    # self.recreate_schema() # huh? this is temp
    
  def recreate_schema(self):
    if not SyncState.table_exists():
      SyncState.create_table()
    if not Notebook.table_exists():
      Notebook.create_table()
    if not Note.table_exists():
      Note.create_table()
    if not Tag.table_exists():
      Tag.create_table()
    if not TagLink.table_exists():
      TagLink.create_table()
    if not Resource.table_exists():
      Resource.create_table()

    self._db.commit() 

  def load(self):
    for notebook in Notebook.select():
      self.notebooks[notebook.guid] = notebook
    for note in Note.select():
      self.notes[note.guid] = note
    for resource in Resource.select():
      self.resources[resource.hash] = resource.localpath
    for tag in Tag.select():
      self.tags[tag.guid] = tag
    query = SyncState.select().limit(1)
    if query.exists():
      self.syncstate = query.get()
    else:
      self.syncstate = SyncState.create(update_count=0, sync_time=0)    
      
  def commit(self):
    self._db.commit()

  def rollback(self):
    self._db.rollback()
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
