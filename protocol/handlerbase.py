import abc
from typing import Type, Tuple, Dict, Any, Union

from protocol.packetbase import PacketBase
from protocol.request import Request
from protocol.response import Response


class HandlerBase(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def _recv(self, buffer_size: int) -> bytes: pass

    def _expect_packet(
            self, packet_type: Type[Union[Request, Response]],
    ) -> Tuple[Type[PacketBase], Dict[str, Any], Dict[str, Any]]:

        # print
        # "From:", self.client_address
        buffer = []

        while True:
            data = self._recv(1024)
            if not data: break
            buffer.append(data)
        self.request.close()

        data = b''.join(buffer)
        header_fields = packet_type.unpack_header(data)
        code = header_fields['Code']
        packet_concrete_type = packet_type.get_concrete_packet_type(code)
        header_offset = packet_concrete_type.HEADER_LENGTH
        payload = data[header_offset:]
        payload_fields = packet_concrete_type.unpack_payload(payload)

        return packet_concrete_type, header_fields, payload_fields

        # TODO: here handle buffered data

