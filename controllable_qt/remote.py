import random
import time
import socket
import typing
import threading
import multiprocessing

from PyQt6 import (
    QtCore,
    QtWidgets,
    QtWebEngineWidgets
)

from .exception import DataNotGiven

class Remote(QtWebEngineWidgets.QWebEngineView):
    COMMAND_POLL_INTERVAL: float = 1
    COMMAND_RESERVED_LENGTH: int = 2

    class __Nothing: pass
    
    def run_js(self, script: str) -> None:
        self.page().runJavaScript(script)
    
    def go_to_url(self, url: str) -> None:
        self.setUrl(QtCore.QUrl(url))
    
    def remote_client(self):
        while True:
            message = self.conn.recv(1024)
            message = message.decode('utf-8')
            self.command = message
            
            while self.result == self.__Nothing:
                time.sleep(0.5)
            
            message.send(self.result.encode('utf-8'))
            self.result: self.__Nothing | str = self.__Nothing

    def __set_timer(self):
        if (isinstance(self.timer, QtCore.QTimer)):
            self.timer.deleteLater()
        self.timer = QtCore.QTimer()
        self.timer.startTimer(self.COMMAND_POLL_INTERVAL)
        self.timer.start()
        self.timer.timeout.connect(self.__recurrent)

    def __recurrent(self):
        self.__set_timer()

        if (self.ready) and (self.command != ""):
            self.result: self.__Nothing | str = self.STR_TO_COMMAND[self.command[:10]](self.command[10:])
    
    def __set_ready(self):
        self.ready = True
    
    def __get_data(self, key: str, required: bool = False) -> typing.Any:
        if key in self.data:
            return self.data[key]
        else:
            if (required):
                raise DataNotGiven(f"Required Data Argument {key=} was not provided.")
            return False
    
    def __format_command(self, command):
        return (f"{{command:0>{self.COMMAND_RESERVED_LENGTH}}}").format(command=command)

    
    def __init__(self, data: dict):
        super().__init__()
        # initialize values.
        self.data = data
        self.ready = False
        self.command = ''
        self.result: self.__Nothing | str = self.__Nothing
        self.loadFinished.connect(self.__set_ready)

        self.timer = None

        self.setUrl(QtCore.QUrl(self.__get_data("starting_url", True)))

        self.conn: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(("localhost", self.__get_data("connection_port", True)))

        threading.Thread(target=self.remote_client, daemon=True).start()
        
        self.STR_TO_COMMAND = {
            self.__format_command(0): self.run_js,
            self.__format_command(1): self.go_to_url
        }

        self.__set_timer()

        self.show()
    
    @classmethod
    def start(cls, data: dict):
        app = QtWidgets.QApplication([__file__])
        remote = cls(data)
        app.exec()
    
    @classmethod
    def start_process(cls, data: dict):
        proc = multiprocessing.Process(target=cls.start, args=(data,), daemon=True)
        proc.name = "Remote-"+("".join(random.sample(list("qwertyuiopasdfghjklzxcvbnm1234567890"), k=20)))
        proc.start()
        return proc