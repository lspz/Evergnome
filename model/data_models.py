import os, binascii, shutil, mimetypes
from lxml.html import html5parser
from gi.repository import GObject
from datetime import datetime
from peewee import *
from model import consts, user_helper
from util import time_util, file_util, enml_converter, misc_util

db_proxy = Proxy()

class ObjectStatus:
  CREATED = 'C'
  UPDATED = 'U'
  DELETED = 'D'  # Need to ensure most views dont display DELETED objects
  SYNCED = 'S' 

class SyncModelPubSub(GObject.GObject):
  __gsignals__ = {
    'updated': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'deleted': (GObject.SIGNAL_RUN_FIRST, None, ())
    }
  def __init__(self, model):
    GObject.GObject.__init__(self)
    self.model = model

class BaseModel(Model):
  class Meta:
    database = db_proxy

class BaseSingletonModel(BaseModel):
  _singleton = None
  
  @classmethod
  def get_singleton(cls):
    if cls._singleton is None:
      query = cls.select().limit(1)
      if query.exists():
        cls._singleton = query.get()
      else:
        cls._singleton = cls()
    return cls._singleton    
  
class UserInfo(BaseSingletonModel):
  username = CharField()
  # Fields can be null depending on what server gave us based on permission
  name = CharField(null=True)
  email = CharField(null=True)
  auth_token = CharField(null=True) 

class SyncState(BaseSingletonModel):
  update_count = IntegerField(default=0)
  sync_time = IntegerField(default=0)  # server time

# Base class for syncable evernote data type
class SyncModel(BaseModel):
  guid = CharField(null=True, index=True)
  usn = IntegerField(default=0)
  object_status = CharField(default=ObjectStatus.CREATED)

  def __init__(self, **kwargs):
    BaseModel.__init__(self, **kwargs)
    self.event = SyncModelPubSub(self)

  def save(self, *args, **kwargs):
    BaseModel.save(self, *args, **kwargs)
    self.event.emit('updated')

  def mark_updated(self):
    self.updated_time = time_util.local_datetime_to_evernote_time(datetime.now())
    if self.object_status == ObjectStatus.SYNCED:
      self.object_status = ObjectStatus.UPDATED
  
  # Use this instead of delete_instance to ensure deletion is synced
  def delete_sync(self):
    if self.object_status == ObjectStatus.SYNCED:
      self.object_status = ObjectStatus.DELETED
      self.save()
    else:
      self.delete_instance()

  def delete_instance(self, *args, **kwargs):
    BaseModel.delete_instance(self, *args, **kwargs)
    self.event.emit('deleted')  

  def update_from_api(self, api_object):
    self.usn = api_object.updateSequenceNum
    self.object_status = ObjectStatus.SYNCED

  def assign_from_api(self, api_object):
    self.guid = api_object.guid
    self.update_from_api(api_object)

  def get_display_name(self):
    return ''

class Notebook(SyncModel):
  name = CharField()
  is_default = BooleanField(default=False)

  def update_from_api(self, api_object):
    super(Notebook, self).update_from_api(api_object)
    self.name = api_object.name

  def get_display_name(self):
    return self.name + ' (' + str(self.notes.where(Note.deleted_time == None).count()) + ')'

class BaseNote(SyncModel):
  title = CharField()
  content = CharField()
  created_time = IntegerField(default=0)  # huh? why don't we store them as date?
  deleted_time = IntegerField(null=True)
  updated_time = IntegerField(default=0)
  is_active = BooleanField(null=True)

class SyncedNoteSnapshot(BaseNote):
  # Declare this separately from Note.notebook as we want to use different related_name
  notebook = ForeignKeyField(Notebook) 

class Note(BaseNote):
  notebook = ForeignKeyField(Notebook, related_name='notes')
  snapshot = ForeignKeyField(SyncedNoteSnapshot, null=True)  
  _embedded_medias_by_hash = None
  _embedded_medias_by_path = None
  _html = None
  _content_preview = None
  _last_update_desc = None

  def save(self, *args, **kwargs):
    # Order is important. 
    self._save_html()    # Save before cache is cleared
    self._reset_cache()  # Reset cache to ensure uptodate-ness before notification
    SyncModel.save(self, *args, **kwargs) 
    self._notify_update_to_links()
  
  def delete_instance(self, *args, **kwargs):
    SyncModel.delete_instance(self, *args, **kwargs)
    self._notify_update_to_links()

  def update_from_api(self, api_object):
    super(Note, self).update_from_api(api_object)
    self.title = api_object.title
    self.content = api_object.content
    self.created_time = api_object.created
    self.deleted_time = api_object.deleted
    self.updated_time = api_object.updated
    self.is_active = api_object.active
    self.notebook = Notebook.select().where(Notebook.guid==api_object.notebookGuid).get()
    self._reset_cache()

  def has_tag(self, ids):
    if len(ids) == 0:
      return False
    for tag in self.tags:
      if tag.od in ids:
        return True
    return False

  def has_tags_modified(self):
    return self.tag_links.where(TagLink.object_status != ObjectStatus.SYNCED).exists()

  def has_resources_modified(self):
    return self.resources.where(Resource.object_status != ObjectStatus.SYNCED).exists()

  def is_deleted(self):
    return self.deleted_time is not None;
    
  def _reset_cache(self):
    self._embedded_medias_by_hash = None
    self._embedded_medias_by_path = None
    self._html = None
    self._content_preview = None
    self._last_update_desc = None

  def _save_html(self):
    if self._html is None:
      return
    enml, resource_hashes = enml_converter.HTMLToENML(self.html, self.embedded_medias_by_path)
    self.content = enml
    for resource in self.resources.where(Resource.is_attachment==False, Resource.object_status!=ObjectStatus.DELETED):  
      if resource.hash not in resource_hashes:
        resource.delete_sync()
    self.html = None

  def _set_html(self, html):
    self._html = html

  def _get_html(self):
    if (self._html is None) and (self.content is not None):
      self._html = enml_converter.ENMLToHTML(self.content.encode('UTF-8'), self.embedded_medias_by_hash)
    return self._html

  def _create_snapshot(self):
    return SyncedNoteSnapshot.create(
      guid=self.guid,
      usn=self.usn,
      object_status=self.object_status,
      title=self.title,
      content=self.content,
      created_time=self.created_time,
      deleted_time=self.deleted_time,
      updated_time=self.updated_time,
      is_active=self.is_active,
      notebook=self.notebook
      )

  def maintain_sync_snapshot(self):
    if self.object_status != ObjectStatus.SYNCED:
      return
    if self.snapshot is not None:
      if self.snapshot.usn < self.usn:
        self.snapshot.delete_instance()
      else:
        return
    self.snapshot = self._create_snapshot()
    self.save()

  def _get_embedded_medias_by_hash(self):
    if self._embedded_medias_by_hash is None:
      self._embedded_medias_by_hash = {}
      for media in self.resources.where(Resource.is_attachment==False):
        self._embedded_medias_by_hash[media.hash] = media 
    return self._embedded_medias_by_hash   

  def _get_embedded_medias_by_path(self):
    if self._embedded_medias_by_path is None:
      self._embedded_medias_by_path = {}
      for media in self.resources.where(Resource.is_attachment==False):
        self._embedded_medias_by_path[media.localpath] = media 
    return self._embedded_medias_by_path   

  def _get_tags(self):
    return Tag.select().join(TagLink).where(TagLink.note==self)

  def get_display_name(self):
    return self.title

  def get_resource_path(self):
    dir_name = str(self.guid) if self.guid is not None else 'noguid'
    return os.path.join(os.path.expanduser(user_helper.get_resource_path()), dir_name)

  def _get_attachments(self):
    # huh?
    return self.resources.where(Resource.is_attachment==True)

  def _get_content_preview(self):
    if self._content_preview is None:
      doc = html5parser.fromstring(self.content)
      desc = doc.xpath("string()").strip()
      desc = (desc[:38] + '..') if len(desc) > 40 else desc
      self._content_preview = desc.replace('\n', '')
    return self._content_preview

  def _get_last_updated_desc(self):
    if self._last_update_desc is None:
      local_updated_time = time_util.evernote_time_to_local_datetime(self.updated_time)
      self._last_update_desc = time_util.get_time_diff_desc(datetime.now(), local_updated_time)
    return self._last_update_desc
  
  def _notify_update_to_links(self):
    # Notify notebook and tag to update view 
    self.notebook.event.emit('updated')
    for tag_link in self.tag_links:
      tag_link.tag.event.emit('updated')


  attachments = property(_get_attachments)
  html = property(_get_html, _set_html)
  embedded_medias_by_hash = property(_get_embedded_medias_by_hash)
  embedded_medias_by_path = property(_get_embedded_medias_by_path)
  content_preview = property(_get_content_preview)
  last_updated_desc = property(_get_last_updated_desc)
  tags = property(_get_tags)

class Resource(SyncModel):
  note = ForeignKeyField(Note, related_name='resources')
  mime = CharField(null=True)
  hash = CharField(null=True)
  localpath = CharField(null=True)
  filename = CharField(null=True)
  is_attachment = BooleanField(null=True)

  @classmethod
  def create_from_path(cls, note, path, is_attachment=True):
    filename = os.path.split(path)[1]
    ext = os.path.splitext(filename)[1].lower()
    mime = mimetypes.guess_type(path)[0]
    hash = file_util.get_file_hash_hex(path)
    new_resource = cls(note=note, filename=filename, hash=hash, mime=mime, is_attachment=is_attachment)
    new_resource.assign_from_path(path)
    return new_resource

  def delete_instance(self, *args, **kwargs):
    localpath = self.localpath
    SyncModel.delete_instance(self, *args, **kwargs)
    os.remove(localpath)

  def update_from_api(self, api_object):
    super(Resource, self).update_from_api(api_object)
    # we dont update the note here
    self.mime = api_object.mime
    self.hash = binascii.b2a_hex(api_object.data.bodyHash)
    self.filename = api_object.attributes.fileName
    self.is_attachment = False if api_object.attributes.attachment is None else api_object.attributes.attachment  
    self.note = Note.select().where(Note.guid==api_object.noteGuid).get()
    self.localpath = None

  def assign_from_bin(self, data):
    if data is None:
      return
    filename = self.filename if self.filename is not None else self.guid 
    file_path = self._get_unique_resource_path(filename)
    with open(file_path, 'w') as output_file:
      output_file.write(data)
    self.localpath = file_path

  def get_content_data(self):
    if self.localpath is None:
      return None
    with open(self.localpath, 'r') as the_file:
      return the_file.read()

  def get_content_size(self):
    if self.localpath is None:
      return 0
    return os.path.getsize(self.localpath)

  def get_hash_in_bin(self):
    return binascii.a2b_hex(self.hash)

  def assign_from_path(self, file_path):
    filename = os.path.split(file_path)[1]
    new_path = self._get_unique_resource_path(filename)
    shutil.copyfile(file_path, new_path)
    self.localpath = new_path

  def _get_unique_resource_path(self, filename):
    filename = file_util.get_valid_filename(filename)
    resource_path = self.note.get_resource_path()
    if not os.path.exists(resource_path):
      os.makedirs(resource_path)
    return file_util.get_unique_filename(os.path.join(resource_path, filename))

class Tag(SyncModel):
  name = CharField()
  parent_tag = ForeignKeyField('self', null=True, related_name='child_tags')

  def update_from_api(self, api_object):
    super(Tag, self).update_from_api(api_object)
    self.name = api_object.name
    # cant assign parent_tag now
  def get_display_name(self):
    return self.name + ' (' + str(self.tag_links.where(Note.deleted_time==None).count()) + ')'


class TagLink(BaseModel):
  tag = ForeignKeyField(Tag, related_name='tag_links')
  note = ForeignKeyField(Note, related_name='tag_links')
  object_status = CharField(default=ObjectStatus.CREATED)



