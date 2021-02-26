import abc
import logging
from typing import Type, Tuple, Dict, Any

from protocol.packetbase import PacketBase


class HandlerBase(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def _recv(self, buffer_size: int) -> bytes: pass

    def _expect_packet(
            self, packet_type: Type[PacketBase],
    ) -> Tuple[Type[PacketBase], Dict[str, Any], Dict[str, Any]]:
        packet_header_bytes = \
            self._recv(packet_type.HEADER_LENGTH)
        header_fields = packet_type.unpack_packet_base(packet_header_bytes)

        packet_payload_bytes = self._recv(header_fields['payload_size'])
        concrete_packet_type = \
            packet_type.get_concrete_packet_type(header_fields['code'])
        payload_fields = \
            concrete_packet_type.unpack_packet_payload(packet_payload_bytes)

        return concrete_packet_type, header_fields, payload_fields
