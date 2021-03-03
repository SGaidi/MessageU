import abc
from typing import Type, Tuple, Union

from common.utils import FieldsValues
from common.exceptions import FieldBaseValueError
from common.unpacker import Unpacker
from protocol.packets.base import PacketBase
from protocol.packets.request import Request, PushMessageRequest
from protocol.packets.response import Response


class HandlerBase(metaclass=abc.ABCMeta):

    def get_concrete_packet_type(self, code: int) -> Type[PacketBase]:
        for packet in Request.ALL_REQUESTS + Response.ALL_RESPONSES:
            if code == packet.CODE:
                return packet
        raise ValueError(f"Unexpected code {code}!")

    def _expect_packet(
            self, socket, packet: Union[Request, Response],
    ) -> Tuple[Type[PacketBase], FieldsValues]:
        header = socket.recv(packet.HEADER_LENGTH)
        unpacker = Unpacker(packet)
        try:
            header_fields = unpacker.unpack_header(header)
        except FieldBaseValueError:
            raise RuntimeError("Server responded with general error!")

        code = header_fields['code']
        packet_concrete_type = self.get_concrete_packet_type(code)()
        print(f"concrete: {packet_concrete_type}")
        payload_size = header_fields['payload_size']
        print(f"payload_size: {payload_size}")
        socket.settimeout(2)

        received_payload = socket.recv(payload_size)
        payload_iter = iter(received_payload)
        print(f"received: {received_payload}")
        unpacker.packet = packet_concrete_type
        payload_fields = unpacker.unpack_payload(payload_iter)
        print(f"received payload: {payload_fields}")
        header_fields.update(payload_fields)

        if isinstance(packet_concrete_type, PushMessageRequest):
            content_size = payload_fields['content_size']
            message_fields = unpacker.unpack_message(payload_iter, content_size)
            print(f"message fields: {message_fields}")
            header_fields.update(message_fields)

        return packet_concrete_type, header_fields
