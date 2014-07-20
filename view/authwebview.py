from gi.repository import Gtk, WebKit
import urlparse

class AuthWebView(Gtk.Dialog):

  def __init__(self, url, callback_url, callback_func): 
    Gtk.Dialog.__init__(self)
    self.callback_url = callback_url
    self.callback_func = callback_func

    self.webview = WebKit.WebView()
    self.webview.set_visible(True)
    self.webview.connect('navigation-policy-decision-requested', self._on_navigation_requested)
    self.webview.load_uri(url)
    self.get_content_area().pack_start(self.webview, True, True, 0)
    self.set_modal(True)
    self.set_size_request(400, 400)

  def _on_navigation_requested(self, web_view, frame, request, navigation_action, policy_decision):
    url_parsed = urlparse.urlparse(request.get_uri())
    if self.callback_url in url_parsed.path:
      # print url_parsed
      query_args = urlparse.parse_qs(url_parsed.query)
      policy_decision.ignore()
      print url_parsed
      if query_args.has_key('oauth_token') and query_args.has_key('oauth_verifier'):
        self.callback_func(token=query_args['oauth_token'], verifier=query_args['oauth_verifier'])
      self.close()
