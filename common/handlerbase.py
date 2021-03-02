import abc
from typing import Type, Tuple, Union

from common.utils import Fields
from common.exceptions import FieldBaseValueError
from protocol.packets.base import PacketBase
from protocol.packets.request import Request
from protocol.packets.response import Response


class HandlerBase(metaclass=abc.ABCMeta):

    def get_concrete_packet_type(self, code: int) -> Type[PacketBase]:
        for packet in Request.ALL + Response.ALL:
            if code == packet.CODE:
                return packet
        raise ValueError(f"Unexpected code {code}!")

    def _expect_packet(
            self, socket, packet: Union[Request, Response],
    ) -> Tuple[Type[PacketBase], Fields, Fields]:
        header = socket.recv(packet.HEADER_LENGTH)
        try:
            header_fields = packet.unpack_header(header)
        except FieldBaseValueError:
            raise RuntimeError("Server responded with general error!")

        code = header_fields['code']
        packet_concrete_type = self.get_concrete_packet_type(code)()
        payload_size = header_fields['payload_size']
        socket.settimeout(2)

        received_payload = socket.recv(payload_size)
        payload_fields = \
            packet_concrete_type.unpack_payload(header_fields, received_payload)

        return packet_concrete_type, header_fields, payload_fields
