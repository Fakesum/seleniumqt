from controllable_qt import Remote
import socket
import time
import threading

def dummy_server(sock):
    sock.listen()
    conn, _ =sock.accept()
    while conn:
        time.sleep(1)

if __name__ == "__main__":
    sock =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))

    threading.Thread(target=dummy_server, args=(sock,), daemon=True).start()

    remote_proc = Remote.start_process({
        "starting_url": "https://www.google.com",
        "connection_port": sock.getsockname()[1]
    })

    input("...")