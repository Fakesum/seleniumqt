# ---------------------------------------------------
# author: Ansh Mathur
# gtihub: https://github.com/Fakesum
# ---------------------------------------------------

# import std library python
import threading
import os
import typing
import time
import socket

# import remote Class.
from .remote import Remote

# import logger
from .logger import logger

# Driver Class.
class Driver:
    """Driver Class, allows for multithreaded control of remote class.

    # Usage
    ## How to Create Driver
    ```python
    driver = Driver({
        ... # Config given to remote, and shared by driver.
    })
    
    ## how to give command to remote.
    
    ```python
    driver.execute()
    ```
    """

    COMMAND_RESERVED_LENGTH = 2

    def __conn_server(self) -> typing.NoReturn:
        """Server which gives commands to remote.

        Returns:
            typing.NoReturn: Never Returns
        """
        self.conn_sock.listen()
        conn, _ = self.conn_sock.accept()

        while conn:
            while self._commands == []:
                time.sleep(1)
            for command in self._commands:
                conn.send(command.encode('utf-8'))
                self._results.update({command:conn.recv(1024).decode('utf-8')})
            self._commands = []
        logger.warning("Closing, Remote Connection was closed.")

    def __format_command(self, command: int | str) -> str:
        """Utility Command to format number to standardized command message format.

        Args:
            command (int | str): Command name/id

        Returns:
            str: formated/standardized command message format.
        """
        return (f"{{command:0>{self.COMMAND_RESERVED_LENGTH}}}").format(command=command)

    def __init__(self, config={"starting_url": "http://httpbin.org/get"}) -> None:
        super().__init__(daemon=True)
        self.daemon = True
        self.config = config
        self._commands = []
        self._results = {}
        self.conn_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn_sock.bind(('localhost', 0))

        self.COMMAND_TO_ID = {
            "js": self.__format_command(0),
            "url": self.__format_command(1),
        }

        logger.debug(f"{self.COMMAND_TO_ID=}")
        
        self._remote_proc = Remote.start_process({
            "connection_port": self.conn_sock.getsockname()[1],
            **self.config
        })

        threading.Thread(target=self.__conn_server, daemon=True).start()
    
    def execute(self, command: str, arg: str):
        
        command = self.COMMAND_TO_ID[command]+arg
        self._commands.append(command)
        while not (command in self._results):
            time.sleep(1)
        result = self._results[command]
        
        del self._results[command]

        return result

    def execute_script_file(self, script_file_name):
        if not os.path.exists(script_file_name):
            raise FileNotFoundError(f"file: {script_file_name=}")
        return self.execute("js", (script_file_name))