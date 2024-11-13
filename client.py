import socket, os.path, os
from common import read_md5, recv_until, recv_file, bytes_to_json
from common import find_files 
from enum import Enum, auto
import struct, argparse
from time import sleep

class FileChange(Enum):
    NEW = auto()
    UPDATED = auto()
    REMOVE = auto()
    MKDIR = auto()

class ServerConnection:
    def __init__(self, conn, folder):
        self.folder = folder
        self.conn = conn
        self.old_file_list = []
        self.file_list = []
        self.compare_folder_with_list()

    def check(self):
        self.get_file_list()
        changes = self.compare_file_lists()
        if len(changes) > 0:
            for change in changes:
                if change[1] == FileChange.NEW:
                    self.get_file(change[0])
                elif change[1] == FileChange.UPDATED:
                    remove_file(change[0])
                    self.get_file(change[0])
                elif change[1] == FileChange.REMOVE:
                    remove_file(change[0])
    
    def get_file(self, file_name):
        command = f"get {file_name}"
        self.conn.send(bytes(command, encoding="utf-8"))
        read_size = self.conn.recv(4)
        read_size = struct.unpack("<I", read_size)[0]
        self.conn.send(b"ACK")
        recv_file(self.conn, file_name, read_size)
        

    def get_file_list(self):
        self.conn.send(b"list-files")
        read_size = self.conn.recv(4)
        read_size = struct.unpack("<I", read_size)[0]
        self.conn.send(b"ACK")
        self.old_file_list = self.file_list
        self.file_list = recv_until(self.conn, read_size, bytes_to_json)

    def compare_file_lists(self):
        changes = []

        for key in self.old_file_list:
            if key not in self.file_list:
                changes.append((key, FileChange.REMOVE))
                continue
            elif key in self.file_list:
                if self.file_list[key] != self.old_file_list[key]:
                    changes.append((key, FileChange.UPDATED))
                    continue

        for key, val in self.file_list.items():
            if val == "":
                if not os.path.exists(key):
                    os.mkdir(key)
            else:
                if key not in self.old_file_list:
                    changes.append((key, FileChange.NEW))
        
        return changes
    
    def send_file(self, file_name):
        command = f"send {file_name}"
        self.conn.sendall(bytes(command, encoding="utf-8"))
        # ACK
        self.conn.recv(1024)
        file_size = os.stat(file_name).st_size
        self.conn.sendall(struct.pack("<I", file_size))
        # ACK
        self.conn.recv(1024)
        f = open(file_name, "rb")
        self.conn.sendfile(f)
        f.close()
        # ACK
        self.conn.recv(1024)

    def compare_folder_with_list(self):
        files = find_files(self.folder)
        
        for file in files:
            if file not in self.file_list:
                self.send_file(file)

parser = argparse.ArgumentParser(
                    prog='pyfsync client',
                    description='Client to pfsync protocol',
                    )

parser.add_argument('host')
parser.add_argument('--port', type=int, default=13131)
args = parser.parse_args()

HOST = args.host
PORT = args.port

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    print(f"Connection to {HOST}:{PORT}")
    s.connect((HOST, PORT))
    folder = s.recv(1024)
    folder = str(folder, encoding="utf-8")
    sc = ServerConnection(s, folder)

    while True:
        sc.check()
        sleep(2)
