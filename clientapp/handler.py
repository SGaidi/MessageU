import socket
from itertools import dropwhile
from typing import Dict, Any

from common.utils import Fields
from common.handlerbase import HandlerBase
from protocol.packets.request import Request
from protocol.packets.response import Response


class ClientHandler(HandlerBase):

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def handle(self, request: Request, fields_to_pack: Fields) -> Fields:
        request_bytes = request.pack(**fields_to_pack)
        socket.setdefaulttimeout(3)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            sock.send(request_bytes)

            response_type_name = \
                request.__class__.__name__[:-7] + 'Response'  # omit 'Request'
            response = next(dropwhile(
                lambda response_t: response_t.__name__ != response_type_name,
                Response.ALL,
            ))()

            p_type, header_fields, payload_fields = \
                self._expect_packet(sock, response)

        header_fields.update(payload_fields)
        return header_fields
