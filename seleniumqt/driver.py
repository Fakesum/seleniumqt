# ---------------------------------------------------
# author: Ansh Mathur
# gtihub: https://github.com/Fakesum
# repo: https://github.com/Fakesum/ TODO: THIS
# ---------------------------------------------------

# -------------------------------------import std library python--------------------------------------
import threading as _threading
import random as _random
import os as _os
import typing as _typing
import time as _time
import contextlib as _contextlib

# import _socket for communication with remote
import socket as _socket

# import _re for url matching, and more.
import re as _re

# import remote Class.
from .remote import Remote as _Remote

# import logger
from .logger import logger

# import exceptions
from .exception import *


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

    # the number of charectors at the begining of the message transfer to _socket
    # that indicate which command is being given.
    COMMAND_RESERVED_LENGTH = 2

    # -----------------------------------------utility functions------------------------------------------
    @_contextlib.contextmanager
    def __temp_file(self, file_name=None):
        if file_name == None:
            file_name = "".join(
                _random.sample("qwertyuiopasdfghjklzxcvbnm1234567890", 20)
            )
        path = _os.path.abspath(file_name)
        open(path, "w").write("")
        try:
            yield path
        finally:
            _os.remove(path)

    # -------------------------------------------initialization-------------------------------------------
    def __conn_server(self) -> _typing.NoReturn:
        """Server which gives commands to remote.

        Returns
        -------
            _typing.NoReturn: Never Returns

        """
        self.conn_sock.listen()
        conn, _ = self.conn_sock.accept()

        while conn:
            while self._commands == []:
                _time.sleep(1)
            for command in self._commands:
                conn.send(command.encode("utf-8"))
                self._results.update(
                    {command: conn.recv(1024).decode("utf-8")}
                )
            self._commands = []
        logger.warning("Closing, _Remote Connection was closed.")

    def __format_command(self, command: int | str) -> str:
        """Utility Command to format number to standardized command message format.

        Args:
        ----
            command (int | str): Command name/id

        Returns:
        -------
            str: formated/standardized command message format.

        """
        return (f"{{command:0>{self.COMMAND_RESERVED_LENGTH}}}").format(
            command=command
        )

    def __init__(
        self,
        config: dict[str, list | str | int] = {
            "starting_url": "http://httpbin.org/get"
        },
    ) -> None:
        """Constructor for Driver

        Args:
        ----
            config (_type_, optional): _description_. Defaults to {"starting_url": "http://httpbin.org/get"}.

        """
        self.daemon = True
        self.config = config
        self._commands: list = []
        self._results: dict[str, _typing.Any] = {}
        self.__hidden = False
        self.conn_sock: _socket.socket = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        self.conn_sock.bind(("localhost", 0))

        self.COMMAND_TO_ID = {
            "js": self.__format_command(0),
            "url": self.__format_command(1),
            "click": self.__format_command(2),
            "hide": self.__format_command(3),
            "show": self.__format_command(4),
        }

        logger.debug(f"{self.COMMAND_TO_ID=}")

        self._remote_proc = _Remote.start_process(
            {"connection_port": self.conn_sock.getsockname()[1], **self.config}
        )

        self.__driver_server_thread = _threading.Thread(
            target=self.__conn_server, daemon=True
        )
        self.__driver_server_thread.name = "driver-server"
        self.__driver_server_thread.start()

    # ==============================================commands==============================================
    # first the basic commands.

    @logger.catch
    def execute(self, command: str, arg: str = "") -> str | None:
        """Execute a command directly to remote.

        Args:
        ----
            command (str): Command name, ex: js, all names are given in self.COMMAND_TO_ID
            arg (str): string argument to give to remote

        Returns:
        -------
            str | None: _description_

        """
        if not self._remote_proc.is_alive():
            raise RemoteExited(f"{self._remote_proc.pid=} has exited.")

        command = self.COMMAND_TO_ID[command] + arg
        self._commands.append(command)
        while not (command in self._results):
            _time.sleep(1)
        result = self._results[command]

        del self._results[command]

        return result

    @logger.catch
    def execute_script_file(self, script_file_name) -> str | None:
        """Execute the javascript in the given script file.

        # Usage
            ```python
            >>> # the file to run.
            >>>
            >>> print(open("main.js", "r").read())
            document.querySelector('body').innerHTML = '';
            >>> # call the function
            >>> driver.execute_script_file('main.js')

            # -------------------------------------------------------

            >>> # with return value.
            >>> print(open("main.js", "r").read())
            return 1;
            >>> a = driver.execute_script_file("main.js")
            >>>
            >>> a
            '1'
            ```

        # Args:
            script_file_name (str): the path of the script file name.

        # Raises:
            FileNotFoundError: Raised if the file is not found.

        # Returns:
            str | None: Whatever is Retuned by the script.
        """
        if not _os.path.exists(script_file_name):
            raise FileNotFoundError(f"file: {script_file_name=}")
        return self.execute("js", (script_file_name))

    @logger.catch
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
            '1'
            >>>
            ```

        # Raises:
            JavascriptException: When there is a problem executing the javascript, The entire console,
            is provided in the exception.

        # Args:
            script (str): The Javascript to execute.

        # Returns:
            str | None: The return value of the script.

        """
        with self.__temp_file() as tempfile_path:
            open(tempfile_path, "w").write(script)
            return self.execute_script_file(tempfile_path)

    @logger.catch
    def open(self, url: str) -> None:
        """Open the url given in the current tab.
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
        url_regex = _re.compile(
            r"^(?:http)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
            r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            _re.IGNORECASE,
        )

        # logger.debug(f"{url_regex.pattern=}, {url=}") # this one is a bit much.
        logger.info(f"going to page: {url}")

        if not url_regex.match(url):
            raise InvalidUrl(f"argument {url=} is not a valid url.")
        self.execute("url", url)

    @logger.catch
    def click(
        self,
        selector: str,
        _type: _typing.Literal["css "] | _typing.Literal["xpath"] = "css ",
        /,
    ) -> None:  # noqa - untested #TODO: debug here.
        """Click an element on screen, this uses the QEvent.Type.MouseButtonPressed, not javascript. so this
        click event is indistiguishable from a real click.

        # Usage
            ```python
            >>> driver.click("input.pfp") # this will click the input html element with the class `pfp`.
            ```

        # Raises:
            InternalWidgitNotFound: An Internal error which is triggred if the internal widgit which the click signal is send
            to is not foound.

        # Args:
            selector (str): the selector for the element that is to be clicked.
            _type (_typing.Literal['css'] | _typing.Literal['xpath], optional): in what format is the selector given, css, xpath, etc. Defaults to 'css '.
        """
        self.execute("click", _type + selector)

    @logger.catch
    def hide_window(self) -> None:
        """Hide the browser window.
        # Usage
            ```python
            >>> # window is visible
            >>> driver.hide_window()
            >>> # window is no longer visible
            >>> driver.show_window()
            >>> # window is visible again.
            ```
        """
        self.__hidden = True
        self.execute("hide")

    @logger.catch
    def show_window(self) -> None:
        """Show the browser window if it is hidden.
        # Usage
            ```python
            >>> # window is visible
            >>> driver.hide_window()
            >>> # window is no longer visible
            >>> driver.show_window()
            >>> # window is visible again.
            ```
        """
        if self.__hidden:
            self.execute("show")
        else:
            logger.warning(
                "Ignoring show_window command, window is not hidden."
            )

    # ----------------------------------------------cleanup-----------------------------------------------
    def __del__(self):
        try:
            self.conn_sock.close()  # just in case, this should be done automatically, but just in case.
        except Exception as e:  # the self.conn_sock might have already closed
            # or the program might have crashed before defining it.
            logger.exception(str(e))


__all__ = ["Driver"]
