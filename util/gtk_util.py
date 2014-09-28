import os
import mimetypes 
from gi.repository import Gtk, Gio

def show_message_dialog(msg, message_type, buttons_type):
  flags = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.USE_HEADER_BAR
  dialog = Gtk.MessageDialog(None, flags, message_type, buttons_type, msg)
  response = dialog.run()
  dialog.destroy()
  return response

def create_image_button(icon_name, label='', on_click=None, size=Gtk.IconSize.BUTTON, toggle=False):
  image = Gtk.Image()
  image.set_from_icon_name(icon_name, size)
  
  if toggle:
    button = Gtk.ToggleButton()
  else: 
    button = Gtk.Button()
  
  button.set_label(label)
  button.set_image(image)
  button.set_property('always_show_image', True)
  #button.set_relief(Gtk.ReliefStyle.NONE)
  if on_click != None:
    button.connect("toggled" if toggle else "clicked", on_click)

  return button

# huh? implement
def get_mime_icon_name(filename):
  default_icon = 'gtk-file'
  mime = mimetypes.guess_type(filename)[0]
  if mime is None:
    return default_icon
  icon = Gio.content_type_get_icon(mime)
  icon_theme = Gtk.IconTheme.get_default()
  names = icon.get_names()
  for name in names:
    if icon_theme.has_icon(name):
      return name
  return default_icon
  # print mime
  # print icon
  # print icon.get_names()
  # icon_info = icon_theme.choose_icon(icon.get_names(), Gtk.IconSize.MENU, Gtk.IconLookupFlags.FORCE_SVG)
  # print icon_info
  # print icon_info.get_filename()
  # return icon_info.get_display_name()
  # return icon.get_names()[0]
  # ext = os.path.splitext(filename)[1].lower()
  # if ext in ['.jpg', '.jpeg', '.png', 'gif', 'svg']:
  #   return 'gnome-mime-image'
  # if ext in ['.avi', '.mkv']:
  #   return 'gnome-mime-video'
  # if ext in ['.txt']:
  #   return 'gnome-mime-text'
  # if ext in ['.tar', '.zip', '.tar.gz', '.7z']:
  #   return 'gnome-package' 
  # if ext in ['.xls', '.xlsx', '.ods']:
  #   return 'office-spreadsheet'
  # if ext in ['.doc', '.docx', '.odf']:
  #   return 'office-document'
  # if ext == '.html':
  #   return 'html'