import os
home = os.path.dirname(os.path.abspath(__file__))

PORT = 14908
ENCODING = 'utf-8'

DB_PROTOCOL = 'sqlite:///'
DB_NAME = '/client_contacts.db'
DB_PATH = DB_PROTOCOL + home + DB_NAME
