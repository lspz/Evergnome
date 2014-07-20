from data_models import *

class LocalSyncProcess:
  
  def __init__(self, class_type, conflict_list):
    self._db_class = class_type 
    self._conflict_list = conflict_list # Tuple of (db object, api object)

  def _has_conflict(self, db_obj, api_obj):
    return db_obj.object_status != ObjectStatus.SYNCED

  def _handle_conflict(self, db_obj, api_obj):
    self._conflict_list.append((db_obj, api_obj))
  
# This deals with expunged object
class LocalSyncDeleter(LocalSyncProcess):

  def __init__(self, class_type, conflict_list, deleted_list, recursive=False):
    LocalSyncProcess.__init__(self, class_type, conflict_list)
    self._deleted_list = deleted_list
    self._recursive = recursive

  def process(self, data):
    if isinstance(data, basestring):
      guid = data
    else: # huh? Assume that we pass evernote api obj 
      guid = data.guid
    query = self._db_class.select().where(self._db_class.guid==guid)  # huh? bulk load this
    if query.exists():
      db_obj = query.get()
      if self._has_conflict(db_obj, None):
        self._handle_conflict(db_obj, None)
        return
      self._deleted_list.append(db_obj)
      db_obj.delete_instance(recursive=self._recursive)
    # huh? handle else?

class LocalSyncUpdater(LocalSyncProcess):

  def __init__(self, class_type, notestore, devtoken, conflict_list, added_list):
    LocalSyncProcess.__init__(self, class_type, conflict_list)
    self._notestore = notestore
    self._devtoken = devtoken
    self._added_list = added_list

  def _do_update(self, db_obj, api_obj):
    db_obj.assign_from_api(api_obj)
    db_obj.save()

  def process(self, api_obj):
    query = self._db_class.select().where(self._db_class.guid==api_obj.guid)  # huh? bulk load this
    if not query.exists():
      db_obj = self._db_class()
      self._added_list.append(db_obj)
      self._do_update(db_obj, api_obj)
    else:
      db_obj = query.get()
      if api_obj.updateSequenceNum > db_obj.usn:
        if self._has_conflict(db_obj, api_obj):
          self._handle_conflict(db_obj, api_obj)
          return
        self._do_update(db_obj, api_obj)

class LocalNoteUpdater(LocalSyncUpdater):
  def __init__(self, notestore, devtoken, conflict_list, added_list):
    LocalSyncUpdater.__init__(self, Note, notestore, devtoken, conflict_list, added_list)

  def _has_conflict(self, db_obj, api_obj):
    return LocalSyncUpdater._has_conflict(self, db_obj, api_obj) or (db_obj.updated_time > api_obj.updated)

  def _do_update(self, db_obj, api_obj):
    if api_obj.content is None: 
      api_obj = self._notestore.getNote(self._devtoken, api_obj.guid, True,  False,  False, False) 
    LocalSyncUpdater._do_update(self, db_obj, api_obj)
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

class LocalResourceUpdater(LocalSyncUpdater):
  def __init__(self, notestore, devtoken, conflict_list, added_list):
    LocalSyncUpdater.__init__(self, Resource, notestore, devtoken, conflict_list, added_list)

  def _do_update(self, db_obj, api_obj):
    LocalSyncUpdater._do_update(self, db_obj, api_obj)
    # Load attachment later on lazyly
    if not api_obj.attributes.attachment:
      resource_data = self._notestore.getResourceData(self._devtoken, api_obj.guid)
      db_obj.assign_from_bin(resource_data)
      db_obj.save()