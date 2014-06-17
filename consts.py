USER_PATH = '~/.evergnome/'
RESOURCE_PATH = USER_PATH + 'resource'

class EvernoteProcessStatus:
  SUCCESS = 0
  AUTH_ERROR = 1
  SYNC_ERROR = 2

class SelectionIdConstant:
  NONE = -1
  TRASH = -2