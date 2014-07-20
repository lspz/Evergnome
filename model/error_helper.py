from evernote.edam.error.ttypes import EDAMErrorCode

# huh? add more
def get_edam_error_msg(errorcode):
  if errorcode == EDAMErrorCode.INVALID_AUTH:
    return 'Authentication Token Invalid'
  if errorcode == EDAMErrorCode.AUTH_EXPIRED:
    return 'Authentication Expired'
  return 'Unknown Error. Error Code: ' + str(errorcode)