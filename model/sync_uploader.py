from data_models import *
from evernote.edam.type import ttypes

# Purpose: Upload and apply changes from local db to server
# Dirty means has been modified but not pushed to server yet

class SyncUploaderBase:

  _db_class = None # To be overriden
  
  def __init__(self, notestore, authtoken,sync_result):
    self.sync_result = sync_result
    self._notestore = notestore
    self._authtoken = authtoken
    self._dirty_objects = None

  def process(self, db_obj):
    if db_obj.object_status == ObjectStatus.CREATED:
      api_obj = self._create_object(db_obj)
      self._update_new_guid(db_obj, api_obj)
      self._update_usn(db_obj, api_obj.updateSequenceNum)
      db_obj.object_status = ObjectStatus.SYNCED
      print 'Sync #%d: New (upload) %s %s' % (api_obj.updateSequenceNum, self._db_class.__name__, api_obj.guid)
    elif db_obj.object_status == ObjectStatus.UPDATED:
      new_usn = self._update_object(db_obj)
      self._update_usn(db_obj, new_usn)
      db_obj.object_status = ObjectStatus.SYNCED
      print 'Sync #%d: Update (upload) %s %s' % (new_usn, self._db_class.__name__, db_obj.guid)
    db_obj.save()
    self.after_upload(db_obj)

  def _update_new_guid(self, db_obj, api_obj):
    if db_obj.guid != api_obj.guid:
      db_obj.guid = api_obj.guid
    
  def _update_usn(self, db_obj, new_usn):
    # if db_obj.usn != (new_usn-1):
      # huh? handle properly
      # print 'Out of sync. guid: %s, db: %d, server: %d' % (db_obj.guid, db_obj.usn, new_usn) 
    db_obj.usn = new_usn
    self.sync_result.last_update_count = new_usn

  def get_dirty_objects(self):
    if self._dirty_objects is None:
      self._dirty_objects = self._db_class.select().where(self._db_class.object_status != ObjectStatus.SYNCED)
    return self._dirty_objects

  # Returns new api_obj
  def _create_object(self, db_obj):
    return None

  # Returns new USN
  def _update_object(self, db_obj):
    return None

  def after_upload(self, db_obj):
    pass

class TagSyncUploader(SyncUploaderBase):

  _db_class = Tag

  def _create_api_object(self, db_obj):
    tag = ttypes.Tag()
    tag.name = db_obj.name
    if db_obj.parent_tag is not None:
      tag.parentGuid = db_obj.parent_tag.guid
    return tag   

  def _create_object(self, db_obj):
    return self._notestore.createTag(self._authtoken, self._create_api_object(db_obj))

  def _update_object(self, db_obj):
    return self._notestore.updateTag(self._authtoken, self._create_api_object(db_obj))


class NotebookSyncUploader(SyncUploaderBase):

  _db_class = Notebook

  def _create_api_object(self, db_obj):
    notebook = ttypes.Notebook()
    notebook.name = db_obj.name
    if db_obj.is_default:
      notebook.defaultNotebook = True
    return notebook   

  def _create_object(self, db_obj):
    return self._notestore.createNotebook(self._authtoken, self._create_api_object(db_obj))

  def _update_object(self, db_obj):
    return self._notestore.updateNotebook(self._authtoken, self._create_api_object(db_obj))


class NoteSyncUploader(SyncUploaderBase):

  _db_class = Note 

  def _create_api_object(self, db_obj):
    note = ttypes.Note()
    note.guid = db_obj.guid
    note.title = db_obj.title

    # huh? We need to get new usn for new resource so that we can update local rsc's usn
    # and SyncState.usn

    if db_obj.snapshot is not None:
      if db_obj.content != db_obj.snapshot.content:
        note.content = db_obj.content
      if db_obj.notebook != db_obj.snapshot.notebook:
        note.notebookGuid = db_obj.notebook.guid
      if db_obj.created_time != db_obj.snapshot.created_time:
        note.created = db_obj.created_time
      if db_obj.updated_time != db_obj.snapshot.updated_time:
        note.updated = db_obj.updated_time
      if db_obj.deleted_time != db_obj.snapshot.deleted_time:
        note.deleted = db_obj.deleted_time
      if db_obj.is_active != db_obj.snapshot.is_active:
        note.active = db_obj.is_active
      if db_obj.has_tags_modified():
        note.tagGuids = [tag.guid for tag in db_obj.tags]
      if db_obj.has_resources_modified():
        note.resources = self.get_resource_list(db_obj)
    else:
      note.content = db_obj.content
      note.notebookGuid = db_obj.notebook.guid
      note.tagGuids = [tag.guid for tag in db_obj.tags]
      note.resources = self.get_resource_list(db_obj)
      note.created = db_obj.created_time
      note.updated = db_obj.updated_time
      note.deleted = db_obj.deleted_time
      note.active = db_obj.is_active
    return note   

  def get_resource_list(self, note):
    result = []
    for resource in note.resources:
      api_obj = ttypes.Resource()
      api_obj.guid = resource.guid
      api_obj.noteGuid = resource.guid
      api_obj.mime = resource.mime
      api_obj.attributes = ttypes.ResourceAttributes()
      api_obj.attributes.fileName = resource.filename
      api_obj.attributes.attachment = resource.is_attachment
      api_obj.data = ttypes.Data()
      # huh? Tried only including content for modified one. But server complains 
      api_obj.data.size = resource.get_content_size()
      api_obj.data.bodyHash = resource.get_hash_in_bin()
      if resource.object_status != ObjectStatus.SYNCED:
        api_obj.data.body = resource.get_content_data()
      print 'rscX: %s, filename: %s, usn: %d ' % (resource.guid, resource.filename, resource.usn)
      result.append(api_obj)
    return result

  def _create_object(self, db_obj):
    note = self._notestore.createNote(self._authtoken, self._create_api_object(db_obj))
    return note.updateSequenceNum

  def _update_object(self, db_obj):
    note = self._notestore.updateNote(self._authtoken, self._create_api_object(db_obj))
    if note.resources is not None:
      for res in note.resources:
        print 'rsc: %s, filename: %s, usn: %d' % (res.guid, res.attributes.fileName, res.updateSequenceNum)
    return note.updateSequenceNum

  def after_upload(self, db_obj):
    db_obj.maintain_sync_snapshot()

    Resource.update(object_status=ObjectStatus.SYNCED).where(Resource.note==db_obj, Resource.object_status==ObjectStatus.CREATED).execute()
    Resource.delete().where(Resource.note==db_obj, Resource.object_status==ObjectStatus.DELETED).execute()
    
    TagLink.update(object_status=ObjectStatus.SYNCED).where(TagLink.note==db_obj, TagLink.object_status==ObjectStatus.CREATED).execute()
    TagLink.delete().where(TagLink.note==db_obj, TagLink.object_status==ObjectStatus.DELETED).execute()