#!/usr/bin/env python3

import argparse
import ast
import csv
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
CSV_FIELDS = ["name", "url", "owners", "paths", "permissions"]


def unicode_escape_char(c):
    cp = ord(c)
    if cp <= 0xFF:
        return f"\\{cp:02o}"
    elif cp <= 0xFFFF:
        return f"\\u{cp:04x}"
    elif cp <= 0xFFFFFFFF:
        return f"\\U{cp:08x}"
    else:
        raise ValueError(f"Cannot encode {c}")


SPECIAL_CHARS = [",", "/"]
SPECIAL_CHAR_ENCODINGS = {c: unicode_escape_char(c) for c in SPECIAL_CHARS}


class ItemPath(object):
    def __init__(self, names):
        assert isinstance(names, list)
        self.__names = names
        self.encoded = encode_item_path(self.__names)

    def append(self, name):
        return ItemPath(self.__names + [name])


def encode_item_name(n):
    e = json.dumps(n)[1:-1]
    for c, encoding in SPECIAL_CHAR_ENCODINGS.items():
        e = e.replace(c, encoding)
    return e


def decode_item_name(e):
    n = e
    for c, e in SPECIAL_CHAR_ENCODINGS.items():
        n = n.replace(e, c)
    n = json.loads(f"\"{n}\"")
    return n


def encode_item_path(names):
    p = "/".join([encode_item_name(n) for n in names])
    return p


def decode_item_path(p):
    es = p.split("/")
    return [decode_item_name(e) for e in es]


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
                parent_item_paths = [self.get_item_paths(
                    x) for x in parent_item_ids]
                return [y.append(item["name"])
                        for x in parent_item_paths
                        for y in x]
            else:
                return [ItemPath([item["name"]])]

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


def format_grantee(grantee):
    t = grantee["type"]
    if t == "user":
        return format_user(grantee)
    elif t == "anyone":
        return "(Anyone)"
    else:
        return f"({t})"


def write_shared_item(csv_writer, c, item, index):
    print(f"Shared item ({index + 1}): {item['name']}")

    encoded_name = item["name"]
    encoded_url = item["webViewLink"]
    encoded_owners = ",".join(encode_item_name(format_user(x))
                              for x in item["owners"])
    encoded_item_paths = ",".join(
        [x.encoded for x in c.get_item_paths(item["id"])])

    permissions = item.get("permissions")
    if permissions:
        filtered_permissions = [
            x for x in permissions if not x.get("deleted", False)]
        encoded_permissions = ",".join(
            [f"{encode_item_name(format_grantee(p))} ({p['role']})" for p in filtered_permissions])
    else:
        encoded_permissions = ""

    csv_writer.writerow([
        encoded_name,
        encoded_url,
        encoded_owners,
        encoded_item_paths,
        encoded_permissions])


def write_shared_items(csv_writer, c, items, shared_items):
    csv_writer.writerow(CSV_FIELDS)
    print(
        f"You have {len(items)} files in Google Drive of which {len(shared_items)} are shared")
    for i, item in enumerate(shared_items):
        try:
            write_shared_item(csv_writer, c, item, i)
        except KeyError as e:
            print(f"FAILURE: {e}")
            print(e)
            traceback.print_exc()
            print(json.dumps(item, sort_keys=True, indent=2))
            exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_file_name", metavar="OUTPUTFILENAME", type=str)
    args = parser.parse_args()

    service = get_service()
    items = get_all_items(service=service)
    c = Cache(service=service, items=items)
    shared_items = [x for x in items if x["shared"]]

    with open(args.output_file_name, "w") as csv_file:
        csv_writer = csv.writer(csv_file)
        write_shared_items(csv_writer, c, items, shared_items)


if __name__ == "__main__":
    main()
