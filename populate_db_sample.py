#!/usr/bin/python

from os import path, rename
from peewee import *
from configs import AppConfig
from data_models import *
import app

config = AppConfig(app.APP_CONFIG_PATH)
db_path = config.db_path

if path.isfile(db_path):
  rename(db_path, db_path + '.bak')

print 'Connecting to ' + db_path
db = SqliteDatabase(db_path)
db.set_autocommit(False)
db_proxy.initialize(db)

Notebook.create_table()
# notebook1 = Notebook(name='Todo')
# notebook1.save()
# notebook2 = Notebook(name='Project')
# notebook2.save()
# notebook3 = Notebook(name='Brainstorm')
# notebook3.save()

Note.create_table()
# note1 = Note(title='Car service', content='blahblahblah', notebook = notebook1)
# note1.save()
# note2 = Note(title='Weekly groceries', content='blahblahblah', notebook = notebook1)
# note2.save()
# note3 = Note(title='Evernote client', content='blahblahblah', notebook = notebook2)
# note3.save()
# note4 = Note(title='What should we do on weekend?', content='blahblahblah', notebook = notebook3)
# note4.save()
# ###

db.commit()
# User.create_table()
# user1 = User(username='louis')
# user1.save()

# ###

# PortfolioInfo.create_table()
# pi = PortfolioInfo()
# pi.user = user1
# pi.save()

# ###

# PortfolioStock.create_table()

# stock1 = PortfolioStock()
# stock1.symbol='CCV.AX'
# stock1.user=user1
# stock1.date_added=None
# stock1.initial_price=0.85
# stock1.unit=2535
# stock1.fee=19.95
# stock1.save()

# stock2 = PortfolioStock()
# stock2.symbol='SUN.AX'
# stock2.user=user1
# stock2.date_added=None
# stock2.initial_price=12.65
# stock2.unit=276
# stock2.fee=19.95
# stock2.save()

# stock3 = PortfolioStock()
# stock3.symbol='SLF.AX'
# stock3.user=user1
# stock3.date_added=None
# stock3.initial_price=9.59
# stock3.unit=380
# stock3.fee=19.95
# stock3.save()

# stock4 = PortfolioStock()
# stock4.symbol='GOLD.AX'
# stock4.user=user1
# stock4.date_added=None
# stock4.initial_price=131.6
# stock4.unit=38
# stock4.fee=19.95
# stock4.save()

# ###

# WatchStock.create_table()

# stock1 = WatchStock()
# stock1.symbol='CBA.AX'
# stock1.user=user1
# stock1.date_added=None
# stock1.save()

# stock2 = WatchStock()
# stock2.symbol='ANN.AX'
# stock2.user=user1
# stock2.date_added=None
# stock2.save()

# stock3 = WatchStock()
# stock3.symbol='TLS.AX'
# stock3.user=user1
# stock3.date_added=None
# stock3.save()
# ###

# stock_db.commit()
