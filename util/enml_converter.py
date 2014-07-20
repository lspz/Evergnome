# huh? make node functions mutable?
import mimetypes
from lxml import etree
from file_util import get_file_hash_hex


HTML_BODY_STYLE = 'word-wrap: break-word; -webkit-line-break: after-white-space;'

ENML_HEADER =  "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
ENML_HEADER += "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\"> "
  
# huh? add validation
def ENMLToHTML(enml, medias_by_hash):
  # print enml
  tree = etree.fromstring(enml, parser=etree.HTMLParser())
  root_note = tree.xpath('//en-note')[0]
  _root_note_to_html(root_note)
  todos = tree.xpath('//en-todo')
  for todo in todos:
    _todo_to_html(todo)
  medias = root_note.xpath('//en-media')
  for media in medias:
    _media_to_html(media, medias_by_hash)

  html = etree.Element('html')
  html.append(root_note)
  html_str = etree.tostring(html, pretty_print=True, method="html")
  # print html_str
  return html_str

def _root_note_to_html(note):
  note.tag = 'body'

def _todo_to_html(element):
  element.tag = 'input'
  element.set('type', 'checkbox')

def _media_to_html(element, medias_by_hash):
  media_type = element.attrib.get('type', '')
  hash = element.attrib.get('hash', '')
  media = medias_by_hash.get(hash)
  if media_type.startswith("image") and (media is not None) and (media.localpath is not None):
    element.tag = 'img'
    element.set('src', 'file://' + media.localpath)
  else:
    _remove_from_parent(element)
  #print etree.tostring(element)

###############################################

def HTMLToENML(html, medias_by_path):
  # huh? remove non-valid element
  resource_hashes = []

  tree = etree.fromstring(html, parser=etree.HTMLParser())
  body = tree.xpath('//body')[0]

  todos = body.xpath('//input[@type="checkbox"]')
  for todo in todos:
    _todo_to_enml(todo)

  images = body.xpath('//img')
  for image in images:
    _image_to_enml(image, medias_by_path, resource_hashes)
    
  _html_body_to_enml(body)
  enml = ENML_HEADER + '\n' + etree.tostring(body, pretty_print=True, method="xml")

  return (enml, resource_hashes)

def _html_body_to_enml(body):
  # huh? webkit automatically add the style below. we just remove it for now,
  # need to be able to restore the original style later
  # bodyword-wrap: break-word; -webkit-nbsp-mode: space; -webkit-line-break: after-white-space;
  body.tag = 'en-note'
  if 'style' in body.attrib:
    del body.attrib['style']
  # body.set('style', body.get('style', default='').replace(HTML_BODY_STYLE, ''))

def _todo_to_enml(element):
  # huh? this doesnt preserve the checked state
  element.tag = 'en-todo'
  del element.attrib['type']

def _image_to_enml(image, medias_by_path, resource_hashes):
  hash = image.get('hash', default=None)
  path = image.get('src', default='')
  if hash is None:
    media = medias_by_path.get(path)
    hash = media.hash
    if media is not None:
      image.set('type', media.mime)
      image.set('hash', media.hash)

  resource_hashes.append(hash)
  image.tag = 'en-media'
  del image.attrib['src']



###############################################

def _remove_from_parent(element):
  parent = element.getparent()
  if parent is not None:
    parent.remove(element)