from model.data_models import *
from model import db_helper

class LocalStore:
  # huh? Probably should not make this public and should make a getter/accessor
  notes = {}
  notes_by_guid = {}
  notebooks = {}
  notebooks_by_guid = {}
  tags = {}
  tags_by_guid = {}
  resources = {}
  resources_by_guid = {}

  db = None

  def __init__(self, db_path):
    self.db = db_helper.init_db(db_path)

  # huh? This could be heavy to load everything up front
  def load(self):
    for notebook in Notebook.select():
      self.add_notebook(notebook)
    for note in Note.select():
      self.add_note(note)
    for resource in Resource.select():
      self.add_resource(resource)
    for tag in Tag.select():
      self.add_tag(tag)

  def add_note(self, note):
    self.notes[note.id] = note
    if note.guid is not None:
      self.notes_by_guid[note.guid] = note

  def add_notebook(self, notebook):
    self.notebooks[notebook.id] = notebook
    if notebook.guid is not None:
      self.notebooks_by_guid[notebook.guid] = notebook

  def add_tag(self, tag):
    self.tags[tag.id] = tag
    if tag.guid is not None:
      self.tags_by_guid[tag.guid] = tag

  def add_resource(self, resource):
    self.resources[resource.id] = resource
    if resource.guid is not None:
      self.resources_by_guid[resource.guid] = resource

  def delete_note(self, note):
    if note.id in self.notes:
      del self.notes[note.id]
    if note.guid in self.notes_by_guid:
      del self.notes_by_guid[note.guid]

  def delete_notebook(self, notebook):
    if notebook.id in self.notebooks:
      del self.notebooks[notebook.id]
    if notebook.guid in self.notebooks_by_guid:
      del self.notebooks_by_guid[notebook.guid]

  def delete_tag(self, tag):
    if tag.id in self.tags:
      del self.tags[tag.id]
    if tag.guid in self.tags_by_guid:
      del self.tags_by_guid[tag.guid]