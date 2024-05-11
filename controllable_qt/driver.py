import threading
import time
import socket
from .remote import Remote

class Driver(threading.Thread):

    def __conn_server(self):
        self.conn_sock.listen()
        conn, _ = self.conn_sock.accept()

        while conn:
            while self._commands == []:
                time.sleep(1)
            for command in self._commands:
                conn.send(command.encode('utf-8'))
                self._results.update({command:conn.recv(1024).decode('utf-8')})
            self._commands = []

    def __init__(self, config):
        super().__init__(daemon=True)
        self.daemon = True
        self.config = config
        self._commands = []
        self._results = {}
        self.conn_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn_sock.bind(('localhost', 0))
        Remote.start_process({
            "starting_url": self.config["starting_url"],
            "connection_port": self.conn_sock.getsockname()[1]
        })
        threading.Thread(target=self.__conn_server, daemon=True).start()

    def execute_script(self, script_file_name):
        command = '00'+script_file_name
        self._commands.append(command)
        while not (command in self._results):
            time.sleep(1)
        return self._results[command]