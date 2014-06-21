from peewee import *
from os import path
from lxml.html import html5parser
import os
import binascii
import consts

db_proxy = Proxy()

class ObjectStatus:
  CREATED = 'C'
  UPDATED = 'U'
  DELETED = 'D'
  SYNCED = 'S' 

class BaseModel(Model):
  class Meta:
    database = db_proxy

class SyncState(BaseModel):
  update_count = IntegerField()
  sync_time = IntegerField()  # server time

class SyncModel(BaseModel):
  guid = CharField(null=True, index=True)
  usn = IntegerField(null=True, default=0)
  object_status = CharField(default=ObjectStatus.CREATED)
  
  def update_from_api(self, api_object):
    self.usn = api_object.updateSequenceNum
  def assign_from_api(self, api_object):
    self.guid = api_object.guid
    self.object_status = ObjectStatus.SYNCED
    self.update_from_api(api_object)

class Notebook(SyncModel):
  name = CharField()

  def update_from_api(self, api_object):
    super(Notebook, self).update_from_api(api_object)
    self.name = api_object.name

class Note(SyncModel):
  title = CharField()
  content = CharField()
  created_time = IntegerField(default=0)
  deleted_time = IntegerField(null=True)
  updated_time = IntegerField(default=0)
  is_active = BooleanField(null=True)
  notebook = ForeignKeyField(Notebook, related_name='notes')

  # Cached stuff - huh? reset onsave
  _content_preview = None
  _last_update_desc = None

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

  def has_tag(self, id):
    for links in self.tag_links:
      if links.tag.id == id:
        return True
    return False

  def is_deleted(self):
    return self.deleted_time is not None;
    
  def _reset_cache(self):
    self._content_preview = None
    self._last_update_desc = None

  def _get_content_preview(self):
    if self._content_preview is None:
      doc = html5parser.fromstring(self.content)
      desc = doc.xpath("string()").strip()
      desc = (desc[:38] + '..') if len(desc) > 40 else desc
      self._content_preview = desc.replace('\n', '')
    return self._content_preview

  def _get_updated_desc(self):
    return '1d ago'   # huh? implement
  
  content_preview = property(_get_content_preview)
  updated_desc = property(_get_updated_desc)

# Add on delete hook to delete file
class Resource(SyncModel):
  note = ForeignKeyField(Note, related_name='resources')
  mime = CharField(null=True)
  hash = CharField(null=True)
  localpath = CharField(null=True)
  filename = CharField(null=True)
  is_attachment = BooleanField(null=True)

  def update_from_api(self, api_object):
    super(Resource, self).update_from_api(api_object)
    # we dont update the note here
    self.mime = api_object.mime
    self.hash = binascii.b2a_hex(api_object.data.bodyHash)
    self.filename = api_object.attributes.fileName
    self.is_attachment = False if api_object.attributes.attachment is None else api_object.attributes.attachment  
    self.note = Note.select().where(Note.guid==api_object.noteGuid).get()

  def save_resource_data(self, data):
    if data is None:
      return
    if self.filename:
      filename = self.filename # huh? possible duplicate
    else:
      filename = self.guid

    # ~/.evergnome/note-guid/guid
    file_path = path.join(path.expanduser(consts.RESOURCE_PATH), str(self.note.guid))
    if not path.exists(file_path):
      os.makedirs(file_path)

    file_path = path.join(file_path, filename)
    with open(file_path, 'w') as output_file:
      output_file.write(data)

    self.localpath = file_path

  # load lazyly, load inline one upon opening note, else on request
  # def load_data(self, notestore, auth_token):
  #   if self.localpath:
  #     return
  #   api_object = notestore.getResource(auth_token, self.guid, True, False, False, False)
  #   self._download_resource(api_object.data.body)

class Tag(SyncModel):
  name = CharField()
  parent_tag = ForeignKeyField('self', null=True, related_name='child_tags')

  def update_from_api(self, api_object):
    super(Tag, self).update_from_api(api_object)
    self.name = api_object.name
    # cant assign parent_tag now


class TagLink(BaseModel):
  tag = ForeignKeyField(Tag, related_name='tag_links')
  note = ForeignKeyField(Note, related_name='tag_links')

# from peewee import *

# db_proxy = Proxy()

# class BaseModel(Model):
#   class Meta:
#     database = db_proxy

# class SyncState(BaseModel):
#   last_update_count = IntegerField()
#   last_sync = IntegerField() 

# class SyncModel(BaseModel):
#   guid = CharField(null=True, index=True)
#   usn = IntegerField(null=True)
#   def update_from_api(self, api_object):
#     self.usn = api_object.updateSequenceNum
#   def assign_from_api(self, api_object):
#     self.guid = api_object.guid
#     self.update_from_api(api_object)

# class Notebook(SyncModel):
#   name = CharField()

#   def update_from_api(self, api_object):
#     super(Notebook, self).update_from_api(api_object)
#     self.name = api_object.name

# class Note(SyncModel):
#   title = CharField()
#   content = CharField()
#   created = IntegerField()
#   deleted = IntegerField(null=True)
#   updated = IntegerField()
#   active = BooleanField(null=True)
#   notebook = ForeignKeyField(Notebook, related_name='notes')

#   def update_from_api(self, api_object):
#     super(Note, self).update_from_api(api_object)
#     self.title = api_object.title
#     self.content = api_object.content # huh? we only want the en-note element
#     self.created = api_object.created
#     self.deleted = api_object.deleted
#     self.updated = api_object.updated
#     self.active = api_object.active
#     self.notebook = Notebook.select().where(Notebook.guid==api_object.notebookGuid).get()

#   def _get_content_preview(self):
#     return 'Content preview..' # huh? implement
#   def _get_updated_desc(self):
#     return '1d ago'   # huh? implement
  
#   content_preview = property(_get_content_preview)
#   updated_desc = property(_get_updated_desc)


# class Resource(SyncModel):
#   note = ForeignKeyField(Note, related_name='resources')
#   mime = CharField(null=True)
#   localpath = CharField(null=True)
#   filename = CharField(null=True)
#   attachment = BooleanField(null=True)

#   def update_from_api(self, api_object):
#     super(Resource, self).update_from_api(api_object)
#     # we dont update the note here
#     self.mime = api_object.mime
#     self.filename = api_object.attributes.fileName
#     self.attachment = api_object.attributes.attachment
    

#   # load lazyly, load inline one upon opening note, else on request
#   def load_data(self):
#     pass

# class Tag(SyncModel):
#   name = CharField()
#   parent_tag = ForeignKeyField('self', null=True, related_name='child_tags')

#   def update_from_api(self, api_object):
#     super(Tag, self).update_from_api(api_object)
#     self.name = api_object.name
#     # cant assign parent_tag now


# class TagLink(BaseModel):
#   tag = ForeignKeyField(Tag, related_name='tag_links')
#   note = ForeignKeyField(Note, related_name='tag_links')


  # Optional notes attributes
  # subject_date = IntegerField()
  # latitude = DoubleField()
  # longitude = DoubleField()
  # altitude = DoubleField()
  # author = CharField()
  # source_url = CharField()



