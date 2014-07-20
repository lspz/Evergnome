import ConfigParser

class AppConfig:
  def __init__(self, filepath, environment='DEFAULT'):
    config = ConfigParser.SafeConfigParser()
    config.read(filepath);
    self.debug = config.get(environment, 'debug') == '1'
    self.manual_sync = config.get(environment, 'manual_sync') == '1'
    self.disable_edit = config.get(environment, 'disable_edit') == '1'
    self.sandbox = config.get(environment, 'sandbox') == '1'