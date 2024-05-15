"""module containing remote."""

# ---------------------------------------------------
# author: Ansh Mathur
# gtihub: https://github.com/Fakesum
# repo: https://github.com/Fakesum/ TODO: THIS
# ---------------------------------------------------

# import python std library
import random as _random
import time as _time
import socket as _socket
import typing as _typing
import threading as _threading
import enum as _enum
import multiprocessing as _multiprocessing
import importlib as _importlib

# import Qt
from PyQt6 import (
    QtCore as _QtCore,
    QtWidgets as _QtWidgets,
    QtWebEngineWidgets as _QtWebEngineWidgets,
    QtWebEngineCore as _QtWebEngineCore,
)

# import Some Custom Exceptions
from .exception import (
    JavascriptException,
    InvalidSelectorType,
    NullPageError,
    InternalWidgitNotFound,
    SetPageEror,
    DataNotGiven
)

# import logger
from .logger import logger


class WindowMode(_enum.IntEnum):
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


class Remote(_QtWebEngineWidgets.QWebEngineView):

    """The Remote Qt Session Host.

    # Usage

    How to use this class by function:
    ## start
    ```python
    proc: _multiprocessing.Process = Remote.start_process({
        # required
        "starting_url": ..., # url/QWebEnginePage where the remote will start
        "connection_port": ..., # the port where the remote will connect to, and listen to commands.

        # optional
        "window_mode": ..., # one of the WindowMode _enum
        "flags": ..., # list of qt.WindowType Flags.
        "wait_for_load": ... # True or False.
    })
    # this will return the process Object where the Remote is running.
    ```

    """

    # ---------------------------------------------constants----------------------------------------------
    # define class Scope Global constants.
    COMMAND_POLL_INTERVAL: int = 100  # once every 100 milliseconds.
    COMMAND_RESERVED_LENGTH: int = 2
    CONSOLE_POLL_TIME = 1000  # once every second.

    # a special None Type, this is used
    # to distinguish whether a command
    # runner has returned None or wether
    # Nothing has yet been given.
    class __Nothing:
        pass  # it is `__` private so that it can't be given as custom return of some kind.

    # ---------------------------------------------javascript---------------------------------------------
    JAVASCRIPT_GET_ELEMENT_POS_CSS = """
    (()=>{{
        try{{
            var elm = document.querySelector({css_selector});
            var box = elm.getBoundingClientRect();
            return (box.right+((box.right-box.left)/2)).toString()+','+(box.top+((box.bottom-box.top)/2)).toString();
        }} catch (err) {{
            return 'JavascriptException, exception: '+err.message;
        }}
    }})()
    """

    JAVASCRIPT_GET_ELEMENT_POS_XPATH = """
    (()=>{{
        try{{
            var elm = document.evaluate({xpath_selector}, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            var box = elm.getBoundingClientRect();
            return (box.right+((box.right-box.left)/2)).toString()+','+(box.top+((box.bottom-box.top)/2)).toString();
        }} catch(err){{
            return 'JavascriptException, exception: '+err.message;
        }}
    }})
    """

    JAVASCRIPT_EXECUTION_SHELL = """
    (() =>{{
        try {{
            {script};
        }} catch (err) {{
            return 'JavascriptException, exception: '+err.message;
        }}
    }})();
    """

    CONSOLE_JAVASCRIPT = """
    (()=>{{
        try{{
            if (!("logs" in console)){{
                console.slogs = console.log.bind(console);
                console.logs = []
                console.log = ((...args)=>{{
                    console.logs.push(args);
                    console.slogs(...args);
                }});
            }};
            return console.logs;
        }} catch (err){{
            return "JavascriptException"+err.message;
        }}
    }})()
    """

    # -----------------------------------------utility functions------------------------------------------

    def __raise(self, e: Exception):
        logger.exception(str(e))
        self.__raise(e)

    def __get_element_pos_callback(self, res):
        """Set Callback for getting the position of elements using javascript, for __click_element function.

        Args:
        ----
            res (str): the resulting point.

        """
        res = str(res)  # convert the res to be for sure str
        # in case it is given in some other format.

        if res.startswith("JavascriptException"):
            self.__raise(JavascriptException(res, self.__console))
        self._element_pos = res.split(",")

    def __get_element_pos(
        self,
        _type: _typing.Literal["css "] | _typing.Literal["xpath"] | str,
        selector: str,
    ) -> None:
        """Set callback to Get the position of Element by selector.

        Args:
        ----
            _type (_typing.Literal['css '] | _typing.Literal['xpath']): type of selector, either css or xpath
            selector (str): selector to get the element.

        """
        match _type:
            case "css ":
                self.__ensure_page().runJavaScript(
                    self.JAVASCRIPT_GET_ELEMENT_POS_CSS.format(
                        css_selector=selector
                    ),
                    resultCallback=self.__get_element_pos_callback,
                )
            case "xpath":
                self.__ensure_page().runJavaScript(
                    self.JAVASCRIPT_GET_ELEMENT_POS_XPATH.format(
                        xpath_selector=selector
                    ),
                    resultCallback=self.__get_element_pos_callback,
                )
            case _:
                self.__raise(InvalidSelectorType(f"{_type=}"))

    def __update_console(self, console):
        console = str(console)
        self.__console = console

    def __show(self) -> None:
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
                    self.setWindowFlag(
                        _QtCore.Qt.WindowType.WindowStaysOnBottomHint
                    )
                    self.show()

                # with Windowed Top, the window will always be above all other windows.
                case WindowMode.WINDOWED_ON_TOP:
                    self.setWindowFlag(
                        _QtCore.Qt.WindowType.WindowStaysOnTopHint
                    )
                    self.show()

                # with Fullscreen the window will take up the entirity of the screen.
                # it will not show the top bar or the bottom windows bar.
                # the only way to get out of this window is either to
                # close it using Alt+F4 or Tab out with Alt+Tab
                case WindowMode.FULLSCREEN:
                    self.showFullScreen()

                # Acts like fullscreen but will always be below all other windows.
                case WindowMode.FULLSCREEN_ON_BOTTOM:
                    self.setWindowFlag(
                        _QtCore.Qt.WindowType.WindowStaysOnBottomHint
                    )
                    self.showFullScreen()

                # Acts like Fullscreen but will always be above all other windows.
                case WindowMode.FULLSCREEN_ON_TOP:
                    self.setWindowFlag(
                        _QtCore.Qt.WindowType.WindowStaysOnTopHint
                    )
                    self.showFullScreen()

                # WIth WindowMode.MAXIMIZED config, the window will open maximized with the top bar and
                # operating system specific UI(such as the windows bottom bar) still visible and interactable
                # same as Maximized with with maximized button on the top bar.
                case WindowMode.MAXIMIZED:
                    self.showMaximized()

                # Acts like Maximized but the window will appear above all other windows.
                case WindowMode.MAXIMIZED_ON_TOP:
                    self.setWindowFlag(
                        _QtCore.Qt.WindowType.WindowStaysOnTopHint
                    )
                    self.showMaximized()

                # Acts like Maximized but the windows will appear below all other windows.
                case WindowMode.MAXIMIZED_ON_BOTTOM:
                    self.setWindowFlag(
                        _QtCore.Qt.WindowType.WindowStaysOnBottomHint
                    )
                    self.showMaximized()

                # This will open the window in a minized position, when unminimized it will be windowed.
                case WindowMode.MINIMIZED:
                    self.showMinimized()
        else:  # if the config is not given, windowed will automatically be applied.
            self.show()

    def __ensure_page(self) -> _QtWebEngineCore.QWebEnginePage:
        page: _typing.Any = self.page()
        if page == None:
            self.__raise(NullPageError("Page was Null"))
        else:
            return page

    # ------------------------------------command execution functions-------------------------------------
    @logger.catch(reraise=True)
    def __run_js(self, script_file_name: str) -> bool:
        """Execute the Given Javascript file.

        Args:
        ----
            script_file_name (str): the path to the javascript file which is to be run.

        """
        # load script from file.
        try:
            script = open(script_file_name, "r").read()
        except Exception:
            logger.exception(
                f"Threre was a problem when reading the script file: {script_file_name=}"
            )
            self.__raise(IOError(f"File: {script_file_name=} not found."))

        def return_callback(result: str):
            result = str(
                result
            )  # convert the result to str if it is given in some other format.

            if result.startswith("JavascriptException"):
                logger.exception("This Here.")
                self.__raise(JavascriptException(
                    "There was a problem with the javascript",
                    result,
                    str(self.__console),
                ))

            self.result: _typing.Any = result  # type: ignore

        logger.info(f"Running {script=}")
        logger.trace(f"Starting to run {script=}")

        self.__ensure_page().runJavaScript(
            self.JAVASCRIPT_EXECUTION_SHELL.format(script=script),
            resultCallback=return_callback,
        )

        logger.trace(f"Done Running {script=}")
        return True

    @logger.catch(reraise=True)
    def __go_to_url(self, url: str) -> bool:
        """Change the url as per the argument given with setUrl.

        Args:
        ----
            url (str): the url given by the driver.

        """
        logger.info(
            f"Changing Url to {url=} from {self.__ensure_page().url().toString()=}"
        )

        logger.trace(f"Setting Url to {url=}")
        self.setUrl(_QtCore.QUrl(url))
        logger.trace(f"Setting Url to {url=}")

        self.result = "done"

        return True

    @logger.catch(reraise=True)
    def __click_element(
        self, selector: str
    ) -> bool:  # noqa - untested #TODO: debug here.
        """Send a QMouseClick Event to the QApplication, at the point of the element's position.

        The element is gotten from the selector.

        Args:
        ----
            selector (str): Selector for the element must be in the format: '<4-letter-type-code, ex: 'css ','xpath'><the-actual-selector>'

        """
        if self._element_pos == None:
            if not self._element_pos_started:
                self._element_pos_started: bool = True
                self.__get_element_pos(selector[:4], selector[4:])
            return False

        self._element_pos = None
        self._element_pos_started = False

        click = _QtCore.QEvent(_QtCore.QEvent.Type.MouseButtonPress)
        _QtWidgets.QApplication.postEvent(self, click)
        self.result = "done"

        return True

    @logger.catch(reraise=True)
    def __hide(self, arg: _typing.Literal[""] = "") -> bool:
        self.hide()
        self.result = "done"
        return True

    @logger.catch(reraise=True)
    def __show_window(self, arg: _typing.Literal[""] = "") -> bool:
        self.__show()
        self.result = "done"
        return True

    @logger.catch(reraise=True)
    def __set_page(self, page_script: str) -> bool:
        try:
            self.setPage(_importlib.import_module(page_script).page)
        except Exception:
            self.__raise(SetPageEror(f"{page_script=}"))
        self.result = "done"
        return True

    @logger.catch(reraise=True)
    def __close(self, arg: _typing.Literal[""] = "") -> _typing.NoReturn:
        self.close()
        self.conn.close()
        raise SystemExit(0)

    @logger.catch(reraise=True)
    def __current_url(self):
        self.result = self.__ensure_page().url().toString()
        return True

    # -------------------------------------driver communication logic-------------------------------------
    def remote_client(self) -> None:
        """Poll self.conn.
        
        This function runs in a seperate thread, here it continously listens for any
        commands that are given by the driver, and updates the self.command property
        accordingly.
        """
        logger.info("Started Remote Command Client")

        while self.conn:
            message: bytes = self.conn.recv(1024)
            self.command = message.decode("utf-8")
            logger.info(
                f"Executing Command: {self.command[:self.COMMAND_RESERVED_LENGTH]} {self.command[self.COMMAND_RESERVED_LENGTH:]}"
            )

            while self.result == self.__Nothing:
                _time.sleep(0.5)

            self.conn.send(
                self.result.encode("utf-8") if self.result != None else b"done"
            )
            self.result = self.__Nothing

        logger.warning("Closing Remote Client.")
        self.close()  # when the connection is close we want qt to close as well.

    def __set_timer(self) -> None:
        """Set slef.timer for recurrent function.
        
        This function deletes any exsiting timers and sets a new timer for
        COMMAND_POLL_INTERVAL _time, upon the completion of which the recurrent function
        is run.
        """
        # delete existing timer
        if isinstance(self.timer, _QtCore.QTimer):
            self.timer.deleteLater()

        # create new timer
        self.timer: _QtCore.QTimer = _QtCore.QTimer()
        self.timer.startTimer(self.COMMAND_POLL_INTERVAL)

        # start and connect new timer.
        self.timer.start()
        self.timer.timeout.connect(self.__recurrent)

    def __recurrent(self) -> None:
        """Poll to check for commands.

        runs in the same thread and process as qt. it is run once every COMMAND_POLL_INTERVAL by the timer.
        """
        # only run if a command is given and the remote worker is ready to execute it.
        if (self.ready) and (self.command != ""):
            if self.STR_TO_COMMAND[
                self.command[: self.COMMAND_RESERVED_LENGTH]
            ][1](self.command[self.COMMAND_RESERVED_LENGTH :]):
                self.command = ""  # reset the command property when done.

        self.__set_timer()  # set the timer for the next call.

    def __console_recurrent(self) -> None:
        self.__ensure_page().runJavaScript(
            self.CONSOLE_JAVASCRIPT, resultCallback=self.__update_console
        )

        # reset console recurrent.
        if isinstance(self._console_timer, _QtCore.QTimer):
            self._console_timer.deleteLater()
            self._console_timer = None
        self._console_timer = _QtCore.QTimer()
        self._console_timer.startTimer(self.CONSOLE_POLL_TIME)

        self._console_timer.start()
        self._console_timer.timeout.connect(self.__console_recurrent)

    # ----------------------------------------initialization logic----------------------------------------
    def __set_ready(self) -> None:
        """Run once when the page is loaded.
        
        to set self.ready and log that the page is done loading.
        """
        self.ready = True
        logger.debug(f"Done Loading, {self.__ensure_page().url().toString()=}")

    def __unset_ready(self) -> None:
        """Run when page loading has started.
        
        to set self.ready and log that the page has started loading.
        """
        self.ready = False
        logger.debug(
            f"Starting Loading, {self.__ensure_page().url().toString()=}"
        )

    def __get_data(
        self, key: str, required: bool = False
    ) -> _typing.Any | _typing.Literal[False] | _typing.NoReturn:
        """Get Data From self.data, if the required key is not present then it will return False.

        Args:
        ----
            key (str): key for data in self.data
            required (bool, optional): if a key is required for the program to function properly, then an DataNotGiven
            exception is raised if it is not found. Instead of False being returned. Defaults to False.

        Raises:
        ------
            DataNotGiven: Exception is raised only when required=True and key is not found in self.data

        Returns:
        -------
            _typing.Any: whatever the contents of self.data[key] are if key is found
            _typing.Literal[False]: False if key is not found, and not required.
            _typing.NoReturn: When key is not found and is required, then Data Not Given Exception is triggered.

        """
        if key in self.data:
            logger.debug(f"{key=} {self.data[key]=}")
            return self.data[key]
        else:
            if required:
                self.__raise(DataNotGiven(
                    f"Required Data Argument {key=} was not provided."
                ))
            return False

    def __format_command(self, command: int | str) -> str:
        """Format number to standardized command message format.

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

    def __init__(self, data: dict) -> None:
        """Construct for Remote.

        Args:
        ----
            data (dict): Data Given to remote by the driver.

        """
        super().__init__()

        # initialize values.
        self.data = data
        self.ready = False

        # variable to record the console.
        self.__console = []
        self._console_timer: _typing.Any = None

        # propogation of commands.
        self.command = ""
        self._element_pos = None
        self._element_pos_started: bool = False

        # the result of the command given
        self.result: self.__Nothing | str | _typing.Any = self.__Nothing

        # set loadFinished to set self.ready
        self.loadFinished.connect(self.__set_ready)
        self.loadStarted.connect(self.__unset_ready)

        self.timer: _QtCore.QTimer = None

        self.setUrl(_QtCore.QUrl(self.__get_data("starting_url", True)))

        # connect to the driver
        self.conn: _socket.socket = _socket.socket(
            _socket.AF_INET, _socket.SOCK_STREAM
        )
        self.conn.connect(
            ("localhost", self.__get_data("connection_port", True))
        )

        # start the function which will recieve commands from the driver.
        self.__remote_client_thread = _threading.Thread(
            target=self.remote_client, daemon=True
        )
        self.__remote_client_thread.name = "remote-client"
        self.__remote_client_thread.start()

        # a dict to convert from the command given in the message
        # to the function which will run it.
        self.STR_TO_COMMAND: dict[str, tuple[str, _typing.Callable]] = {
            self.__format_command(0): ("js", self.__run_js),
            self.__format_command(1): ("url", self.__go_to_url),
            self.__format_command(2): ("click", self.__click_element),
            self.__format_command(3): ("hide", self.__hide),
            self.__format_command(4): ("show", self.__show_window),
            self.__format_command(5): ("page", self.__set_page),
            self.__format_command(6): ("close", self.__close),
            self.__format_command(7): ("current_url", self.__current_url)
        }

        logger.debug(f"{self.STR_TO_COMMAND=}")

        flags = self.__get_data("flags")

        if flags:
            # if additional window flags have been specified by the driver
            # then apply the specifed flags.
            for flag in flags:
                self.setWindowFlag(flag)

        self.__show()

        logger.trace("Starting Main Loop Timer.")
        logger.debug(f"{self.COMMAND_POLL_INTERVAL=}")
        self.__set_timer()  # set the starting timer for the main loop
        # this will call __recursive function every COMMAND_POLL_INTERVAL duration.

    # ------------------------------------------bootstrap logic-------------------------------------------
    @classmethod
    def _start(cls, data: dict):
        """Start the main Qt loop.

        Args:
        ----
            data (dict): Data given to remote, by driver

        """
        app = _QtWidgets.QApplication([__file__])
        
        remote = cls(data) # noqa: F841 # this is because qt works in weird and mysterious ways.

        logger.info("Starting Main Qt Loop.")
        return_code = app.exec()
        logger.warning(f"Exiting with return_code: {return_code}")
        raise SystemExit(return_code)

    @classmethod
    def start_process(cls, data: dict):
        """Create a process to run _start.

        Args:
        ----
            data (dict): Data given to remote, by driver

        Returns:
        -------
            _multiprocessing.Process: The _multiprocessing.Process where the remote is run.

        """
        proc = _multiprocessing.Process(
            target=cls._start, args=(data,), daemon=True
        )
        proc.name = "Remote-" + (
            "".join(
                _random.sample(
                    list("qwertyuiopasdfghjklzxcvbnm1234567890"), k=20
                )
            )
        )
        logger.debug(f"Starting {proc.name=}")
        logger.trace(f"Starting {proc.name=}")
        proc.start()
        logger.trace(f"Started {proc.name=}")
        return proc


__all__ = ["Remote"]
