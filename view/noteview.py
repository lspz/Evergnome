from gi.repository import Gtk, WebKit
from gi.repository import Pango
from gi.repository import Gio
from util.enml import ENMLToHTML
from gi.repository import Pango
import gtkutils as GtkUtils
import os



class NoteView(Gtk.Box):
  edit_mode = False
  current_note = None

  def __init__(self, app):
    Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)
    self._localstore = app.localstore
    self._app = app

    # self._init_actions()
    # self.set_border_width(5)

    self.webview = WebKit.WebView()
    # self.webview.set_border_width(5)
    self.webview.set_margin_left(9)
    self.webview.set_margin_right(9)
    # self.webview.set_margin_bottom(9)
    self.webview.set_margin_top(12)
    self.webview.set_zoom_level(0.9)
    self.webview.get_style_context().add_class('webkit')
    # webview_container = Gtk.Box()
    # webview_container.pack_start(self.webview, True, True, 0)
    # webview_container.get_style_context().add_class('noteview')
    #self.webview.get_settings().set_property('enable-universal-access-from-file-uris', True)

    #self.webview.set_editable(True)

    scrollbox = Gtk.ScrolledWindow()
    scrollbox.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
    scrollbox.add(self.webview)
    scrollbox.set_size_request(400, 400)
    scrollbox.get_style_context().add_class('note-view-scrollbox')
    # scrollbox.set_border_width(3)

    self.btn_edit = GtkUtils.create_image_button('edit-symbolic', ' Edit', on_click=self._on_edit_click, size=Gtk.IconSize.BUTTON)
    self.btn_edit.set_halign(Gtk.Align.END)
    self.btn_edit.set_valign(Gtk.Align.START)
    self.btn_edit.set_margin_top(10)
    self.btn_edit.set_margin_right(10)
    self.btn_edit.get_style_context().add_class('osd')
    self.btn_edit.set_no_show_all(True)
    self.btn_edit.set_visible(False)

    self.header = self._create_header()
    self.overlay = Gtk.Overlay()
    self.overlay.add(scrollbox)
    self.overlay.add_overlay(self.btn_edit)

    eventbox = Gtk.EventBox()
    eventbox.connect('enter-notify-event', self._on_enter_webkit)
    eventbox.connect('leave-notify-event', self._on_leave_webkit)
    eventbox.add(self.overlay)
    # self.header.set_no_show_all(True)
    # self.overlay.set_no_show_all(True)

    self.toolbar = self._create_toolbar()
    self.toolbar.set_visible(False)

    self.note_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    self.note_box.pack_start(self.header, False, False, 0)
    self.note_box.pack_start(self.toolbar, False, False, 0)
    self.note_box.pack_end(eventbox, True, True, 0)

    self.nonote_box = Gtk.Box()
    self.nonote_box.set_size_request(400, 400)

    self.stack = Gtk.Stack()
    self.stack.add_named(self.nonote_box, 'nonote')
    self.stack.add_named(self.note_box, 'note')
    self.stack.set_visible_child_name('nonote')

    self.pack_start(self.stack, True, True, 0)

  def on_note_selected(self, note):
    self.current_note = note
    #content = "<!DOCTYPE en-note SYSTEM ""http://xml.evernote.com/pub/enml2.dtd""><en-note style=""background: #e6e6e6;font-family: 'Helvetica Neue',  Helvetica, Arial, 'Liberation Sans', FreeSans, sans-serif;color: #585957;font-size: 14px;line-height: 1.3;"">  <div style=""height: 40px;"">&nbsp;</div>  <div style=""max-width: 600px;padding: 25px 0px 0px 0px;background-color: #fff;margin: 0 auto;box-shadow: 0 0px 5px rgba(0, 0, 0, 0.2);"">     <div style=""margin: 0px 25px;padding-bottom: 15px;"">      <en-media alt=""Evernote Logo"" type=""image/png"" hash=""4914ced8925f9adcc1c58ab87813c81f""></en-media>        <h1 style=""color: #5fb336;margin: 0;margin-top: 15px;font-size: 20px;font-weight: normal;"">Welcome to Evernote</h1>         <p style=""font-size: 16px;margin: 0px 0px 6px 0px;line-height: 1.4;"">Put everything in one place - your notes, images, documents, web clips and audio notes. Find what you're looking for using our powerful search. Sync makes your notes accessible across your devices.</p>      </div>    <div style=""margin: 0px 25px;font-size: 14px;color: #4d4b47;background-color: #e6f4f6;border: 1px solid #c1e8ec;padding: 0px 15px 8px;clear: both;"">        <h2 style=""font-size: 16px;line-height: 1.25em;padding-top: 8px;margin-bottom: 6px;padding: 0;"">Get Started</h2>        <p style=""margin: 8px 0;""><span style=""font-weight: bold;"">Create a New Note</span><br />Save your ideas, to-do lists, research, meeting notes, and more.</p>         <p style=""margin: 8px 0;""><span style=""font-weight: bold;"">Snap a Photo</span><br />Capture images that you want to remember&mdash;from business cards to wine labels to pictures of your family.</p>         <p style=""margin: 8px 0;""><span style=""font-weight: bold;"">Sync Notes and Find Them Anywhere</span><br />Search for anything, even text within images, on any computer, phone or tablet you use.</p>          <p style=""margin: 8px 0;"">Need more inspiration? Check out our <a href=""http://blog.evernote.com"" style=""text-decoration: none;color: #5fb336;"">Blog</a></p>        <p style=""margin: 8px 0;"">Have more questions? Check out our <a href=""http://evernote.com/getting_started/"" style=""text-decoration: none;color: #5fb336;"">Getting Started Guide &amp; Tutorial</a></p>      </div>    <div style=""margin: 0px 25px;"">         <h2 style=""font-size: 16px;line-height: 1.25em;padding-top: 8px;margin-bottom: 6px;"">Install and use Evernote everywhere</h2>       <ul style=""padding: 0;margin: 0;"">              <li style=""list-style-position: inside;padding-left: 4px;""><a href=""http://evernote.com/evernote/"" style=""text-decoration: none;color: #5fb336;"">Get Evernote</a> on your computer, phone and tablet.</li>              <li style=""list-style-position: inside;padding-left: 4px;"">Install a <a href=""http://evernote.com/webclipper"" style=""text-decoration: none;color: #5fb336;"">Web Clipper</a> into your browser to remember interesting web pages.</li>           <li style=""list-style-position: inside;padding-left: 4px;"">Email notes to your Evernote email address. Find it in your settings.</li>       </ul>     </div>    <div style=""margin: 0px 25px;"">         <h2 style=""font-size: 16px;line-height: 1.25em;padding-top: 8px;margin-bottom: 12px;"">Our products work great together. Try them all!</h2>          <div>             <div style=""width: 100%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;display: block;min-height: 35px;"">                <div style=""width: 50%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;"">                     <a href=""http://evernote.com/evernote/"" style=""text-decoration: none;line-height: 1em;color: #6f6f6f;position: relative; display: block;"">              <en-media alt=""Evernote"" type=""image/png"" hash=""836fc57702fc08596a5b6d74e54b33cc"" style=""position:absolute;top:0;left:0;border-color:transparent;""></en-media>                          <div style=""width: 50%;min-width: 200px;margin: 0 0px 8px 0px;padding-right: 10px;line-height: .8em;margin-left: 34px;"">                            <span style=""display: block;font-size: 14px;margin-bottom: .3em;font-weight: bold;"">Evernote</span>                             <span style=""font-size: 12px;width: auto;"">Remember everything </span>                          </div>                    </a>                  </div>                <div style=""width: 50%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;"">                     <a href=""http://evernote.com/hello/"" style=""text-decoration: none;line-height: 1em;color: #6f6f6f;position: relative; display: block;"">              <en-media alt=""Evernote Hello"" type=""image/png"" hash=""0e2d61050811670832d80ed457203343"" style=""position:absolute;top:0;left:0;border-color:transparent;""></en-media>                       <div style=""width: 50%;min-width: 200px;margin: 0 0px 8px 0px;padding-right: 10px;line-height: .8em;margin-left: 34px;"">                            <span style=""display: block;font-size: 14px;margin-bottom: .3em;font-weight: bold;"">Evernote Hello</span>                           <span style=""font-size: 12px;width: auto;"">Remember people</span>                       </div>                    </a>                  </div>            </div>            <div style=""width: 100%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;display: block;min-height: 35px;"">                <div style=""width: 50%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;"">                     <a href=""http://evernote.com/food/"" style=""text-decoration: none;line-height: 1em;color: #6f6f6f;position: relative; display: block;"">              <en-media alt=""Evernote Food"" type=""image/png"" hash=""908ca278561900d6620da9a8b06ecbaf"" style=""position:absolute;top:0;left:0;border-color:transparent;""></en-media>                         <div style=""width: 50%;min-width: 200px;margin: 0 0px 8px 0px;padding-right: 10px;line-height: .8em;margin-left: 34px;"">                            <span style=""display: block;font-size: 14px;margin-bottom: .3em;font-weight: bold;"">Evernote Food</span>                            <span style=""font-size: 12px;width: auto;"">Preserve your food memories</span>                       </div>                    </a>                  </div>                <div style=""width: 50%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;"">                     <a href=""http://evernote.com/skitch/"" style=""text-decoration: none;line-height: 1em;color: #6f6f6f;position: relative; display: block;"">              <en-media alt=""Skitch"" type=""image/png"" hash=""e9a7b8ccbfaeca2feebc51ccb1faa2b6"" style=""position:absolute;top:0;left:0;border-color:transparent;""></en-media>                          <div style=""width: 50%;min-width: 200px;margin: 0 0px 8px 0px;padding-right: 10px;line-height: .8em;margin-left: 34px;"">                            <span style=""display: block;font-size: 14px;margin-bottom: .3em;font-weight: bold;"">Skitch</span>                           <span style=""font-size: 12px;width: auto;"">Draw attention</span>                        </div>                    </a>                  </div>            </div>            <div style=""width: 100%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;display: block;min-height: 35px;"">                <div style=""width: 50%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;"">                     <a href=""http://evernote.com/clearly/"" style=""text-decoration: none;line-height: 1em;color: #6f6f6f;position: relative; display: block;"">              <en-media alt=""Evernote Clearly"" type=""image/png"" hash=""c7dbb1ce10ff3dfe7c0a485d904d0d23"" style=""position:absolute;top:0;left:0;border-color:transparent;""></en-media>                       <div style=""width: 50%;min-width: 200px;margin: 0 0px 8px 0px;padding-right: 10px;line-height: .8em;margin-left: 34px;"">                            <span style=""display: block;font-size: 14px;margin-bottom: .3em;font-weight: bold;"">Evernote Clearly</span>                             <span style=""font-size: 12px;width: auto;"">Distraction-free reading</span>                          </div>                    </a>                  </div>                <div style=""width: 50%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;"">                     <a href=""http://evernote.com/peek/"" style=""text-decoration: none;line-height: 1em;color: #6f6f6f;position: relative;  display: block;"">              <en-media alt=""Evernote Peek"" type=""image/png"" hash=""950bf3517b1e7f23bc40066853a23f7e"" style=""position:absolute;top:0;left:0;border-color:transparent;""></en-media>                        <div style=""width: 50%;min-width: 200px;margin: 0 0px 8px 0px;padding-right: 10px;line-height: .8em;margin-left: 34px;"">                            <span style=""display: block;font-size: 14px;margin-bottom: .3em;font-weight: bold;"">Evernote Peek</span>                            <span style=""font-size: 12px;width: auto;"">Study smarter</span>                         </div>                    </a>                  </div>            </div>            <div style=""width: 100%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;display: block;min-height: 35px;"">                <div style=""width: 50%;min-width: 200px;float: left;margin: 0 0px 8px 0px;padding-right: 0px;"">                     <a href=""http://evernote.com/penultimate/"" style=""text-decoration: none;line-height: 1em;color: #6f6f6f;position: relative;  display: block;"">              <en-media alt=""Penultimate"" type=""image/png"" hash=""bb54c12582d7d1793fb860ae27fe9daa"" style=""position:absolute;top:0;left:0;border-color:transparent;""></en-media>                       <div style=""width: 50%;min-width: 200px;margin: 0 0px 8px 0px;padding-right: 10px;line-height: .8em;margin-left: 34px;"">                            <span style=""display: block;font-size: 14px;margin-bottom: .3em;font-weight: bold;"">Penultimate</span>                              <span style=""font-size: 12px;width: auto;"">Beautiful digital handwriting</span>                         </div>                    </a>                  </div>            </div>        </div>    </div>    <div style=""margin: 0px 25px;clear: both;padding-bottom: 10px;"">        <h2 style=""font-size: 16px;line-height: 1.25em;padding-top: 8px;margin-bottom: 0;"">Go Premium, Get more</h2>        <p style=""margin-top: 2px;"">Get additional features by upgrading to <a href=""http://evernote.com/premium/"" style=""text-decoration: none;color: #5fb336;"">Evernote Premium</a>.</p>      </div>    <div style=""background: #f5f5f5;min-height: 16px;padding: 1px 30px;text-align: center;border-top: 1px solid #ebebeb;"">          <p style=""color: #747474;line-height: 1.5em;""><a href=""http://blog.evernote.com/"" style=""text-decoration: none;color: #747474;"">Blog</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; <a href=""http://www.evernote.com/market/"" style=""text-decoration: none;color: #747474;"">Market</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; <a href=""https://twitter.com/evernote"" style=""text-decoration: none;color: #747474;"">Twitter</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; <a href=""https://www.facebook.com/evernote"" style=""text-decoration: none;color: #747474;"">Facebook</a></p>      </div>  </div>  <div style=""height: 40px;"">&nbsp;</div></en-note>"
    #html = enml.HTMLOfENML(note.content.encode('UTF-8'))#note.content.encode('UTF-8'))
    if note is None:
      self.stack.set_visible_child_name('nonote')
    else:
      self._set_edit_mode(False)
      self.stack.set_visible_child_name('note') 
      self.text_title.set_text(note.title)
      html = ENMLToHTML(note.content.encode('UTF-8'), self._localstore.resources)
      self.webview.load_string(html, 'text/html', 'UTF-8', 'file://')
    #self.webview.load_string('<html><body><img src="file:///home/louis/.evergnome/resource/1/8bb429f6-4c1b-40de-9cb4-fc5fca6b1818"/></body></html>', 'text/html', 'UTF-8', 'file://')
    #print self.webview.get_uri()


  def _create_header(self):
    self.text_title = Gtk.Entry()
    self.text_title.set_editable(False)
    self.text_title.set_has_frame(False)
    self.text_title.get_style_context().add_class('note-title')
    self.text_title.get_style_context().add_class('opaque')
    #self.text_title.set_has_frame(False)
    # self.text_title.modify_font(Pango.FontDescription('Size 12'))
    #btn_edit = GtkUtils.create_image_DND('edit-symbolic', label='Edit', on_click=self._on_edit_click, toggle=True)
    #btn_info = GtkUtils.create_image_button('dialog-information-symbolic', label='Info', on_click=None, toggle=True)
    #btn_remove.set_relief(Gtk.ReliefStyle.NONE)
    btn_detail = Gtk.LinkButton(label='Detail')
    btn_detail.get_style_context().add_class('opaque')

    headerbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    headerbar.pack_start(self.text_title, True, True, 0)
    headerbar.pack_end(btn_detail, False, False, 0)
    headerbar.get_style_context().add_class('note-headerbox')
    #headerbar.set_border_width(4)
    #headerbar.pack_end(btn_edit, False, False, 0)
    return headerbar

  def _create_toolbar(self):
    handlers = {
      'on_note_color_set': self._on_note_color_set,
      'on_note_font_set': self._on_note_font_set,
      'on_note_bold': self._on_note_bold,
      'on_note_italic': self._on_note_italic,
      'on_note_underline': self._on_note_underline,
      'on_note_strikethrough': self._on_note_strikethrough,
      'on_note_align_left': self._on_note_align_left,
      'on_note_align_center': self._on_note_align_center,
      'on_note_align_right': self._on_note_align_right,
      'on_note_align_fill': self._on_note_align_fill,
      'on_note_unindent': self._on_note_unindent,
      'on_note_indent': self._on_note_indent,
      'on_note_save': self._on_note_save,
      'on_note_insert_checkbox': self._on_note_insert_checkbox,
      'on_note_insert_object': self._on_note_insert_object,
      'on_note_insert_link': self._on_note_insert_link
    }

    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'note_toolbar.ui') 
    builder = Gtk.Builder()
    builder.add_from_file(path)
    builder.connect_signals(handlers)

    toolbar = builder.get_object('box-toolbar')
    btn_color = builder.get_object('btn-color')

    btn_color.set_relief(Gtk.ReliefStyle.NONE)
    btn_font_select = builder.get_object('btn-font-select')
    btn_font_select.set_relief(Gtk.ReliefStyle.NONE)
    # btn_save = builder.get_object('btn-save')
    # btn_save.connect('clicked', self._on_btn_save_clicked)
    # toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    # toolbar.pack_start(toolbar, True, True, 0)
    # toolbar.pack_end
    return toolbar

  # def _init_actions(self):


    # action = Gio.SimpleAction.new('note-bold', None)
    # action.connect('activate', self._on_note_bold)
    # self._app.add_action(action)

  def _on_edit_click(self, source):
    self._set_edit_mode(True)

  def _on_enter_webkit(self, source, event):
    if not self.edit_mode:
      self.btn_edit.set_visible(True)

  def _on_leave_webkit(self, source, event):
    if not self.edit_mode:
      self.btn_edit.set_visible(False)

  def _set_edit_mode(self, is_edit):
    self.edit_mode = is_edit
    self.btn_edit.set_visible(not is_edit)
    self.toolbar.set_visible(is_edit)
    self.webview.set_editable(is_edit)

  def _on_note_bold(self, source):
    self._web_exec_cmd('bold')
  def _on_note_italic(self, source):
    self._web_exec_cmd('italic')
  def _on_note_underline(self, source):
    self._web_exec_cmd('underline')
  def _on_note_strikethrough(self, source):
    self._web_exec_cmd('strikethrough')
  def _on_note_align_left(self, source):
    self._web_exec_cmd('justifyleft')
  def _on_note_align_center(self, source):
    self._web_exec_cmd('justifycenter')
  def _on_note_align_right(self, source):
    self._web_exec_cmd('justifyright')
  def _on_note_align_fill(self, source):
    self._web_exec_cmd('justifyfull')
  def _on_note_unindent(self, source):
    self._web_exec_cmd('outdent')
  def _on_note_indent(self, source):
    self._web_exec_cmd('indent')
    
  def _on_note_insert_object(self, source):
    dialog = Gtk.FileChooserDialog(
      "Please choose a file", 
      self._app.window,
      Gtk.FileChooserAction.OPEN,
      (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
    
    dialog.set_filename('~/')
    dialog.set_show_hidden(False)

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
      self._web_exec_cmd('insertImage', value=dialog.get_filename())
    
    dialog.destroy()

  def _on_note_insert_link(self, source):
    pass
  def _on_note_insert_checkbox(self, source):
    pass

  def _on_note_color_set(self, source):
    self._web_exec_cmd('forecolor', value=source.get_rgba().to_string())

  def _on_note_font_set(self, source):
    # huh? does not work!!
    font = source.get_font_desc()
    size = font.get_size() / Pango.SCALE
    
    # js = '''
    #   document.execCommand("fontSize", false, "7");
    #   var fontElements = document.getElementsByTagName("font");
    #   for (var i = 0, len = fontElements.length; i < len; ++i) {
    #       if (fontElements[i].size == "7") {
    #           fontElements[i].removeAttribute("size");
    #           fontElements[i].style.fontSize = "%s";
    #       }
    #   }
    # ''' % (size)

    self._web_exec_cmd('fontname', value=font.get_family())
    self._web_exec_cmd('fontsize', value=7)
    # Hack
    # self.webview.run_javascript(js, None, None, None)

  def _on_note_save(self, source):
    self._set_edit_mode(False)

  def _web_exec_cmd(self, cmd, value=None, show_ui=False):
    show_ui_str = 'null' if show_ui is None else ('false' if show_ui==False else 'true')
    value = 'null' if value is None else ('"' + value + '"' if isinstance(value, basestring) else str(value))
    full_cmd = 'document.execCommand("%s", %s, %s);' % (cmd, show_ui_str, value)
    # print full_cmd
    self.webview.execute_script(full_cmd)

  def _get_webkit_html(self):
    self.editor.execute_script("document.title=document.documentElement.innerHTML;")
    return self.webview.get_main_frame().get_title()