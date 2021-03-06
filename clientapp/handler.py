import logging

from common.utils import FieldsValues
from common.handlerbase import HandlerBase
from protocol.packets.request.base import Request
from protocol.packets.response.base import Response
from protocol.packets.response.responses import ALL_RESPONSES


class ClientHandler(HandlerBase):

    SOCKET_TIMEOUT = 5

    logger = logging.getLogger(__name__)

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def _request_to_response(self, request: Request) -> Response:
        """Maps the sent request from client to the expected response from
        server.

        Note the server response with PushMessageResponse to all
        PushMessageRequests."""
        from itertools import dropwhile
        from protocol.packets.request.messages import PushMessageRequest

        if isinstance(request, PushMessageRequest):
            response_type_name = 'PushMessageResponse'
        else:
            response_type_name = \
                request.__class__.__name__.replace('Request', 'Response')
        response_type = next(dropwhile(
            lambda response_t: response_t.__name__ != response_type_name,
            ALL_RESPONSES,
        ))

        return response_type()

    def handle(
            self, request: Request, fields_to_pack: FieldsValues,
    ) -> FieldsValues:
        """Sends a request to server and expects a response.

        Opens a connection to server, sends a request with the fields to pack,
          waits for a specific response from the server (according to the
          request).
        If there was no timeout, unpacks the response, and returns it's fields
          values. Otherwise, propagates the timeout error."""
        import socket
        from common.packer import Packer

        self.logger.debug(
            f"request: {request}, fields_to_pack: {fields_to_pack}")
        request_bytes = Packer(request).pack(**fields_to_pack)

        socket.setdefaulttimeout(ClientHandler.SOCKET_TIMEOUT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            sock.send(request_bytes)

            response = self._request_to_response(request)
            p_type, fields = self._expect_packet(sock, response)

        return fields
