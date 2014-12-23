#!/usr/bin/python

import sys
from gi.repository import GObject, Gdk
from app import EverGnomeApp
from model.db_helper import clean_cache
from model.user_helper import delete_user_data

sys.path.append('model')
sys.path.append('util')

def handle_commands():
  if args.removeuserdata:
    delete_user_data()
    sys.exit(0)
  if args.cleancache:
    clean_cache()
    sys.exit(0)

if __name__ == '__main__':

  parser = EverGnomeApp.create_arg_parser()
  args = parser.parse_args()

  handle_commands()

  app = EverGnomeApp(args)
  
  GObject.threads_init()
  Gdk.threads_enter()

  exit_status = app.run(None)
  
  Gdk.threads_leave()

  sys.exit(exit_status)