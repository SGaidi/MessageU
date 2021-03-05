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
                self.logger.info(f"Update {field_to_pack} with {field_length}")
                field_to_pack.length = field_length

    def _unpack_fields(
            self, bytes_iter: Iterator[bytes],
            expected_fields: Tuple[FieldBase],
    ) -> OrderedDict[str, FieldBase]:
        from itertools import tee
        fields = OrderedDict()

        self.logger.info(f"expected fields: {expected_fields}")
        for field in expected_fields:
            self.logger.info(f"Unpacking {field}")
            bytes_iter_copy_before, bytes_iter = tee(bytes_iter)
            field_value = field.unpack(bytes_iter)
            self.logger.info(f"field.unpack result: {field_value}")
            fields[field.name] = field_value
            if field.name.endswith('_size'):
                # TODO: return the number of bytes unpacked
                #  need to refactor unpack
                bytes_iter_copy_after, bytes_iter = tee(bytes_iter)
                bytes_unpacked = len(bytes(bytes_iter_copy_before)) - \
                    len(bytes(bytes_iter_copy_after))
                self._update_size_field_to_field(
                    field.name, bytes_unpacked, expected_fields)
        return fields

    def unpack_header(self, header: bytes) -> FieldsValues:
        self._validate_header_length(header)
        header_iter = iter(header)
        return self._unpack_fields(header_iter, self.packet.header_fields)

    def unpack_payload(self, payload_iter: Iterator[bytes]) -> FieldsValues:
        payload_fields = \
            self._unpack_fields(payload_iter, self.packet.payload_fields)
        return payload_fields

    def unpack_message(
            self, message_iter: Iterator[bytes], message_size: int,
    ) -> FieldsValues:
        from protocol.fields.message import MessageContent

        self.logger.info(f"Trying to unpack message fo size {message_size}")
        message_fields = self._unpack_fields(
            message_iter,
            (MessageContent(length=message_size), ),
        )

        return message_fields

    def unpack_messages(self, message_iter: Iterator[bytes]) -> FieldsValues:
        from protocol.fields.message import Messages
        message_fields = \
            self._unpack_fields(message_iter, (Messages(), ))
        return message_fields
