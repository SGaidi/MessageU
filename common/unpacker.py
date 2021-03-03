import logging
from typing import Iterable, Tuple
from collections import OrderedDict

from common.utils import FieldsValues
from common.exceptions import UnpackerValueError
from protocol.packets.base import PacketBase
from protocol.fields.base import FieldBase


class Unpacker:

    def __init__(self, packet: PacketBase):
        self.packet = packet

    def _validate_header_length(self, packet_bytes: bytes) -> None:
        bytes_length = len(packet_bytes)
        if bytes_length < self.packet.HEADER_LENGTH:
            raise UnpackerValueError(
                self,
                f"Packet length {bytes_length} is lower then expected "
                f"header length {self.packet.HEADER_LENGTH}.")

    def _unpack_fields(
            self, bytes_iter: Iterable[bytes],
            expected_fields: Tuple[FieldBase],
    ) -> OrderedDict[str, FieldBase]:
        fields = OrderedDict()
        expected_sizes = {}
        for field in expected_fields:
            logging.debug(f"Unpacking {field}")
            field_value = field.unpack(bytes_iter)
            logging.debug(f"field.unpack result: {field_value}")
            if field_value == float('inf'):
                field_value = expected_sizes[field.name]
            fields[field.name] = field_value
            print(f"value: {field_value}")
            if field.name.endswith('_size'):
                expected_sizes[field.name] = field_value
        return fields

    def unpack_header(self, header: bytes) -> FieldsValues:
        self._validate_header_length(header)
        header_iter = iter(header)
        return self._unpack_fields(header_iter, self.packet.header_fields)

    def unpack_payload(self, payload_iter: bytes,) -> FieldsValues:
        payload_fields = \
            self._unpack_fields(payload_iter, self.packet.payload_fields)
        return payload_fields

    def unpack_message(self, message_iter: bytes, message_size: int) -> FieldsValues:
        from protocol.fields.message import MessageContent
        message_fields = \
            self._unpack_fields(message_iter,
                                (MessageContent(length=message_size), ))
        return message_fields
