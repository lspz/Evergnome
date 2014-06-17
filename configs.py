import ConfigParser

class AppConfig:
  def __init__(self, filepath, environment='DEFAULT'):
    config = ConfigParser.SafeConfigParser()
    config.read(filepath);
    self.db_path = config.get(environment, 'db_path')
    self.debug = config.get(environment, 'debug') == '1'
    self.manual_sync = config.get(environment, 'manual_sync') == '1'