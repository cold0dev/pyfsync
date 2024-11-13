from glob import glob
import json, hashlib
import os, os.path

def read_md5(file_name):
    with open(file_name, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chuink)
        return file_hash.hexdigest()

def remove_file(file_name):
    pass

def recv_until(conn, size, parser=None):
    buffer = bytes()

    i = 0
    while True:
        if i == size: break
        if size - i >= 1024:
            buffer += conn.recv(1024)
            i += 1024
        else:
            buffer += conn.recv(size - i)
            break

    if parser is None:
        return buffer
    else:
        return parser(buffer)

def recv_file(conn, name, size):
    f = open(name, "wb")

    i = 0
    while True:
        if i == size: break
        if size - i >= 1024:
            buffer = conn.recv(1024)
            f.write(buffer)
            i += 1024
        else:
            buffer = conn.recv(size - i)
            f.write(buffer)
            break

def bytes_to_json(v):
    return json.loads(str(v, encoding="utf-8"))

def find_files(folder):
        files = glob(f"{folder}/**", recursive=True)
        out = {}
        for file in files:
            if os.path.isdir(file):
                out[file] = ""
                continue

            out[file] = read_md5(file) 
        return out
