from data_models import *

# Purpose: Download and apply changes from server to local db

class SyncDownloaderBase:
  
  def __init__(self, localstore, db_class, sync_result):
    self._localstore = localstore
    self._db_class = db_class 
    self.sync_result = sync_result 

  def process(self, data):
    pass # To be overriden

  def _has_conflict(self, db_obj, api_obj):
    return db_obj.object_status != ObjectStatus.SYNCED

  def _handle_conflict(self, db_obj, api_obj):
    self.sync_result.conflict_list.append((db_obj, api_obj))

    # To be implemented by subclass
  def _get_db_obj(self, guid):
    return None
  
# This deals with expunged object
class SyncDeleter(SyncDownloaderBase):

  def __init__(self, localstore, db_class, sync_result, recursive=False):
    SyncDownloaderBase.__init__(self, localstore, db_class, sync_result)
    self._recursive = recursive

  def process(self, data):
    if isinstance(data, basestring):
      guid = data
    else: # Assume that we pass evernote api obj 
      guid = data.guid
    db_obj = self._get_db_obj(guid)  # huh? bulk load this
    if db_obj is not None:
      print 'Sync : Delete %s %s' % (self._db_class.__name__, db_obj.guid)
      if self._has_conflict(db_obj, None):
        self._handle_conflict(db_obj, None)
        return
      self._deleted_list.append(db_obj)
      self._delete_db_obj(db_obj)
      db_obj.delete_instance(recursive=self._recursive)
    # huh? handle else?

  # To be imlemented by subclass
  def _delete_db_obj(self, db_obj):
    pass

class NoteDeleter(SyncDeleter):
  def __init__(self, localstore, sync_result):
    SyncDeleter.__init__(self, localstore, Note, sync_result, recursive=True)

  def _get_db_obj(self, guid):
    return self._localstore.notes_by_guid.get(guid)

  def _delete_db_obj(self, db_obj):
    self._localstore.delete_note(db_obj)

class NotebookDeleter(SyncDeleter):
  def __init__(self, localstore, sync_result):
    SyncDeleter.__init__(self, localstore, Notebook, sync_result)

  def _get_db_obj(self, guid):
    return self._localstore.notebooks_by_guid.get(guid)

  def _delete_db_obj(self, db_obj):
    self._localstore.delete_notebook(db_obj)

class TagDeleter(SyncDeleter):
  def __init__(self, localstore, sync_result):
    SyncDeleter.__init__(self, localstore, Tag, sync_result)

  def _get_db_obj(self, guid):
    return self._localstore.tags_by_guid.get(guid)

  def _delete_db_obj(self, db_obj):
    self._localstore.delete_tag(db_obj)

class SyncUpdater(SyncDownloaderBase):

  def __init__(self, localstore, db_class, notestore, authtoken, sync_result):
    SyncDownloaderBase.__init__(self, localstore, db_class, sync_result)
    self._notestore = notestore
    self._authtoken = authtoken

  def _do_update(self, db_obj, api_obj):
    db_obj.assign_from_api(api_obj)
    db_obj.save()

  def process(self, api_obj):
    db_obj = self._get_db_obj(api_obj.guid)
    if db_obj is None:
      print 'Sync #%d: New %s %s' % (api_obj.updateSequenceNum, self._db_class.__name__, api_obj.guid)
      db_obj = self._db_class()
      self.sync_result.added_list.append(db_obj)
      self._do_update(db_obj, api_obj)
      self._add_db_obj(db_obj)
    else:
      print 'Sync #%d: Update %s %s' % (api_obj.updateSequenceNum, self._db_class.__name__, api_obj.guid)
      if api_obj.updateSequenceNum > db_obj.usn:
        if self._has_conflict(db_obj, api_obj):
          self._handle_conflict(db_obj, api_obj)
          return
        self._do_update(db_obj, api_obj)

  # To be implemented by subclass
  def _add_db_obj(self, db_obj):
    pass


class TagUpdater(SyncUpdater):
  def __init__(self, localstore, notestore, authtoken, sync_result):
    SyncUpdater.__init__(self, localstore, Tag, notestore, authtoken, sync_result)

  def _get_db_obj(self, guid):
    return self._localstore.tags_by_guid.get(guid)

  def _add_db_obj(self, db_obj):
    self._localstore.add_tag(db_obj)

class NotebookUpdater(SyncUpdater):
  def __init__(self, localstore, notestore, authtoken, sync_result):
    SyncUpdater.__init__(self, localstore, Notebook, notestore, authtoken, sync_result)

  def _get_db_obj(self, guid):
    return self._localstore.notebooks_by_guid.get(guid)

  def _add_db_obj(self, db_obj):
    self._localstore.add_notebook(db_obj)

class NoteUpdater(SyncUpdater):
  def __init__(self, localstore, notestore, authtoken, sync_result):
    SyncUpdater.__init__(self, localstore, Note, notestore, authtoken, sync_result)

  def _has_conflict(self, db_obj, api_obj):
    return SyncUpdater._has_conflict(self, db_obj, api_obj) or (db_obj.updated_time > api_obj.updated)

  def _do_update(self, db_obj, api_obj):
    if api_obj.content is None: 
      api_obj = self._notestore.getNote(self._authtoken, api_obj.guid, True,  False,  False, False) 
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

  def _get_db_obj(self, guid):
    return self._localstore.notes_by_guid.get(guid)

  def _add_db_obj(self, db_obj):
    self._localstore.add_note(db_obj)

class ResourceUpdater(SyncUpdater):
  def __init__(self, localstore, notestore, authtoken, sync_result):
    SyncUpdater.__init__(self, localstore, Resource, notestore, authtoken, sync_result)

  def _do_update(self, db_obj, api_obj):
    SyncUpdater._do_update(self, db_obj, api_obj)
    # Load attachment later on lazyly
    if not api_obj.attributes.attachment:
      resource_data = self._notestore.getResourceData(self._authtoken, api_obj.guid)
      db_obj.assign_from_bin(resource_data)
      db_obj.save()

  def _get_db_obj(self, guid):
    return self._localstore.resources_by_guid.get(guid)

  def _add_db_obj(self, db_obj):
    self._localstore.add_resource(db_obj)     