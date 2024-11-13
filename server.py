import socket, os
from glob import glob
import json, hashlib
import os.path
from common import read_md5, find_files
import struct, argparse

class ClientConnection:
    def __init__(self, conn, folder):
        self.shared_folder = folder
        self.conn = conn

        status = f"folder {self.shared_folder}"
        self.conn.send(bytes(status, encoding="utf-8"))

    def handle_command(self):
        command = self.conn.recv(1024)
        command = str(command, encoding="utf-8")
        print(f"Received command: {command}")
        args = command.split()
        args = [arg.strip() for arg in args]
        #TODO: validate args
        if args[0] == "list-files":
            self.send_files_list()
        elif args[0] == "get":
            self.send_file(args[1])
        elif args[0] == "close":
            return True

    def send_files_list(self):
        files = find_files(self.shared_folder)
        files = json.dumps(files)
        files = bytes(files, encoding="utf-8")
        self.conn.sendall(struct.pack("<I", len(files)))
        self.conn.recv(1024)
        self.conn.sendall(files)

    def send_file(self, file_name): 
        file_size = os.stat(file_name).st_size
        self.conn.sendall(struct.pack("<I", file_size))
        # ACK
        self.conn.recv(1024)
        f = open(file_name, "rb")
        self.conn.sendfile(f)
        f.close()

parser = argparse.ArgumentParser(
                    prog='pyfsync server',
                    description='Server to pfsync protocol',
                    )

parser.add_argument('folder')
parser.add_argument('--port', type=int, default=13131)
args = parser.parse_args()

folder = args.folder 
HOST = ''
PORT = args.port

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"Starting server at :{PORT}")
    while True:
        conn, addr = s.accept()
        cc = ClientConnection(conn, folder)
        while True:
            close = cc.handle_command()
            if close is True:
                break
        conn.close()
