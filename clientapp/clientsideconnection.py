import socket

from protocol.request import Request
from protocol.response import Response


class ClientSideConnection:

    RESPONSE_HEADER_LENGTH = Response.HEADER_LENGTH
    PAYLOAD_SIZE_START_BYTES = \
        Response.HEADER_LENGTH - Response.PAYLOAD_SIZE_LENGTH

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def _expect_response(self) -> bytes:
        packet_header_bytes = \
            self._recv(buffer_size=ClientSideConnection.RESPONSE_HEADER_LENGTH)

        bytes_idx = 0
        header_fields = {}

        for header_field in Response.HEADER_FIELDS:
            python_type, field_length = \
                Response.FIELDS_TO_TYPE_AND_LENGTH[header_field]

            next_bytes_idx = bytes_idx + field_length
            field_bytes = packet_header_bytes[bytes_idx:next_bytes_idx]
            bytes_idx = next_bytes_idx

            converted_field = python_type(field_bytes)
            header_fields[header_field] = converted_field

        payload_size = header_fields['payload_size']
        assert payload_size >= 0
        packet_payload_bytes = self._recv(buffer_size=self.payload_size)
        return packet_header_bytes + packet_payload_bytes

    def handle(self, request: Request):

        while True:
            response = self._expect_response()
