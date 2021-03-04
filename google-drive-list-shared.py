#!/usr/bin/env python3

import ast
import itertools
import json
import time
import traceback

from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools

SCOPES = "https://www.googleapis.com/auth/drive.readonly.metadata"
PARENT_FIELDS = ["id", "name", "parents"]
DETAIL_FIELDS = ["id", "name", "owners", "parents",
                 "permissions", "shared", "webViewLink"]


class Cache(object):
    def __init__(self, service, items):
        self.__service = service
        self.__item_cache = {x["id"]: x for x in items}

    def get_item(self, item_id):
        item = self.__item_cache.get(item_id)
        if item is None:
            item = self.__service.files().get(
                fileId=item_id, fields=", ".join(PARENT_FIELDS)).execute()
            assert item["id"] == item_id
            self.__item_cache[item_id] = item
            return item
        else:
            return item

    def get_item_paths(self, item_id):
        def helper(item):
            parent_item_ids = item.get("parents")
            if parent_item_ids:
                parent_item_paths = itertools.chain.from_iterable(
                    [self.get_item_paths(x) for x in parent_item_ids])
                return [f"{x}/{item['name']}" for x in parent_item_paths]
            else:
                return [item["name"]]

        item = self.get_item(item_id)
        item_paths = item.get("__item_paths")
        if item_paths is None:
            item_paths = helper(item)
            item["__item_paths"] = item_paths
            return item_paths
        else:
            return item_paths


def get_service():
    store = file.Storage("storage.json")
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets("client_id.json", SCOPES)
        creds = tools.run_flow(flow, store)

    service = discovery.build("drive", "v3", http=creds.authorize(Http()))
    return service


def get_all_items(service):
    detail_field_list = ", ".join(DETAIL_FIELDS)
    results = service.files().list(
        pageSize=100, fields=f"nextPageToken, files({detail_field_list})").execute()
    token = results.get("nextPageToken")
    items = results.get("files", [])

    while token is not None:
        results = service.files().list(pageSize=1000, pageToken=token,
                                       fields=f"nextPageToken, files({detail_field_list})").execute()
        token = results.get("nextPageToken")
        items.extend(results.get("files", []))

    # Google Drive API does not return valid JSON because the property
    # names are not enclosed in double quotes, they are enclosed in
    # single quotes. So, use Python AST to convert the string to an
    # iterable list.
    return ast.literal_eval(str(items))


def format_user(user):
    return f"{user['displayName']} <{user['emailAddress']}>"


def format_permission(permission):
    t = permission["type"]
    if t == "user":
        return format_user(permission)
    elif t == "anyone":
        return "(Anyone)"
    else:
        return f"({t})"


def show_shared_item(c, item, index):
    item_paths = c.get_item_paths(item["id"])
    name = item["name"]
    owners = item["owners"]
    url = item["webViewLink"]
    owners = item["owners"]
    temp = item.get("permissions")
    if temp:
        permissions = [x for x in item["permissions"]
                       if not x.get("deleted", False)]
    else:
        permissions = None

    print(f"Shared item ({index + 1}):")
    print(f"  Name: {name}")
    print(f"  Owners:")
    for x in owners:
        print(f"    {format_user(x)}")
    print(f"  URL: {url}")
    print(f"  Path(s):")
    for p in item_paths:
        print(f"    {p}")
    if permissions:
        print(f"  Permissions:")
        for p in permissions:
            print(
                f"    {format_permission(p)} ({p['role']})")
    else:
        print("  Permissions: (none)")


def show_shared_items(c, items, shared_items):
    print(
        f"You have {len(items)} files in Google Drive of which {len(shared_items)} are shared")
    for i, item in enumerate(shared_items):
        try:
            show_shared_item(c, item, i)
        except KeyError as e:
            print(f"FAILURE: {e}")
            print(e)
            traceback.print_exc()
            print(json.dumps(item, sort_keys=True, indent=2))
            exit(1)


service = get_service()
items = get_all_items(service=service)
c = Cache(service=service, items=items)
shared_items = [x for x in items if x["shared"]]
show_shared_items(c, items, shared_items)
