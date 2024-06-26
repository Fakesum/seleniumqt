"""module to store functions which are used to run tests on the module."""

# import logger
from .logger import logger

# import the Driver
from .driver import Driver
from .comms import DriverComs

# import socket, threading & threading for test flask server
import socket
import threading
import flask


# an easy way to create objects.
import types

# for unit tests.
import unittest
import time
import typing
import os
import random

# a url object in order to compare whether two urls are equal.
from urllib.parse import urlparse, parse_qsl, unquote_plus


class Url(object):
    """compared two or more urls.

    without regard to the vagaries of encoding, escaping, and ordering
    of parameters in query strings."""

    def __init__(self, url):
        self.__url = url
        parts = urlparse(url)
        _query = frozenset(parse_qsl(parts.query))
        _path = unquote_plus(parts.path)
        parts = parts._replace(query=_query, path=_path)
        self.parts = parts
    
    def __repr__(self):
        return self.__url

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.parts == other.parts

    def __hash__(self):
        return hash(self.parts)

class TestDriverComsDriver(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.daemon = True
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.bind(('localhost', 0))

        self.port = self.conn.getsockname()[1]
        self._commands = []
        self._result = None

        self._conn = None

        self.start()
    
    def run(self):
        self.conn.listen()
        conn, _ = self.conn.accept()
        
        self._conn = DriverComs(conn)

        while conn:
            for command in self._commands:
                self._conn.send(command.encode('utf-8'))
                self._result = self._conn.recv().decode('utf-8')
            self._commands = []
            time.sleep(1)

class TestDriverComsRemote(threading.Thread):
    def __init__(self, port):
        super().__init__(daemon=True)
        self.daemon = True
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect(('localhost', port))
        self._conn = DriverComs(self.conn)

        self.start()
    
    def run(self):
        while self.conn:
            command = self._conn.recv()
            command = command.decode('utf-8')
            self._conn.send("".join(reversed(command)))

class TestDriverComs(unittest.TestCase):

    driver = None
    remote = None

    def __ensure_connection(self):
        if (self.driver == None) or (self.remote == None):
            self.driver = TestDriverComsDriver()
            self.remote = TestDriverComsRemote(self.driver.port)
        self.driver._result = None

    def test_1(self):
        self.__ensure_connection()

        test_string = "".join([random.choice("qwertyuiopasdfghjklzxcvbnm1234567890") for i in range(4096)])

        self.driver._commands.append(test_string)
        
        while self.driver._result == None:
            time.sleep(1)
        
        self.assertEqual(self.driver._result, "".join(reversed(test_string)))

class TestServerObject:
    """Store test server variables in one object."""

    app: flask.Flask | typing.Any = None
    flask_port: flask.Flask | typing.Any = None
    thread: threading.Thread | typing.Any = None

    clicked: bool = False

class Tests(unittest.TestCase):
    """run tests on seleniumqt."""

    driver: typing.Any | Driver = None
    server: typing.Any | TestServerObject = None

    def __ensure_driver(self):
        """ensure that the driver is running."""
        if self.driver == None:
            logger.info("Starting Driver Init.")
            self.driver = Driver()
            logger.info("Done driver Init.")
        else:
            logger.trace("Driver was already initialized")

    def __find_free_port(self):
        """give a free port which is not currently is use."""
        with socket.socket() as sock:
            sock.bind(("localhost", 0))
            sock_name = sock.getsockname()[1]
            logger.info(f"Free Socket given: {sock_name=}")
            return sock_name

    def __ensure_server(self):
        """ensure that the test flask server is working."""
        if self.server == None:
            self.server = types.ModuleType(
                "self.server", "container for test server."
            )

            self.server.app = flask.Flask(__name__)
            self.server.clicked = False

            @self.server.app.route("/")
            def main():
                """Give the html for the home page of the test server"""
                return flask.render_template(
                    os.path.join(
                        os.path.dirname(__file__),
                        "test_resources/test_main.html",
                    )
                )

            @self.server.app.route("/clicked")
            def _clicked():
                """run if the button was on the home page."""
                self.server.clicked = True

            self.server.flask_port = str(self.__find_free_port())

            self.server.thread = threading.Thread(
                target=self.server.app.run,
                args=(self.server.flask_port,),
                daemon=True,
            )

            logger.info("Starting flask app.")
            self.server.thread.start()
        else:
            if self.server.clicked:
                logger.warning("self.server.clicked is already set, it will be unset.")
                self.server.clicked = False
            logger.trace("self.server was already started.")

    def test_init_0(self):
        """test that the init for the driver is working.

        this should be the first test to be conducted."""
        self.__ensure_driver()
        logger.success("Passed test_init_0")

    def test_open(self):
        """test that the open function which opens a new url is working"""
        self.__ensure_driver()
        self.__ensure_server()

        flask_url = f"http://localhost:{self.server.flask_port}/"

        self.driver.open(flask_url)

        logger.trace(f"{self.driver.page_html()=}")

        self.assertEqual(
            Url(self.driver.current_url()),
            Url(flask_url),
            "page url was not changed.",
        )

        logger.success("Passed test_open")

    def test_click(self):
        """test that clicking on a button is working."""
        self.__ensure_driver()
        self.__ensure_server()

        self.driver.open(f"http://localhost:{self.server.flask_port}/")
        self.driver.click(".only-button")

        st = time.time()
        while not self.server.clicked:
            if (time.time() - st) < 3:
                self.fail("Took too long to click on button, more than 10 seconds!")

        logger.success("Passed test_click")

    def test_click_xpath(self):
        """test that clicking on a button is working, when used with xpath"""
        self.__ensure_driver()
        self.__ensure_server()

        self.driver.open(f"http://localhost:{self.server.flask_port}/")
        self.driver.click("//button[@class = 'only-button']", Driver.XPATH)

        st = time.time()

        while not self.server.clicked:
            if (time.time() - st) < 3:
                self.fail("Took too long to click on button, more than 10 seconds!")
        
        logger.success("Passed test_click_xpath")

    def test_hide_and_show_1(self):
        self.__ensure_driver()

        if os.getenv("SELENIUMQT_CONTRIB"):
            self.skipTest("This test requires manual interaction from a user, can only be conducted on a CONTRIB device. set SELENIUMQT_CONTRIB=1 in your env to set device as CONTRIB device")
            return
        
        self.driver.open("https://www.google.com/")
        self.driver.hide_window()
        if input("Was the window hidden :- ").lower() in ['n', 'no']:
            logger.error("The window was not hidden")
            self.fail("According to the user, the window was not hidden")
        
        self.driver.show_window()

        if input("was the window shown again :- ").lower() in ['n', 'no']:
            logger.error("The window was not shown again")
            self.fail("According to the user, the window was not shown again.")
        
        logger.success("Passed test_hide_and_show")


def main():
    """Run unit Tests."""
    logger.info("starting tests")
    unittest.main(verbosity=2)