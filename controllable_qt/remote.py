# ---------------------------------------------------
# author: Ansh Mathur
# gtihub: https://github.com/Fakesum
# ---------------------------------------------------

# import python std library
import random
import time
import socket
import typing
import threading
import enum
import multiprocessing

# import Qt
from PyQt6 import (
    QtCore,
    QtWidgets,
    QtWebEngineWidgets
)

# import Some Custom Exceptions
from .exception import DataNotGiven

# import logger
from .logger import logger

class WindowMode(enum.IntEnum):
    WINDOWED = 0
    FULLSCREEN = 1
    MAXIMIZED = 2
    MINIMIZED = 3
    WINDOWED_ON_TOP = 4
    FULLSCREEN_ON_TOP = 5
    MAXIMIZED_ON_TOP = 6
    WINDOWED_ON_BOTTOM = 7
    FULLSCREEN_ON_BOTTOM = 8
    MAXIMIZED_ON_BOTTOM = 9

class Remote(QtWebEngineWidgets.QWebEngineView):
    """The Remote Qt Session Host.

    # Usage

    How to use this class by function:
    ## start
    ```python
    proc: multiprocessing.Process = Remote.start_process({
        # required
        "starting_url": ..., # url/QWebEnginePage where the remote will start
        "connection_port": ..., # the port where the remote will connect to, and listen to commands.

        # optional
        "window_mode": ..., # one of the WindowMode enum
        "flags": ..., # list of qt.WindowType Flags.
        "wait_for_load": ... # True or False.
    })
    # this will return the process Object where the Remote is running.
    ```
    
    """
    
    # define class Scope Global constants.
    COMMAND_POLL_INTERVAL: float = 1
    COMMAND_RESERVED_LENGTH: int = 2

    # a special None Type, this is used
    # to distinguish whether a command 
    # runner has returned None or wether
    # Nothing has yet been given.
    class __Nothing: pass # it is `__` private so that it can't be given as custom return of some kind.
    
    # ------------------------------------command execution functions-------------------------------------
    def run_js(self, script_file_name: str) -> None:
        """Execute the Given Javascript file.
        Args:
            script_file_name (str): the path to the javascript file which is to be run.
        """

        # load script from file.
        try:
            script = open(script_file_name, "r").read()
        except Exception as e:
            logger.exception(f"Threre was a problem when reading the script file: {script_file_name=}")
            return

        logger.info(f"Running {script=}")
        logger.trace(f"Starting to run {script=}")
        self.page().runJavaScript(script)
        logger.trace(f"Done Running {script=}")
    
    def go_to_url(self, url: str) -> None:
        """Change the url as per the argument given with setUrl.

        Args:
            url (str): the url given by the driver.
        """

        logger.info(f'Changing Url to {url=} from {self.page().url().toString()=}')

        logger.trace(f"Setting Url to {url=}")
        self.setUrl(QtCore.QUrl(url))
        logger.trace(f"Setting Url to {url=}")
    
    # -------------------------------------driver communication logic-------------------------------------
    def remote_client(self) -> typing.NoReturn:
        """This function runs in a seperate thread, here it continously listens for any
        commands that are given by the driver, and updates the self.command property
        accordingly."""

        logger.info("Started Remote Command Client")
        
        while self.conn:
            message = self.conn.recv(1024)
            message = message.decode('utf-8')
            self.command = message
            logger.info(f"Executing Command: {self.command[:self.COMMAND_RESERVED_LENGTH]} {self.command[self.COMMAND_RESERVED_LENGTH:]}")
            
            while self.command != '':
                time.sleep(0.5)
            
            self.conn.send(self.result.encode('utf-8') if self.result != None else b'done')
            self.result: self.__Nothing | str = self.__Nothing
        
        logger.warning("Closing Remote Client.")
        self.close() # when the connection is close we want qt to close as well.

    def __set_timer(self) -> None:
        """This function deletes any exsiting timers and sets a new timer for 
        COMMAND_POLL_INTERVAL time, upon the completion of which the recurrent function
        is run.
        """

        # delete existing timer
        if (isinstance(self.timer, QtCore.QTimer)):
            self.timer.deleteLater()
        
        # create new timer
        self.timer = QtCore.QTimer()
        self.timer.startTimer(self.COMMAND_POLL_INTERVAL)

        # start and connect new timer.
        self.timer.start()
        self.timer.timeout.connect(self.__recurrent)

    def __recurrent(self) -> None:
        """This is the main loop of the remote worker, it is run in the same thread amd process.
        it is run once every COMMAND_POLL_INTERVAL by the timer.
        """
        # only run if a command is given and the remote worker is ready to execute it.
        if (self.ready) and (self.command != ""):
            self.result: self.__Nothing | str = self.STR_TO_COMMAND[self.command[:self.COMMAND_RESERVED_LENGTH]](self.command[self.COMMAND_RESERVED_LENGTH:])
            self.command = '' # reset the command property when done.
        
        self.__set_timer() # set the timer for the next call.
    
    # ----------------------------------------initialization logic----------------------------------------
    def __set_ready(self) -> None:
        """Runs once when the page is loaded.
        """
        self.ready = True
    
    def __unset_ready(self) -> None:
        """Runs when page loading has started.
        """
        self.ready = False
    
    def __get_data(self, key: str, required: bool = False) -> typing.Any | typing.Literal[False] | typing.NoReturn:
        """Get Data From self.data, if the required key is not present then it will return False.

        Args:
            key (str): key for data in self.data
            required (bool, optional): if a key is required for the program to function properly, then an DataNotGiven
            exception is raised if it is not found. Instead of False being returned. Defaults to False.

        Raises:
            DataNotGiven: Exception is raised only when required=True and key is not found in self.data

        Returns:
            typing.Any: whatever the contents of self.data[key] are if key is found
            typing.Literal[False]: False if key is not found, and not required.
            typing.NoReturn: When key is not found and is required, then Data Not Given Exception is triggered.
        """
        if key in self.data:
            return self.data[key]
        else:
            if (required):
                raise DataNotGiven(f"Required Data Argument {key=} was not provided.")
            return False
    
    def __format_command(self, command: int | str) -> str:
        """Utility Command to format number to standardized command message format.

        Args:
            command (int | str): Command name/id

        Returns:
            str: formated/standardized command message format.
        """
        return (f"{{command:0>{self.COMMAND_RESERVED_LENGTH}}}").format(command=command)
    
    def __init__(self, data: dict) -> None:
        """The Constructor for Remote.

        Args:
            data (dict): Data Given to remote by the driver.
        """

        super().__init__()

        # initialize values.
        self.data = data
        self.ready = False
        self.command = ''
        self.result: self.__Nothing | str = self.__Nothing
        
        # set loadFinished to set self.ready
        self.loadFinished.connect(self.__set_ready)
        self.loadStarted.connect(self.__unset_ready)

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

        flags = self.__get_data("flags")

        if flags:
            # if additional window flags have been specified by the driver
            # then use them.
            for flag in flags:
                self.setWindowFlag(flag)

        window_mode = self.__get_data("window_mode")

        if window_mode:
            # if window mode is given then the corresponding WindowMode will be applied.
            match window_mode:
                
                # when the window_mode is given as Windowed,
                # the window will appear windowed with the minimum
                # width and height that QWebBrowser can have at init.
                case WindowMode.WINDOWED:
                    self.show()
                
                # with Windowed Bottom config, the window will always be below every other window.
                case WindowMode.WINDOWED_ON_BOTTOM:
                    self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnBottomHint)
                    self.show()
                
                # with Windowed Top, the window will always be above all other windows.
                case WindowMode.WINDOWED_ON_TOP:
                    self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                    self.show()
                
                # with Fullscreen the window will take up the entirity of the screen.
                # it will not show the top bar or the bottom windows bar.
                # the only way to get out of this window is either to
                # close it using Alt+F4 or Tab out with Alt+Tab
                case WindowMode.FULLSCREEN:
                    self.showFullScreen()
                
                # Acts like fullscreen but will always be below all other windows.
                case WindowMode.FULLSCREEN_ON_BOTTOM:
                    self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnBottomHint)
                    self.showFullScreen()
                
                # Acts like Fullscreen but will always be above all other windows.
                case WindowMode.FULLSCREEN_ON_TOP:
                    self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                    self.showFullScreen()
                
                # WIth WindowMode.MAXIMIZED config, the window will open maximized with the top bar and 
                # operating system specific UI(such as the windows bottom bar) still visible and interactable
                # same as Maximized with with maximized button on the top bar.
                case WindowMode.MAXIMIZED:
                    self.showMaximized()
                
                # Acts like Maximized but the window will appear above all other windows.
                case WindowMode.MAXIMIZED_ON_TOP:
                    self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                    self.showMaximized()
                
                # Acts like Maximized but the windows will appear below all other windows.
                case WindowMode.MAXIMIZED_ON_BOTTOM:
                    self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnBottomHint)
                    self.showMaximized()
                
                # This will open the window in a minized position, when unminimized it will be windowed.
                case WindowMode.MINIMIZED:
                    self.showMinimized()
        else: # if the config is not given, windowed will automatically be applied.
            self.show()
    
    # ------------------------------------------bootstrap logic-------------------------------------------
    @classmethod
    def _start(cls, data: dict):
        """Starts the main Qt loop

        Args:
            data (dict): Data given to remote, by driver
        """
        app = QtWidgets.QApplication([__file__])
        remote = cls(data)
        app.exec()
    
    @classmethod
    def start_process(cls, data: dict):
        """Create a process to run _start.

        Args:
            data (dict): Data given to remote, by driver

        Returns:
            _type_: _description_
        """
        proc = multiprocessing.Process(target=cls._start, args=(data,), daemon=True)
        proc.name = "Remote-"+("".join(random.sample(list("qwertyuiopasdfghjklzxcvbnm1234567890"), k=20)))
        proc.start()
        return proc