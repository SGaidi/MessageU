import abc
import logging
from typing import Type, Tuple, Union, Iterator

from common.utils import FieldsValues
from common.exceptions import FieldBaseValueError, PacketBaseValueError
from common.unpacker import Unpacker
from protocol.packets.base import PacketBase
from protocol.packets.request.base import Request
from protocol.packets.request.requests import ALL_REQUESTS
from protocol.packets.request.messages import PushMessageRequest, \
    ALL_REQUEST_MESSAGES
from protocol.packets.response.base import Response
from protocol.packets.response.responses import ALL_RESPONSES, \
    PushMessageResponse


class HandlerBase(metaclass=abc.ABCMeta):

    logger = logging.getLogger(__name__)

    def get_packet_type_by_code(self, code: int) -> Type[PacketBase]:
        """Tries to find te packet associated with the code in the header.
        If fails, raises a PacketBaseValueError."""
        for packet in ALL_REQUESTS + ALL_RESPONSES:
            if code == packet.CODE:
                return packet
        raise PacketBaseValueError(packet, f"Unexpected code {code}!")

    def get_packet_type_by_message_type(
            self, message_type: int,
    ) -> Type[Union[PushMessageRequest, PushMessageResponse]]:
        """Tries to find te packet associated with the message type from the
          message payload.
        If fails, raises a PacketBaseValueError."""
        from protocol.fields.message import MessageType

        for packet in ALL_REQUEST_MESSAGES + (PushMessageResponse, ):
            if message_type == packet.CODE:
                return packet

        # TODO: MessageValueError?
        raise FieldBaseValueError(
            MessageType(), f"Unexpected message type {message_type}!")

    def _expect_packet(
            self, socket, packet: Union[Request, Response],
    ) -> Tuple[PacketBase, FieldsValues]:
        self.logger.info(f"Expecting packet: {packet}.")
        header = socket.recv(packet.HEADER_LENGTH)
        unpacker = Unpacker(packet)
        try:
            header_fields = unpacker.unpack_header(header)
        except FieldBaseValueError as e:
            raise RuntimeError(f"Server responded with general error: {e!r}")

        code = header_fields['code']
        packet_concrete_type = self.get_packet_type_by_code(code)()
        print(f"concrete: {packet_concrete_type}")
        payload_size = header_fields['payload_size']
        socket.settimeout(2)

        received_payload = socket.recv(payload_size)
        self.logger.info(f"received ({len(received_payload)}: {received_payload}")
        payload_iter = iter(received_payload)
        unpacker.packet = packet_concrete_type
        payload_fields = unpacker.unpack_payload(payload_iter)
        header_fields.update(payload_fields)
        payload = bytes(payload_iter)
        assert payload == b'', f"Did not read all the payload ({len(payload)})"

        return packet_concrete_type, header_fields
