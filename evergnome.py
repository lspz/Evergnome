#!/usr/bin/python

import sys
from gi.repository import GObject, Gdk
from app import EverGnomeApp

sys.path.append('thirdparty')
sys.path.append('util')

if __name__ == '__main__':

  app = EverGnomeApp()
  
  GObject.threads_init()
  Gdk.threads_enter()

  exit_status = app.run(None)
  
  Gdk.threads_leave()

  sys.exit(exit_status)