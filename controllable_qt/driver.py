# ---------------------------------------------------
# author: Ansh Mathur
# gtihub: https://github.com/Fakesum
# repo: https://github.com/Fakesum/ TODO: THIS
# ---------------------------------------------------

# -------------------------------------import std library python--------------------------------------
import threading
import random
import os
import typing
import time
import contextlib

# import socket for communication with remote
import socket

# import re for url matching, and more.
import re

# import remote Class.
from .remote import Remote

# import logger
from .logger import logger

# import exceptions
from .exception import *

class Element: 
    pass

# Driver Class.
class Driver:
    """Driver Class, allows for multithreaded control of remote class.

    # Usage
    ## How to Create Driver
    ```python
    driver = Driver({
        ... # Config given to remote, and shared by driver.
    })
    ```
    
    ## how to give command to remote.
    
    ```python
    driver.execute(...) # see execute function for more info.
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

    def __init__(self, config: dict[str, list | str | int]={"starting_url": "http://httpbin.org/get"}) -> None:
        """Constructor for Driver

        Args:
            config (_type_, optional): _description_. Defaults to {"starting_url": "http://httpbin.org/get"}.
        """
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

    @contextlib.contextmanager
    def __temp_file(self, file_name=None, mode="w+"):
        if file_name == None:
            file_name = "".join(random.sample("qwertyuiopasdfghjklzxcvbnm1234567890", 20))
        path = os.path.abspath(file_name)
        yield open(path, mode), path
        os.remove(path)

    def execute(self, command: str, arg: str) -> str | None:
        """Execute a command directly to remote.

        Args:
            command (str): Command name, ex: js, all names are given in self.COMMAND_TO_ID
            arg (str): string argument to give to remote

        Returns:
            str | None: _description_
        """
        command = self.COMMAND_TO_ID[command]+arg
        self._commands.append(command)
        while not (command in self._results):
            time.sleep(1)
        result = self._results[command]
        
        del self._results[command]

        return result

    def execute_script_file(self, script_file_name) -> str | None:
        """execute the javascript in the given script file.

        Args:
            script_file_name (str): the path of the script file name.

        Raises:
            FileNotFoundError: Raised if the file is not found.

        Returns:
            str | None: Whatever is Retuned by the script.
        """
        if not os.path.exists(script_file_name):
            raise FileNotFoundError(f"file: {script_file_name=}")
        return self.execute("js", (script_file_name))

    def execute_script(self, script: str) -> str | None:
        """Execute given Script, and return the returned value from the script, converted to python.

        # Usage
            ```python
            >>> # without return
            >>> driver.execute_script("console.log('abc')")
            >>>
            >>> # with return
            >>> a = driver.execute_script("console.log('abc'); return 1;")
            >>> print(a)
            1
            >>> 
            ```

        # Raises:
            JavascriptException: When there is a problem executing the javascript,
            currently no additional info provided - TODO: Provide the reason for the javascript exception. by piping stdout/stderr from Remote process maybe?

        # Args:
            script (str): The Javascript to execute.

        # Returns:
            str | None: The return value of the script.
        
        """
        with self.__temp_file() as (tempfile, tempfile_name):
            tempfile.write(script)
            return self.execute_script_file(tempfile_name)
    
    def open(self, url: str) -> None:
        """open the url given in the current tab.
        returns None. uses setURL.

        # Usage
            ```python
            >>> driver.open("https://www.google.com/") # this will open the url.
            >>> driver.open('my purse') # this will throw a InvalidUrl Exception.
            ```
        
        # Raises:
            InvalidUrl: raised when the url is detected to be invalid.

        # Args:
            url (str): open the url in the current tab.
        """

        # regex(s) taken from github.com/seleniumbase/seleniumbase > fixtures.page_utils.is_valid_url
        url_regex = re.compile(
            r"^(?:http)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
            r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        logger.debug(f"{url_regex.pattern=}, {url=}")
        logger.info(f"going to page: {url}")

        if not url_regex.match(url):
            raise InvalidUrl(f"argument {url=} is not a valid url.")
        return self.execute("url", url)

    def get_element(self, selector: str, ) -> Element:
        pass