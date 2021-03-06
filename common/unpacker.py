import logging
from typing import Iterator, Tuple
from collections import OrderedDict

from common.utils import FieldsValues
from common.exceptions import UnpackerValueError
from protocol.packets.base import PacketBase
from protocol.fields.base import FieldBase


class Unpacker:

    logger = logging.getLogger(__name__)

    def __init__(self, packet: PacketBase):
        self.packet = packet

    def _validate_header_length(self, packet_bytes: bytes) -> None:
        bytes_length = len(packet_bytes)
        if bytes_length < self.packet.HEADER_LENGTH:
            raise UnpackerValueError(
                self,
                f"Packet length {bytes_length} is lower then expected "
                f"header length {self.packet.HEADER_LENGTH}.")

    def _update_size_field_to_field(
            self, field_name: str, field_length: int,
            fields_to_pack: FieldsValues,
    ) -> None:
        for field_to_pack in fields_to_pack:
            if field_to_pack.name + '_size' == field_name:
                field_to_pack.length = field_length

    def _unpack_fields(
            self, bytes_iter: Iterator[bytes],
            expected_fields: Tuple[FieldBase],
    ) -> OrderedDict[str, FieldBase]:
        fields = OrderedDict()
        for field in expected_fields:
            field_value = field.unpack(bytes_iter)
            fields[field.name] = field_value
            if field.name.endswith('_size'):
                self._update_size_field_to_field(
                    field.name, field_value, expected_fields)
        return fields

    def unpack_header(self, header: bytes) -> FieldsValues:
        self._validate_header_length(header)
        header_iter = iter(header)
        return self._unpack_fields(header_iter, self.packet.header_fields)

    def unpack_payload(self, payload_iter: Iterator[bytes]) -> FieldsValues:
        payload_fields = \
            self._unpack_fields(payload_iter, self.packet.payload_fields)
        return payload_fields
