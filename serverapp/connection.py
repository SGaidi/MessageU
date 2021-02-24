from typing import List

from django.core.exceptions import ValidationError

from mysite import exceptions
from serverapp.models import Client, Message
from protocol.packetbase import PacketBase
from protocol.request import Request


class Connection:

    REQUEST_HEADER_LENGTH = PacketBase.REQUEST_HEADER_LENGTH
    PAYLOAD_SIZE_START_BYTES = \
        PacketBase.REQUEST_HEADER_LENGTH - PacketBase.PAYLOAD_SIZE_LENGTH

    BUFFER_SIZE = 1024

    def __init__(self, server_socket, client_socket, address):
        self.server_socket = server_socket
        self.client_socket = client_socket
        self.address = address

    def _recv(self, buffer_size: int) -> bytes:
        try:
            return self.server_socket.recv(buffer_size)
        except Exception as e:
            self.server_socket.close()
            raise exceptions.ConnectionException(
                "Failed to read from socket: {}".format(e))

    def _read_missing_bytes(self, missing_count: int) -> None:
        """Tries reading `missing_count` bytes from socket."""
        missing_bytes = b''
        while len(missing_bytes) < missing_count:
            recv_bytes = self._recv(missing_count)
            print("Received {} bytes".format(len(recv_bytes)))
            if recv_bytes == b'':
                raise exceptions.ConnectionException(
                    "Expected {} more bytes and did not receive them".format(
                        missing_count))
            missing_bytes += recv_bytes
        self.response += missing_bytes

    def _handle_response_length(self):
        """Validates length, updates idx, and receives any missing bytes"""
        if self.idx + Connection.REQUEST_HEADER_LENGTH > len(self.response):
            raise PeerMessage.Exception(
                "Corrupt response: {}".format(self.response))
        self.length = int.from_bytes(
            self.response[self.idx:self.idx + self.LENGTH_BYTES],
            byteorder="big")
        self.idx += self.LENGTH_BYTES
        if self.length + self.idx > len(self.response):
            self.logger.debug(
                "Message length ({}) is higher than current length in buffer ({})".format(
                    self.length, len(self.response) - self.idx
                ))
            self._read_missing_bytes(
                self.length + self.idx - len(self.response))

    def _determine_message_type(self):
        """messages factory-like method"""
        if self.length == 0:
            self.message = KeepAlive()
        else:
            # Messages that at least have an ID
            id = self.response[self.idx]
            payload = self.response[
                      self.idx + self.MESSAGE_ID_BYTES:self.idx + self.length]
            message_cls = id_to_message[id]
            self.logger.debug("'{}' message".format(message_cls.__name__))
            if message_cls in [Choke, UnChoke, Interested, NotInterested]:
                # All messages with id only and no payload
                if self.length != self.MESSAGE_ID_BYTES:
                    raise PeerMessage.Exception(
                        "{} messages should be of length 1 ({})".format(
                            type(message_cls).__name__, self.length
                        ))
                self.message = message_cls()
            else:
                self.message = message_cls.from_payload(payload)

    def _parse_response(self) -> List[PacketBase]:
        """returns list of messages objects
        tries reading whole messages, but not everything from socket"""
        self.response = self._recv(Connection.REQUEST_HEADER_LENGTH)
        print("Parsing response")
        packets = []
        self.idx = 0

        while self.idx < len(self.response):
            try:
                self._handle_response_length()
                self._determine_message_type()
            except (PeerMessage.Exception, KeyError) as e:
                self.logger.error(
                    "Failed to parse messages, dropping all read messages from buffer: {}".format(
                        e))
                return messages
            messages.append(self.message)
            self.idx += self.length
        return messages

    def _handle_messages(self, messages: list) -> List[Block]:
        """changes state machine according to received messages
        and appends any Block messages to be handled by GetPiece class"""
        block_messages = []
        for message in messages:
            self.logger.info("Handling {} message".format(message))
            if isinstance(message,
                          (KeepAlive, RequestBlock, CancelRequest, Port)):
                self.logger.debug(
                    "Ignoring message of type {} - not supported".format(
                        type(message).__name__))
            elif isinstance(message, Choke):
                self.peer_choking = True
            elif isinstance(message, UnChoke):
                self.peer_choking = False
            elif isinstance(message, Interested):
                self.peer_interested = True
            elif isinstance(message, NotInterested):
                self.peer_interested = False
            elif isinstance(message, Block):
                block_messages.append(message)
        return block_messages

    def expect_blocks(self) -> List[Block]:
        """returns a list of any received blocks"""
        messages = self._parse_response()
        return self._handle_messages(messages)

    def send(self, message: bytes):
        """wrapper of socket.send, applying BitTorrent specifications with `choking` and `interested` values"""
        try:
            self.socket.send(message)
        except Exception as e:
            self.socket.close()
            raise PeerConnection.Exception(
                "Failed to send message to socket: {}".format(e))



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
            self._recv(buffer_size=Connection.REQUEST_HEADER_LENGTH)

        bytes_idx = 0
        header_fields = {}

        for header_field in Request.REQUEST_HEADER_FIELDS:
            python_type, field_length = \
                PacketBase.FIELDS_TO_TYPE_AND_LENGTH[header_field]

            next_bytes_idx = bytes_idx + field_length
            field_bytes = packet_header_bytes[bytes_idx:next_bytes_idx]
            bytes_idx = next_bytes_idx

            converted_field = python_type(field_bytes)
            header_fields[header_field] = converted_field

        payload_size = header_fields['payload_size']
        assert payload_size >= 0
        packet_payload = self._recv(buffer_size=self.payload_size)

    def handle(self):

        while True:
            request = self._expect_request()
