
DELIM_CHAR = ','

def serialize_keys(query, delim=DELIM_CHAR):
  return DELIM_CHAR.join([str(row[0]) for row in query.tuples()])

# Assume key is an int
def deserialize_keys(delimited_str):
  return [int(id) for id in delimited_str.split(str=DELIM_CHAR)]

def list_eq(list1, list2):
  print 'Comparing: ' + str(list1) + ' w/ ' + str(list2)
  if len(list1) != len(list2):
    return False
  for el in list1:
    if el not in list2:
      return False
  return True