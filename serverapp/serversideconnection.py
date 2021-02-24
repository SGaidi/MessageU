import logging
import socketserver

from django.core.exceptions import ValidationError

from mysite import exceptions
from serverapp.models import Client, Message
from protocol.request import Request


class ServerSideConnection(socketserver.BaseRequestHandler):

    REQUEST_HEADER_LENGTH = Request.HEADER_LENGTH
    PAYLOAD_SIZE_START_BYTES = \
        Request.HEADER_LENGTH - Request.PAYLOAD_SIZE_LENGTH

    def _register_client(self, request):
        try:
            client = Client.objects.create()
        except ValidationError as e:
            raise exceptions.ClientValidationError()

    def _list_clients(self, request):
        return Client.objects.all()

    def _push_message(self, request):
        try:
            message = Message.objects.create()
        except ValidationError as e:
            raise exceptions.MessageValidationError()

    def _pull_messages(self, request):
        # TODO: with lock?
        messages = Message.objects.filter(to_client=request.client)
        # TODO: convert data to other type
        Message.objects.all().delete()
        return messages


    def _expect_request(self) -> bytes:
        packet_header_bytes = \
            self.request.recv(ServerSideConnection.REQUEST_HEADER_LENGTH)

        bytes_idx = 0
        header_fields = {}

        for header_field in Request.HEADER_FIELDS:
            python_type, field_length = \
                Request.FIELDS_TO_TYPE_AND_LENGTH[header_field]

            next_bytes_idx = bytes_idx + field_length
            field_bytes = packet_header_bytes[bytes_idx:next_bytes_idx]
            bytes_idx = next_bytes_idx

            logging.info(f'{header_field}: {python_type}:{field_length}')
            if python_type is int:
                converted_field = int.from_bytes(
                    bytes=field_bytes,
                    byteorder="little",
                    signed=False,
                )
            else:
                converted_field = python_type(field_bytes)
            header_fields[header_field] = converted_field

        payload_size = header_fields['payload_size']
        assert payload_size >= 0
        packet_payload_bytes = self.request.recv(payload_size)
        return packet_header_bytes + packet_payload_bytes

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self._expect_request()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        # just send back the same data, but upper-cased
        self.request.send(self.data.upper())
