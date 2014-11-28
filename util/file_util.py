import hashlib

def get_file_hash_hex(path, blocksize=65536):
  afile = open(path, 'rb')
  hasher = hashlib.md5()
  buf = afile.read(blocksize)
  while len(buf) > 0:
    hasher.update(buf)
    buf = afile.read(blocksize)
  return hasher.hexdigest()

# huh? Implement!
def get_unique_filename(path):
  return path

# huh? Implement! there is this filename: '26/03/2014 8:57:48 pm'
def get_valid_filename(filename):
  return filename.replace('/', '-')