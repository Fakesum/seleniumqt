"""module to store functions which are used to run tests on the module."""

from .logger import logger
from .driver import Driver
import socket
import threading
import flask
import types
import unittest
import time
import typing
import os

from urllib.parse import urlparse, parse_qsl, unquote_plus
    
class Url(object):
    '''compared two or more urls.

    without regard to the vagaries of encoding, escaping, and ordering
    of parameters in query strings.'''

    def __init__(self, url):
        parts = urlparse(url)
        _query = frozenset(parse_qsl(parts.query))
        _path = unquote_plus(parts.path)
        parts = parts._replace(query=_query, path=_path)
        self.parts = parts

    def __eq__(self, other):
        return self.parts == other.parts

    def __hash__(self):
        return hash(self.parts)

class TestServerObject:
    """Store test server variables in one object."""
    app: flask.Flask | typing.Any = None
    flask_port: flask.Flask | typing.Any = None
    thread: threading.Thread | typing.Any = None

    clicked: bool = False

class Tests(unittest.TestCase):
    """run tests on seleniumqt."""
    driver: typing.Any | Driver= None
    server: typing.Any | TestServerObject = None

    def __ensure_driver(self):
        """ensure that the driver is running."""
        if (self.driver == None):
            logger.info("Starting Driver Init.")
            self.driver = Driver()
            logger.info("Done driver Init.")
        else:
            logger.trace("Driver was already initialized")
    
    def __find_free_port(self):
        """give a free port which is not currently is use."""
        with socket.socket() as sock:
            sock.bind(('localhost', 0))
            sock_name = sock.getsockname()[1]
            logger.info(f'Free Socket given: {sock_name=}')
            return sock_name
    
    def __ensure_server(self):
        """ensure that the test flask server is working."""
        if self.server == None:
            self.server = types.ModuleType("self.server", "container for test server.")
            
            self.server.app = flask.Flask(__name__)
            self.server.clicked = False

            @self.server.app.route("/")
            def main():
                """Give the html for the home page of the test server"""
                return flask.render_template(os.path.join(os.path.dirname(__file__), "test_resources/test_main.html"))

            @self.server.app.route("/clicked")
            def _clicked():
                """run if the button was on the home page."""
                self.server.clicked = True

            self.server.flask_port = str(self.__find_free_port())

            self.server.thread = threading.Thread(target=self.server.app.run, args=(self.server.flask_port,),daemon=True)

            logger.info("Starting flask app.")
            self.server.thread.start()
        else:
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

        self.driver.open(f"https://localhost:{self.server.flask_port}")

        self.assertEqual(Url(self.driver.current_url()), Url("https://www.google.com"), "page url was not changed.")

        logger.success("Passed test_open")
    
    def test_click(self):
        """test that clicking on a button is working."""
        self.__ensure_driver()
        self.__ensure_server()

        self.driver.open(f"http://localhost:{self.server.flask_port}/")
        self.driver.click(".only-button")
        
        st = time.time()
        while (not self.server.clicked):
            if ((time.time() - st) < 10):
                raise TimeoutError("Took too long to click on button, more than 10 seconds!")
        
        logger.success("Passed test_click")

def main():
    """Run unit Tests."""
    logger.info("starting tests")
    unittest.main(verbosity=2)