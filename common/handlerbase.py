import abc
from typing import Type, Tuple, Dict, Any, Optional

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
            self, socket,
    ) -> Tuple[Type[PacketBase], Dict[str, Any], Dict[str, Any]]:

        partial_header_length = PacketBase.BASE_HEADER_LENGTH
        print(partial_header_length)
        partial_header = socket.recv(partial_header_length)
        partial_header_fields = PacketBase.unpack_base_header(partial_header)

        code = partial_header_fields['code']
        packet_concrete_type = self.get_concrete_packet_type(code)()
        header_length = packet_concrete_type.HEADER_LENGTH
        remaining_header_length = header_length - partial_header_length
        header = partial_header + socket.recv(remaining_header_length)
        header_fields = packet_concrete_type.unpack_header(header)

        payload_size = header_fields['payload_size']
        received_payload = socket.recv(payload_size)
        print(f'size: {payload_size}')
        print(f'receive: {len(received_payload)}')
        payload_fields = \
            packet_concrete_type.unpack_payload(header_fields, received_payload)

        return packet_concrete_type, header_fields, payload_fields

        # TODO: here handle buffered data
