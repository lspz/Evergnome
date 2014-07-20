import hashlib
# import mimetypes

def get_file_hash_hex(path, blocksize=65536):
  afile = open(path, 'rb')
  hasher = hashlib.md5()
  buf = afile.read(blocksize)
  while len(buf) > 0:
    hasher.update(buf)
    buf = afile.read(blocksize)
  return hasher.hexdigest()
