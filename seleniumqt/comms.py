"""
Author: Ansh Mathur
repo: https://www.github.com/Fakesum/seleniumqt
"""
import socket as _socket
import math as _math

class DriverComs:
    MAX_PACKET_SIZE = 1024

    def __init__(self, conn: _socket.socket) -> None:
        """Construct DriverComs."""
        self.conn = conn
    
    def send(self, data: bytes) -> None:
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.conn.send(str(_math.ceil(len(data)/self.MAX_PACKET_SIZE)).encode('utf-8'))
        self.conn.recv(1)
        self.conn.send(data)
    
    def recv(self) -> bytes:
        n_packets = int(self.conn.recv(self.MAX_PACKET_SIZE).decode('utf-8'))
        self.conn.send(b'1')
        
        packet = b''
        for _ in range(n_packets):
            packet += self.conn.recv(self.MAX_PACKET_SIZE)
        return packet