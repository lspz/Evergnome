from evernote.edam.type import ttypes as Types
from evernote.edam.notestore.ttypes import SyncChunkFilter#NoteFilter, NotesMetadataResultSpec
from evernote.api.client import EvernoteClient
from data_models import *
from consts import EvernoteProcessStatus

DEV_TOKEN = 'S=s1:U=8eaf4:E=14da8d27c19:C=1465121501f:P=1cd:A=en-devtoken:V=2:H=56ce86a4c75fdd0f2f655707b57bec95' 
CONSUMER_KEY = 'louis-parengkuan'
CONSUMER_SECRET = '9e1109d8913fbc87'
MAX_ENTRIES = 100000

class SyncObjectProcess:
  _db_class = None
  _local_objects = None  # dict with guid as key and _db_class instance as val

  _conflict_list = [] # Tuple of (db object, api object)
  
  def __init__(self, class_type, local_objects, conflict_list):
    self._db_class = class_type 
    self._local_objects = local_objects
    self._conflict_list = conflict_list

  def _has_conflict(self, db_obj, api_obj):
    return db_obj.object_status != ObjectStatus.SYNCED

  def _handle_conflict(self, db_obj, api_obj):
    self._conflict_list.append((db_obj, api_obj))
  
class SyncDeleter(SyncObjectProcess):
  _deleted_list = None
  _recursive = False
  
  def __init__(self, class_type, local_objects, conflict_list, deleted_list, recursive=False):
    SyncObjectProcess.__init__(self, class_type, local_objects, conflict_list)
    self._deleted_list = deleted_list
    self._recursive = recursive

  def process(self, data):
    if isinstance(data, basestring):
      guid = data
    else: # huh? Assume that we pass evernote api obj 
      guid = data.guid
    db_obj = self._local_objects.get(guid)
    if db_obj is not None:
      if self._has_conflict(db_obj, None):
        self._handle_conflict(db_obj, None)
        return
      del self._local_objects[db_obj.guid]
      self._deleted_list.append(db_obj)
      db_obj.delete_instance(recursive=self._recursive)
    # huh? handle else?

class SyncUpdater(SyncObjectProcess):
  _notestore = None 
  _added_list = None
  _updated_list = None

  def __init__(self, class_type, local_objects, notestore, conflict_list, added_list, updated_list):
    SyncObjectProcess.__init__(self, class_type, local_objects, conflict_list)
    self._notestore = notestore
    self._added_list = added_list
    self._updated_list = updated_list

  def _do_update(self, db_obj, api_obj):
    db_obj.assign_from_api(api_obj)
    db_obj.object_status = ObjectStatus.SYNCED
    db_obj.save()

  def process(self, api_obj):
    db_obj = self._local_objects.get(api_obj.guid)
    if db_obj is None:
      db_obj = self._db_class()
      self._added_list.append(db_obj)
      self._local_objects[db_obj.guid] = db_obj
      self._do_update(db_obj, api_obj)
    else:
      if api_obj.updateSequenceNum > db_obj.usn:
        if self._has_conflict(db_obj, api_obj):
          self._handle_conflict(db_obj, api_obj)
          return
        self._updated_list.append(db_obj)
        self._do_update(db_obj, api_obj)

class NoteUpdater(SyncUpdater):
  def __init__(self, local_objects, notestore, conflict_list, added_list, updated_list):
    SyncUpdater.__init__(self, Note, local_objects, notestore, conflict_list, added_list, updated_list)

  def _has_conflict(self, db_obj, api_obj):
    return SyncUpdater._has_conflict(self, db_obj, api_obj) or (db_obj.updated_time > api_obj.updated)

  def _do_update(self, db_obj, api_obj):
    if api_obj.content is None: 
      api_obj = self._notestore.getNote(DEV_TOKEN, api_obj.guid, True,  False,  False, False) 
    SyncUpdater._do_update(self, db_obj, api_obj)
    self._update_tags(db_obj, api_obj)

  def _update_tags(self, db_obj, api_obj):
    db_tag_guids = []
    for tag_link in db_obj.tag_links:
      if tag_link.tag.guid not in api_obj.tagGuids:
        tag_link.delete_instance()
      else:
        db_tag_guids.append(tag_link.tag.guid)  
    if api_obj.tagGuids is not None: 
      for api_tag_guid in api_obj.tagGuids:
        if api_tag_guid not in db_tag_guids:
          tag = Tag.select().where(Tag.guid==api_tag_guid)
          new_link = TagLink.create(note=db_obj, tag=tag)

class ResourceUpdater(SyncUpdater):
  def __init__(self, local_objects, notestore, conflict_list, added_list, updated_list):
    SyncUpdater.__init__(self, Resource, local_objects, notestore, conflict_list, added_list, updated_list)

  def _do_update(self, db_obj, api_obj):
    SyncUpdater._do_update(self, db_obj, api_obj)
    if not api_obj.attributes.attachment:
      resource_data = self._notestore.getResourceData(DEV_TOKEN, api_obj.guid)
      db_obj.save_resource_data(resource_data)
      db_obj.save()

class SyncResult:
  conflict_list = None
  added_list = None
  updated_list = None
  deleted_list = None

class EvernoteHandler:
  auth_user = None
  _notestore = None
  _localstore = None
  _events = None

  def __init__(self, localstore, events):
    self._localstore = localstore
    self._events = events

  def authenticate(self):
    self._events.emit('auth_started')
    print 'authenticating..'
    try:
      client = EvernoteClient(token=DEV_TOKEN, sandbox=True)
      userstore = client.get_user_store()
      self._notestore = client.get_note_store()
      self.auth_user = userstore.getUser()
      print 'authenticated as ' + self.auth_user.username
      self._events.emit('auth_ended', EvernoteProcessStatus.SUCCESS)
    except Exception, e:
      print e
      self._events.emit('auth_ended', EvernoteProcessStatus.AUTH_ERROR)

  def sync(self):
    if self.auth_user is None:
      self.authenticate()
      if self.auth_user is None:
        return
    self._events.emit('sync_started')
    # try:
    #   self._do_sync()
    #   self._events.emit('sync_ended', EvernoteProcessStatus.SUCCESS)
    # except Exception, e:
    #   print e
    #   self._events.emit('sync_ended', EvernoteProcessStatus.SYNC_ERROR)
    self._do_sync()
    self._events.emit('sync_ended', EvernoteProcessStatus.SUCCESS)

  def _do_sync(self):
    syncstate_db_obj = self._localstore.syncstate
    syncstate_api = self._notestore.getSyncState(DEV_TOKEN)

    last_update_count = syncstate_db_obj.update_count

    if (syncstate_db_obj.update_count>0) and (syncstate_api.fullSyncBefore>syncstate_db_obj.sync_time):
      self._delete_everything()
      last_update_count = 0
    if syncstate_api.updateCount == syncstate_db_obj.update_count: 
      print 'already updated..'
      return
    elif syncstate_api.updateCount < syncstate_db_obj.update_count:
      raise Exception('usn mismatch')
    
    # huh? pass lists
    conflict_list = []
    added_list = []
    updated_list = []
    deleted_list = []
    syncchunk = self._get_filtered_sync_chunk_from_notestore(last_update_count)

    # huh? double check these
    self._update_counter = 0
    self.total_update = syncchunk.updateCount - last_update_count

    tag_updater = SyncUpdater(Tag, self._localstore.tags, self._notestore, conflict_list, added_list, updated_list)
    notebook_updater = SyncUpdater(Notebook, self._localstore.notebooks, self._notestore, conflict_list, added_list, updated_list)
    note_updater = NoteUpdater(self._localstore.notes, self._notestore, conflict_list, added_list, updated_list)
    resource_updater = ResourceUpdater(self._localstore.resources, self._notestore, conflict_list, added_list, updated_list)

    # Order is important
    self._process_list(tag_updater, syncchunk.tags)    
    self._process_list(notebook_updater, syncchunk.notebooks)    
    self._process_list(note_updater, syncchunk.notes)    
    self._process_list(resource_updater, syncchunk.resources)   

    note_deleter = SyncDeleter(Note, self._localstore.notes, conflict_list, deleted_list, recursive=True)
    notebook_deleter = SyncDeleter(Notebook, self._localstore.notebooks, conflict_list, deleted_list)
    tag_deleter = SyncDeleter(Tag, self._localstore.tags, conflict_list, deleted_list)

    self._process_list(note_deleter, syncchunk.expungedNotes)    
    self._process_list(notebook_deleter, syncchunk.expungedNotebooks)    
    self._process_list(tag_deleter, syncchunk.expungedTags)    

    syncstate_db_obj.sync_time = syncchunk.currentTime 
    syncstate_db_obj.update_count = syncchunk.updateCount
    syncstate_db_obj.save()

    syncresult = SyncResult()
    syncresult.conflict_list = conflict_list
    syncresult.added_list = added_list
    syncresult.updated_list = updated_list
    syncresult.deleted_list = deleted_list
    self._localstore.last_sync_result = syncresult

    self._localstore.commit()

  def _process_list(self, processor, obj_list):
    if obj_list is not None:
      for api_obj in obj_list:
        processor.process(api_obj) 

  def _delete_everything(self):
    pass

  def _update_progress(self):
    self._update_counter += 1
    msg = 'Syncing update {:d} of {:d}'.format(self._update_counter, self.total_update)
    self._events.emit('sync_progress', msg)

  def _get_filtered_sync_chunk_from_notestore(self, last_update_count):
    print 'fetch from ' + str(last_update_count)
      # Might need more later
    syncchunk_filter = SyncChunkFilter(
      includeNotes=True,
      includeNotebooks=True,
      includeNoteResources=True,
      includeNoteAttributes=False, 
      includeTags=True,
      includeSearches=False,
      includeResources=True,
      includeExpunged=True,
      includeNoteApplicationDataFullMap=False,
      includeResourceApplicationDataFullMap=False,
      includeNoteResourceApplicationDataFullMap=False,
      requireNoteContentClass='')

    return self._notestore.getFilteredSyncChunk(
      DEV_TOKEN, 
      last_update_count,
      MAX_ENTRIES,
      syncchunk_filter)

  def _combine_list(self, lists):
    result = []
    for list_src in lists:
      result.extend(list_src)
    return result




 