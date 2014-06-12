import time

def evernote_time_to_str(evernote_timestamp):
  # huh? implement more inteligent string. E.g: if lastime is today then just show date, else show num day
  return time.strftime('%H:%M:%S', evernote_time_to_local(evernote_timestamp)) 

def evernote_time_to_local(evernote_timestamp):
  return time.localtime(evernote_timestamp / 1000)
