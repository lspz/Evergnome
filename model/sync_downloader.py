from data_models import *

# Purpose: Download and apply changes from server to local db

class SyncDownloaderBase:
  
  def __init__(self, class_type, sync_result):
    self._db_class = class_type 
    self.sync_result = sync_result 

  def process(self, data):
    pass # To be overriden

  def _has_conflict(self, db_obj, api_obj):
    return db_obj.object_status != ObjectStatus.SYNCED

  def _handle_conflict(self, db_obj, api_obj):
    self.sync_result.conflict_list.append((db_obj, api_obj))
  
# This deals with expunged object
class SyncDeleter(SyncDownloaderBase):

  def __init__(self, class_type, sync_result, recursive=False):
    SyncDownloaderBase.__init__(self, class_type, sync_result)
    self._recursive = recursive

  def process(self, data):
    if isinstance(data, basestring):
      guid = data
    else: # huh? Assume that we pass evernote api obj 
      guid = data.guid
    query = self._db_class.select().where(self._db_class.guid==guid)  # huh? bulk load this
    if query.exists():
      db_obj = query.get()
      print 'Sync : Delete %s %s' % (self._db_class.__name__, db_obj.guid)
      if self._has_conflict(db_obj, None):
        self._handle_conflict(db_obj, None)
        return
      self._deleted_list.append(db_obj)
      db_obj.delete_instance(recursive=self._recursive)
    # huh? handle else?

class SyncUpdater(SyncDownloaderBase):

  def __init__(self, class_type, notestore, authtoken, sync_result):
    SyncDownloaderBase.__init__(self, class_type, sync_result)
    self._notestore = notestore
    self._authtoken = authtoken

  def _do_update(self, db_obj, api_obj):
    db_obj.assign_from_api(api_obj)
    db_obj.save()

  def process(self, api_obj):
    query = self._db_class.select().where(self._db_class.guid==api_obj.guid)  # huh? bulk load this
    if not query.exists():
      print 'Sync #%d: New %s %s' % (api_obj.updateSequenceNum, self._db_class.__name__, api_obj.guid)
      db_obj = self._db_class()
      self.sync_result.added_list.append(db_obj)
      self._do_update(db_obj, api_obj)
    else:
      print 'Sync #%d: Update %s %s' % (api_obj.updateSequenceNum, self._db_class.__name__, api_obj.guid)
      db_obj = query.get()
      if api_obj.updateSequenceNum > db_obj.usn:
        if self._has_conflict(db_obj, api_obj):
          self._handle_conflict(db_obj, api_obj)
          return
        self._do_update(db_obj, api_obj)

class NoteUpdater(SyncUpdater):
  def __init__(self, notestore, authtoken, sync_result):
    SyncUpdater.__init__(self, Note, notestore, authtoken, sync_result)

  def _has_conflict(self, db_obj, api_obj):
    return SyncUpdater._has_conflict(self, db_obj, api_obj) or (db_obj.updated_time > api_obj.updated)

  def _do_update(self, db_obj, api_obj):
    if api_obj.content is None: 
      api_obj = self._notestore.getNote(self._authtoken, api_obj.guid, True,  False,  False, False) 
    SyncUpdater._do_update(self, db_obj, api_obj)
    self._update_tags(db_obj, api_obj)
    db_obj.maintain_sync_snapshot()

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
  def __init__(self, notestore, authtoken, sync_result):
    SyncUpdater.__init__(self, Resource, notestore, authtoken, sync_result)

  def _do_update(self, db_obj, api_obj):
    SyncUpdater._do_update(self, db_obj, api_obj)
    # Load attachment later on lazyly
    if not api_obj.attributes.attachment:
      resource_data = self._notestore.getResourceData(self._authtoken, api_obj.guid)
      db_obj.assign_from_bin(resource_data)
      db_obj.save()