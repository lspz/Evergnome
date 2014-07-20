from dateutil.relativedelta import relativedelta
from datetime import datetime
import time
import calendar
import math

def evernote_time_to_str(evernote_timestamp):
  # huh? implement more inteligent string. E.g: if lastime is today then just show date, else show num day
  return time.strftime('%H:%M:%S', evernote_time_to_local_struct_time(evernote_timestamp)) 

def evernote_time_to_local_struct_time(evernote_timestamp):
  return time.localtime(evernote_timestamp / 1000)

def evernote_time_to_local_datetime(evernote_timestamp):
  return datetime.fromtimestamp(evernote_timestamp/1000)

def local_datetime_to_evernote_time(local_datetime):
  return calendar.timegm(local_datetime.timetuple()) * 1000

def get_time_diff_desc(time1, time2):
  delta = relativedelta(time1, time2)
  if delta.years > 0:
    return str(delta.years) + 'y ago'
  if delta.months > 0:
    return str(delta.months) + 'm ago'
  weeks = int(math.floor(delta.days / 7))
  if weeks > 0:
    return str(weeks) + 'w ago'
  if delta.days > 0:
    return str(delta.days) + 'd ago'
  if delta.hours > 0:
    return str(delta.hours) + 'h ago'
  if delta.minutes > 0: 
    return str(delta.minutes) + 'm ago'
  return 'just now'