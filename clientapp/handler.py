import logging

from common.utils import FieldsValues
from common.handlerbase import HandlerBase
from protocol.packets.request.base import Request
from protocol.packets.response import Response


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
            Response.ALL_RESPONSES,
        ))
        return response_type()

    def handle(
            self, request: Request, fields_to_pack: FieldsValues,
    ) -> FieldsValues:
        import socket
        from common.packer import Packer
        logging.info(f"request: {request}, fields_to_pack: {fields_to_pack}")
        request_bytes = Packer(request).pack(**fields_to_pack)
        logging.info(f"request_bytes: {request_bytes}")

        socket.setdefaulttimeout(ClientHandler.SOCKET_TIMEOUT)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            sock.send(request_bytes)

            response = self._request_to_response(request)
            p_type, fields, payload_iter = self._expect_packet(sock, response)

            # FIXME: everything is already unpacked in _expect_packet
            # if isinstance(p_type, PopMessagesResponse):
            #     print("UNPACK MESSAGES")
            #     unpacker = Unpacker(p_type)
            #     messages_fields = unpacker.unpack_messages(payload_iter)
            #     print(f"messages fields: {messages_fields}")
            #     fields.update(messages_fields)

        return fields
