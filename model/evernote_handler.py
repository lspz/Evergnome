from gi.repository import GObject, GLib
from evernote.edam.error.ttypes import EDAMUserException, EDAMSystemException
from evernote.edam.notestore.ttypes import SyncChunkFilter#NoteFilter, NotesMetadataResultSpec
from evernote.api.client import EvernoteClient
from model.data_models import *
from model import error_helper
from model.sync_downloader import *
from model.sync_uploader import *
from model.consts import EvernoteProcessStatus, MAX_ENTRIES, CONSUMER_KEY, CONSUMER_SECRET
from view.authwebview import AuthWebView
from util import gtk_util

DUMMY_CALLBACK_URL = 'redirect-to-evergnome.com'

class SyncResult:
  def __init__(self):
    self.conflict_list = [] # Tuple of (db object, api object)
    self.added_list = []
    self.updated_list = []
    self.deleted_list = []
    self.last_update_count = None


class EvernoteHandler(GObject.GObject):
  _localstore = None
  _notestore = None
  _debug = False
  auth_user = None
  sync_result = None
  is_authenticated = False
  on_edam_error = None

  __gsignals__ = {
    'auth_started': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'sync_started': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'sync_progress': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    'sync_ended': (GObject.SIGNAL_RUN_FIRST, None, (int, str)),
    'edam_error': (GObject.SIGNAL_RUN_FIRST, None, (int, str)),
    'download_resource_started': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'download_resource_ended': (GObject.SIGNAL_RUN_FIRST, None, (int, str, str))
  }

  def __init__(self, localstore, debug=False, sandbox=True, devtoken=None):
    GObject.GObject.__init__(self)
    self._localstore = localstore
    self._debug = debug
    self._devtoken = devtoken

    print 'Initiating evernote client. debug=%s sandbox=%s' % (debug, sandbox)

    auth_token = UserInfo.get_singleton().auth_token if self._devtoken is None else self._devtoken
    self.client = EvernoteClient(
      token=auth_token, # Can be None
      consumer_key=CONSUMER_KEY,
      consumer_secret=CONSUMER_SECRET,
      sandbox=sandbox
      )

  def download_resource(self, resource_db_obj):
    try:
      self.emit('download_resource_started')
      print 'Downloading resource %s - %s' % (resource_db_obj.filename, resource_db_obj.guid)
      resource_data = self.notestore.getResourceData(self.client.token, resource_db_obj.guid)
      if resource_data is not None:
        resource_db_obj.assign_from_bin(resource_data)
        resource_db_obj.save()
        self._localstore.db.commit()
      self.emit('download_resource_ended', EvernoteProcessStatus.SUCCESS, resource_db_obj.guid, '')
    except Exception, e:
      print e
      self.emit('download_resource_ended', EvernoteProcessStatus.RESOURCE_ERROR, resource_db_obj.guid, 'Download error.')
  
  def authenticate(self):
    self.emit('auth_started')
    if self.client.token is None:
      self.perform_oauth()
    else:
      self.finalize_auth()

  def perform_oauth(self):
    request_token = self.client.get_request_token(DUMMY_CALLBACK_URL) 
    self.oauth_token_secret = request_token['oauth_token_secret']
    auth_url = self.client.get_authorize_url(request_token)
    self.authview = AuthWebView(auth_url, DUMMY_CALLBACK_URL, self._oauth_after_redirect)
    self.authview.run()

  def _oauth_after_redirect(self, token, verifier):
    self.authview.destroy()
    self.client.get_access_token(token, self.oauth_token_secret, verifier) # This will set client.token
    self.finalize_auth()

  def finalize_auth(self):
    print 'Authenticating, token: ' + self.client.token  
    self._notestore = self.client.get_note_store()
    self._save_user_info()
    self.is_authenticated = True

  def _save_user_info(self):
    if not UserInfo.select().limit(1).exists():
      print 'Saving user info..'
      userstore = self.client.get_user_store()
      auth_user = userstore.getUser() 
      user_info = UserInfo.get_singleton()
      user_info.username = auth_user.username
      user_info.name = auth_user.name
      user_info.email = auth_user.email
      user_info.auth_token = self.client.token
      user_info.save()

  def sync(self):
    if self._debug:
      self._do_sync()
      return

    try:
      self._do_sync()
    except (EDAMUserException, EDAMSystemException) as e:
      if self.on_edam_error is not None:
        GLib.idle_add(self.on_edam_error, e.errorCode)
      self.emit('sync_ended', EvernoteProcessStatus.SYNC_ERROR, error_helper.get_edam_error_msg(e.errorCode))
    except IOError as e:
      self.emit('sync_ended', EvernoteProcessStatus.SYNC_ERROR, 'Please check your connection.')
    except Exception as e:
      self.emit('sync_ended', EvernoteProcessStatus.SYNC_ERROR, ' ')
      print e

  def _do_sync(self):
    if not self.is_authenticated:
      self.authenticate()
      if not self.is_authenticated:
        return

    self.emit('sync_started')
    self.sync_result = SyncResult()

    with self._localstore.db.transaction(): # Auto transaction handling
      self.download_changes()
      
    # Unlike downloading changes, we do one transaction per objects (see _process_objects_to_upload)
    # As sending transaction to server cannot be rolledback, hence we want
    # to ensure local db is as closely synced to server in case of failure 
    
    # huh? Bypass upload for REAL data for now. This is scary
    # if self.app.config.sandbox:
    self.upload_changes()

    SyncState.get_singleton().save()

    self.emit('sync_ended', EvernoteProcessStatus.SUCCESS, '')

    # huh? do we need to repeat _do_sync again in case there are even newer updates

  def download_changes(self):
    syncstate_db_obj = SyncState.get_singleton()
    syncstate_api = self.notestore.getSyncState(self.client.token)
    
    if (syncstate_db_obj.update_count>0) and (syncstate_api.fullSyncBefore>syncstate_db_obj.sync_time):
      self._delete_everything()
      syncstate_db_obj.update_count = 0
    if syncstate_api.updateCount == syncstate_db_obj.update_count: 
      print 'No new changes from server'
      return
    elif syncstate_api.updateCount < syncstate_db_obj.update_count:
      raise Exception('usn mismatch')

    # huh? double check these
    syncchunk = self._get_filtered_sync_chunk_from_notestore(syncstate_db_obj.update_count)

    self._download_counter = 0
    self._total_download = syncchunk.updateCount - syncstate_db_obj.update_count

    tag_updater = TagUpdater(localstore=self._localstore, notestore=self.notestore, authtoken=self.client.token, sync_result=self.sync_result)
    notebook_updater = NotebookUpdater(localstore=self._localstore, notestore=self.notestore, authtoken=self.client.token, sync_result=self.sync_result)
    note_updater = NoteUpdater(localstore=self._localstore, notestore=self.notestore, authtoken=self.client.token, sync_result=self.sync_result)
    resource_updater = ResourceUpdater(localstore=self._localstore, notestore=self.notestore, authtoken=self.client.token, sync_result=self.sync_result)

    # Order is important
    self._process_download_list(tag_updater, syncchunk.tags)    
    self._process_download_list(notebook_updater, syncchunk.notebooks)    
    self._process_download_list(note_updater, syncchunk.notes)    
    self._process_download_list(resource_updater, syncchunk.resources)   

    note_deleter = NoteDeleter(localstore=self._localstore, sync_result=self.sync_result)
    notebook_deleter = NotebookDeleter(localstore=self._localstore, sync_result=self.sync_result)
    tag_deleter = TagDeleter(localstore=self._localstore, sync_result=self.sync_result)

    self._process_download_list(note_deleter, syncchunk.expungedNotes)    
    self._process_download_list(notebook_deleter, syncchunk.expungedNotebooks)    
    self._process_download_list(tag_deleter, syncchunk.expungedTags)    

    # huh? might need to redownload syncchunk to get updated usn after upload
    syncstate_db_obj = SyncState.get_singleton()
    syncstate_db_obj.sync_time = syncchunk.currentTime 
    syncstate_db_obj.update_count = syncchunk.updateCount

  def _process_download_list(self, downloader, obj_list):
    if obj_list is not None:
      for api_obj in obj_list:
        self._update_download_progress()
        downloader.process(api_obj) 

  def _update_download_progress(self):
    self._download_counter += 1
    msg = 'Syncing update {:d} of {:d}'.format(self._download_counter, self._total_download)
    self.emit('sync_progress', msg)

  def upload_changes(self):
    self._upload_counter = 0

    tag_uploader = TagSyncUploader(self.notestore, self.client.token, self.sync_result)
    notebook_uploader = NotebookSyncUploader(self.notestore, self.client.token, self.sync_result)
    note_uploader = NoteSyncUploader(self.notestore, self.client.token, self.sync_result)

    # huh? Debug
    print 'Testing upload. NOT A REAL RUN'
    self._total_upload = tag_uploader.get_dirty_objects().wrapped_count()
    self._total_upload += notebook_uploader.get_dirty_objects().wrapped_count()  
    self._total_upload += note_uploader.get_dirty_objects().wrapped_count()
    print 'Total objects to upload: ' + str(self._total_upload)

    # self._process_objects_to_upload(tag_uploader)
    # self._process_objects_to_upload(notebook_uploader)
    # self._process_objects_to_upload(note_uploader)
    # if self.sync_result.last_update_count is not None:
    #   SyncState.get_singleton().update_count = self.sync_result.last_update_count
    
  def _process_objects_to_upload(self, uploader):
    with self._localstore.db.transaction():
      for db_obj in uploader.get_dirty_objects():
        self._update_upload_progress()
        uploader.process(db_obj)

  def _update_upload_progress(self):
    self._upload_counter += 1
    msg = 'Uploading change {:d} of {:d}'.format(self._upload_counter, self._total_upload)
    self.emit('sync_progress', msg)

  def _delete_everything(self):
    pass

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

    return self.notestore.getFilteredSyncChunk(
      self.client.token, 
      last_update_count,
      MAX_ENTRIES,
      syncchunk_filter)

  def _get_notestore(self):
    if self._notestore is None:
      if not self.is_authenticated:
        self.authenticate()
      self._notestore = self.client.get_note_store()  
    return self._notestore

  def get_default_notebook(self):
    query = Notebook.select().where(Notebook.is_default==True)
    if query.exists():
      return query.get()
    
    if not self.is_authenticated:
      self.authenticate()
    
    api_obj = self.notestore.getDefaultNotebook(self.client.token)
    db_obj = Notebook.select().where(Notebook.guid==api_obj.guid).get()
    db_obj.is_default = True
    db_obj.save()
    return db_obj

  notestore = property(_get_notestore) 

