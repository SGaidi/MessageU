import socket
from itertools import dropwhile

from common.utils import FieldsValues
from common.handlerbase import HandlerBase
from common.packer import Packer
from common.unpacker import Unpacker
from protocol.packets.request import Request
from protocol.packets.response import Response, PopMessagesResponse


class ClientHandler(HandlerBase):

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def _request_type_to_response(self, request: Request) -> Response:
        from protocol.packets.request import PushMessageRequest
        if isinstance(request, PushMessageRequest):
            response_type_name = 'PushMessageResponse'
        else:
            response_type_name = \
                request.__class__.__name__.replace('Request', 'Response')
        print(response_type_name)
        response_type = next(dropwhile(
            lambda response_t: response_t.__name__ != response_type_name,
            Response.ALL_RESPONSES,
        ))
        return response_type()

    def handle(self, request: Request, fields_to_pack: FieldsValues) -> FieldsValues:
        print("HANDLE")
        print(f"fields_to_pack {fields_to_pack}")
        request_bytes = Packer(request).pack(**fields_to_pack)
        print(f"request_bytes: {request_bytes}")
        socket.setdefaulttimeout(3)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            sock.send(request_bytes)

            response = self._request_type_to_response(request)
            p_type, fields, payload_iter = self._expect_packet(sock, response)

            # FIXME everything is already unpacked in _expect_packet
            # if isinstance(p_type, PopMessagesResponse):
            #     print("UNPACK MESSAGES")
            #     unpacker = Unpacker(p_type)
            #     messages_fields = unpacker.unpack_messages(payload_iter)
            #     print(f"messages fields: {messages_fields}")
            #     fields.update(messages_fields)

        return fields
