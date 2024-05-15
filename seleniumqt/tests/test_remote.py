import unittest
import socket
import threading
import multiprocessing
import time

from seleniumqt.logger import logger
from seleniumqt.remote import Remote

remote_proc: multiprocessing.Process = None
commands = []


def get_free_sock() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        return sock.getsockname()[1]


test_server_ready = False


def run_command(com):
    while not test_server_ready:
        time.sleep(0.1)

    commands.append(com)

    while commands != []:
        time.sleep(0.1)


def _test_server(_sock):
    global test_server_ready
    logger.trace("Starting test server.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", _sock))

        test_server_ready = True
        sock.listen()
        conn, _ = sock.accept()

        logger.trace("Test server started.")
        while conn:
            while commands == []:
                time.sleep(1)
            logger.trace("Starting command execution.")
            for command in commands:
                logger.debug(f"Sending command: {command=}")
                conn.send(command.encode("utf-8"))
                message = conn.recv(1024)
                message = message.decode("utf-8")
                logger.debug(
                    f"Message recieved from remote: {message=} {command=}"
                )
            commands = []
        logger.trace("Connection closed by remote.")
    logger.trace("test server closed.")


def start_test_server():
    free_sock = get_free_sock()
    threading.Thread(
        target=_test_server, args=(free_sock,), daemon=True
    ).start()
    return free_sock


testing_server_proc = start_test_server()


def _ensure_remote_proc():
    global remote_proc, testing_server_proc
    if remote_proc == None:
        testing_server_proc = start_test_server()
        time.sleep(1)  # give it a second to setup the server just in case.
        remote_proc = Remote.start_process(
            {
                "starting_url": "http://httpbin.org/ip",
                "connecting_port": testing_server_proc,
            }
        )


class TestRemote(unittest.TestCase):
    def test_init_1(self):
        global remote_proc
        logger.trace("Starting Remote Initialization.")
        remote_proc = Remote.start_process(
            {
                "starting_url": "http://httpbin.org/ip",
                "connecting_port": testing_server_proc,
            }
        )

        logger.debug(
            f"{remote_proc.pid=}, {remote_proc.is_alive()=}, {remote_proc.name=}"
        )

        self.assertTrue(remote_proc.is_alive())

    def test_close_2(self):
        run_command("06")  # this will give the close command.
        st = time.time()

        while ((time.time() - st) < 10) and remote_proc.is_alive():
            time.sleep(0.1)

        if (time.time() - st) >= 10:
            remote_proc.kill()
            self.fail("took too long to close remote. more than 10 seconds.")

        self.assertFalse(remote_proc.is_alive())

        if not remote_proc.is_alive():
            remote_proc = None


if __name__ == "__main__":
    unittest.main()
