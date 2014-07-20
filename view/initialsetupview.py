from gi.repository import Gtk

class InitialSetupView(Gtk.Dialog):

  def __init__(self, app):
    Gtk.Dialog.__init__(self, modal=False, use_header_bar=False)
    self.app = app
    self.add_button('Exit', Gtk.ResponseType.REJECT)
    btn_next = self.add_button('Next', Gtk.ResponseType.ACCEPT)
    btn_next.grab_focus()
    # self.connect('response', self._on_response)

    welcome_label = Gtk.Label()
    welcome_label.set_visible(True  )
    welcome_label.set_markup('<span font="13">Welcome to EverGnome.\nClick next to Authenticate. </span>')
    self.get_content_area().pack_start(welcome_label, True, True, 0)
    self.spinner = Gtk.Spinner()
    self.spinner.set_visible(False)
    self.get_action_area().pack_end(self.spinner, True, True, 0)
    self.set_size_request(400, 200)
    self.set_resizable(False)
    self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
    self.set_no_show_all(True)
    self.show_all()

  def _on_response(self, sender, response):
    # if response == Gtk.ResponseType.ACCEPT:
    #   self.spinner.set_visible(True)
    #   self.spinner.start()
    self.close()
    # pass