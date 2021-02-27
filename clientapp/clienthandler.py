import socket
from typing import Dict, Any

from protocol.handlerbase import HandlerBase
from protocol.request import Request
from protocol.response import *


class ClientHandler(HandlerBase):

    def _recv(self, buffer_size: int) -> bytes:
        return self.socket.recv(buffer_size)

    def _expect_response(self) -> bytes:
        return self._expect_packet(Response)

    def handle(self, request: Request, fields: Dict[str, Any]) -> Dict[str, Any]:
        request_bytes = request.pack(**fields)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.send(request_bytes)
        expected_response_type = \
            request.__class__.__name__[:-7] + 'Response'  # omit 'Request'
        response_type, header_fields, payload_fields = self._expect_response()
        if response_type != expected_response_type:
            raise ValueError(f"Got {response_type!r}, but expected "
                             f"{expected_response_type!r}.")
        header_fields.update(payload_fields)
        return header_fields
