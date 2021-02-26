import socket
from typing import Dict, Any

from protocol.handlerbase import HandlerBase
from protocol.request import Request
from protocol.response import Response


class ClientHandler(HandlerBase):

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def _recv(self, buffer_size: int) -> bytes:
        return self.socket.recv(buffer_size)

    def _expect_response(self) -> bytes:
        return self._expect_packet(Response)

    def handle(self, request: Request) -> Dict[str, Any]:
        request_bytes = request.pack()
        self.socket.send(request_bytes)
        concrete_packet_type, header_fields, payload_fields = self._expect_response()
        return payload_fields
