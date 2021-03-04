import logging
from typing import Tuple

from common.utils import FieldsValues
from common.exceptions import PackerValueError
from protocol.packets.base import PacketBase
from protocol.fields.base import FieldBase


class Packer:

    def __init__(self, packet: PacketBase):
        self.packet = packet

    def _pack_fields(
            self, fields: Tuple[FieldBase], kwargs: FieldsValues,
    ) -> bytes:
        fields_bytes = []
        for field in fields:
            name = field.name
            field_value = kwargs.pop(name, field.value)
            if field_value is None:
                raise PackerValueError(
                    kwargs, f"Missing field {name!s}.")
            if name.endswith('_size') and field_value == float('inf'):
                field_value = \
                    sum(len(field_bytes) for field_bytes in fields_bytes)
            logging.debug(f"Packing {field} with {field_value}")
            field_bytes = field.pack(field_value)
            fields_bytes.append(field_bytes)
        return b''.join(fields_bytes)

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
