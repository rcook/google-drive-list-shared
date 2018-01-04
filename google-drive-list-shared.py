#!/usr/bin/env python

from __future__ import print_function
import time

from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = 'https://www.googleapis.com/auth/drive.readonly.metadata'
store = file.Storage('storage.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)

DRIVE = discovery.build('drive', 'v3', http=creds.authorize(Http()))
file_service = DRIVE.files()
files = file_service.list().execute().get('files', [])
for f in files:
    file_shared = (file_service.get(fileId=f['id'], fields="name, shared").execute())
    
    # Only display files that are shared
    if file_shared['shared']:
        print(file_shared['name'])

    # Sleep 1/10 of a second between every API call, otherwise
    # you will exceed the number of calls allowed
    time.sleep(.100)
