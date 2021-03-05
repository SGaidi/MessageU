import logging
from typing import Tuple

from common.utils import FieldsValues
from protocol.packets.base import PacketBase
from protocol.fields.base import FieldBase


class Packer:

    logger = logging.getLogger(__name__)

    def __init__(self, packet: PacketBase):
        self.packet = packet

    def _update_field_to_size_field(
            self, field_name: str, field_length: int,
            fields_to_pack: FieldsValues,
    ) -> None:
        for field_to_pack in fields_to_pack:
            if field_to_pack.name == field_name + '_size':
                self.logger.info(f"Update {field_to_pack} with {field_length}")
                field_to_pack.value = field_length

    def _pack_fields(
            self, fields: Tuple[FieldBase], kwargs: FieldsValues,
    ) -> bytes:
        fields_bytes = []
        for field in reversed(fields):
            name = field.name
            field_value = kwargs.pop(name, field.value)
            self.logger.info(f"Packing {field} with {field_value}")
            field_bytes = field.pack(field_value)
            self._update_field_to_size_field(name, len(field_bytes), fields)
            fields_bytes.append(field_bytes)
        return b''.join(reversed(fields_bytes))

    def _pack_payload(self, kwargs: FieldsValues) -> bytes:
        payload_bytes = self._pack_fields(self.packet.payload_fields, kwargs)
        kwargs['payload_size'] = len(payload_bytes)
        return payload_bytes

    def _pack_header(self, kwargs: FieldsValues) -> bytes:
        return self._pack_fields(self.packet.header_fields, kwargs)

    def pack(self, **kwargs: FieldsValues) -> bytes:
        payload_bytes = self._pack_payload(kwargs)
        header_bytes = self._pack_header(kwargs)
        return header_bytes + payload_bytes
