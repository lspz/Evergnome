from lxml import etree

# huh? add validation
def ENMLToHTML(input, resources):
  tree = etree.fromstring(input, parser=etree.HTMLParser())
  root_note = tree.xpath('//en-note')[0]
  _convert_root_note(root_note)
  todos = tree.xpath('//en-todo')
  for todo in todos:
    _convert_todo(todo)
  medias = root_note.xpath('//en-media')
  for media in medias:
    _convert_media(media, resources)

  html = etree.Element('html')
  html.append(root_note)
  return etree.tostring(html, pretty_print=True, method="html")

def _convert_root_note(note):
  style = note.get('style')
  if style is None:
    style = ''
  note.tag = 'body'
  note.set('style', style + ' word-wrap: break-word; -webkit-line-break: after-white-spac') #-webkit-nbsp-mode: space; e;

def _convert_todo(element):
  element.tag = 'input'
  element.set('type', 'checkbox')

def _convert_media(element, resources):
  media_type = element.attrib.get('type', '')
  hash = element.attrib.get('hash', '')
  width = element.attrib.get('width', None)
  height = element.attrib.get('height', None)
  resourcepath = resources.get(hash)
  if media_type.startswith("image") and (resourcepath is not None):
    element.tag = 'img'
    element.set('src', 'file://' + resourcepath)
    if width is not None:
      element.set('width', str(width))
    if height is not None:
      element.set('height', str(height))
  else:
    _remove_from_parent(element)
  #print etree.tostring(element)


def _remove_from_parent(element):
  parent = element.getparent()
  if parent is not None:
    parent.remove(element)