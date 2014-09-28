from gi.repository import GObject
from evernote.edam.error.ttypes import EDAMUserException, EDAMSystemException
from evernote.edam.notestore.ttypes import SyncChunkFilter#NoteFilter, NotesMetadataResultSpec
from evernote.api.client import EvernoteClient
from consts import EvernoteProcessStatus, MAX_ENTRIES, CONSUMER_KEY, CONSUMER_SECRET
from data_models import *
from local_sync_process import *
from view.authwebview import AuthWebView
from model import error_helper

DUMMY_CALLBACK_URL = 'redirect-to-evergnome.com'

class SyncResult:
  conflict_list = None
  added_list = None
  updated_list = None
  deleted_list = None

class EvernoteHandler(GObject.GObject):
  _notestore = None
  _debug = False
  auth_user = None
  last_sync_result = None
  is_authenticated = False


  __gsignals__ = {
    'auth_started': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'sync_started': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'sync_progress': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    'sync_ended': (GObject.SIGNAL_RUN_FIRST, None, (int, str)),
    'edam_error': (GObject.SIGNAL_RUN_FIRST, None, (int, str)),

    'download_resource_started': (GObject.SIGNAL_RUN_FIRST, None, ()),
    'download_resource_ended': (GObject.SIGNAL_RUN_FIRST, None, (int, str))
  }

  def __init__(self, app, debug=False, sandbox=True, devtoken=None):
    GObject.GObject.__init__(self)
    self.app = app
    self._debug = debug
    self._devtoken = devtoken

    auth_token = UserInfo.get_singleton().auth_token if self._devtoken is None else self._devtoken
    self.client = EvernoteClient(
      token=auth_token, # Can be None
      consumer_key=CONSUMER_KEY,
      consumer_secret=CONSUMER_SECRET,
      sandbox=sandbox
      )

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
    print 'auth_token: ' 
    print self.client.token  
    self._notestore = self.client.get_note_store()
    self._save_user_info()
    self.is_authenticated = True

  def _save_user_info(self):
    if not UserInfo.select().limit(1).exists():
      print 'Saving user info..'
      userstore = self.client.get_user_store()
      auth_user = userstore.getUser() 
      # print auth_users
      user_info = UserInfo.get_singleton()
      user_info.username = auth_user.username
      user_info.name = auth_user.name
      user_info.email = auth_user.email
      user_info.auth_token = self.client.token
      user_info.save()

  def sync(self):
    try:
      if not self.is_authenticated:
        self.authenticate()
        if not self.is_authenticated:
          return

      self.emit('sync_started')
      with self.app.db.transaction(): # Auto transaction handling
        self._do_sync()
        self.emit('sync_ended', EvernoteProcessStatus.SUCCESS, '')
    except (EDAMUserException, EDAMSystemException) as e:
      print e
      self.emit('edam_error', e.errorCode, '')
      self.emit('sync_ended', EvernoteProcessStatus.SYNC_ERROR, error_helper.get_edam_error_msg(e.errorCode))
      # show_message_dialog(error_helper.get_edam_error_msg(errorcode), Gtk.MessageType.ERROR, Gtk.ButtonsType.OK)

    except IOError as e:
      self.emit('sync_ended', EvernoteProcessStatus.SYNC_ERROR, 'Connection Error.')
    except Exception as e:
      self.emit('sync_ended', EvernoteProcessStatus.SYNC_ERROR, ' ')
      print e
      # if self._debug:
        # raise e
      # else:
        # print e


  def download_resource(self, resource_db_obj):
    try:
      self.emit('download_resource_started')
      resource_data = self.notestore.getResourceData(self.auth_token, resource_db_obj.guid)
      resource_db_obj.assign_from_bin(resource_data)
      resource_db_obj.save()
      self.app.db.commit()
      self.emit('download_resource_ended', EvernoteProcessStatus.SUCCESS, resource_db_obj.guid)
    except Exception, e:
      print e
      self.emit('download_resource_ended', EvernoteProcessStatus.RESOURCE_ERROR, resource_db_obj.guid)

  def _do_sync(self):
    syncstate_db_obj = SyncState.get_singleton()
    syncstate_api = self.notestore.getSyncState(self.client.token)

    last_update_count = syncstate_db_obj.update_count

    if (syncstate_db_obj.update_count>0) and (syncstate_api.fullSyncBefore>syncstate_db_obj.sync_time):
      self._delete_everything()
      last_update_count = 0
    if syncstate_api.updateCount == syncstate_db_obj.update_count: 
      print 'already updated..'
      return
    elif syncstate_api.updateCount < syncstate_db_obj.update_count:
      raise Exception('usn mismatch')
    
    conflict_list = []
    added_list = []
    deleted_list = []
    syncchunk = self._get_filtered_sync_chunk_from_notestore(last_update_count)

    # huh? double check these
    self._update_counter = 0
    self.total_update = syncchunk.updateCount - last_update_count

    tag_updater = LocalSyncUpdater(Tag, self.notestore, self.client.token, conflict_list, added_list)
    notebook_updater = LocalSyncUpdater(Notebook, self.notestore, self.client.token, conflict_list, added_list)
    note_updater = LocalNoteUpdater(self.notestore, self.client.token, conflict_list, added_list)
    resource_updater = LocalResourceUpdater(self.notestore, self.client.token, conflict_list, added_list)

    # Order is important
    self._process_list(tag_updater, syncchunk.tags)    
    self._process_list(notebook_updater, syncchunk.notebooks)    
    self._process_list(note_updater, syncchunk.notes)    
    self._process_list(resource_updater, syncchunk.resources)   

    note_deleter = LocalSyncDeleter(Note, conflict_list, deleted_list, recursive=True)
    notebook_deleter = LocalSyncDeleter(Notebook, conflict_list, deleted_list)
    tag_deleter = LocalSyncDeleter(Tag, conflict_list, deleted_list)

    self._process_list(note_deleter, syncchunk.expungedNotes)    
    self._process_list(notebook_deleter, syncchunk.expungedNotebooks)    
    self._process_list(tag_deleter, syncchunk.expungedTags)    

    syncstate_db_obj.sync_time = syncchunk.currentTime 
    syncstate_db_obj.update_count = syncchunk.updateCount
    syncstate_db_obj.save()

    self.last_sync_result = SyncResult()
    self.last_sync_result.added_list = added_list
    # These are not used atm
    self.last_sync_result.conflict_list = conflict_list
    self.last_sync_result.deleted_list = deleted_list 

  def _process_list(self, processor, obj_list):
    if obj_list is not None:
      for api_obj in obj_list:
        self._update_progress()
        processor.process(api_obj) 

  def _delete_everything(self):
    pass

  def _update_progress(self):
    self._update_counter += 1
    msg = 'Syncing update {:d} of {:d}'.format(self._update_counter, self.total_update)
    self.emit('sync_progress', msg)

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
      self._notestore = self.client.get_note_store()  
    return self._notestore

  notestore = property(_get_notestore) 


  # def authenticate(self):
  #   if self.is_authenticated:
  #     return True

  #   self.emit('auth_started')

  #   try:
  #     if self.client.token is None:
  #       self.perform_oauth()
  #     else:
  #       self.finalize_auth()

  #     self.emit('auth_ended', EvernoteProcessStatus.SUCCESS)

  #     return True
    
  #   except Exception, e:
  #     self.emit('auth_ended', EvernoteProcessStatus.AUTH_ERROR)
  #     print e
  #     return False

