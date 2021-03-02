import abc
from copy import deepcopy
from collections import OrderedDict
from typing import Tuple, Any, NewType, Iterable

from common.utils import abstractproperty, classproperty, Fields
from common.exceptions import PacketBaseValueError
from protocol.fields.base import Base


class PacketBase(metaclass=abc.ABCMeta):
    """Abstract packet base class in MessageU protocol.

    Class Attributes:
      PacketBase: class typing hack.
      CODE: Unique packet code. Each concrete packet implementation has a
        different code.
      X_FIELD: Shortcut for creating specific fields.
    Attributes:
      header_fields: TODO:
      payload_fields: TODO:
    """

    PacketBase = NewType('PacketBase', type)  # only for type notations

    @abstractproperty
    def CODE(self) -> int: pass

    payload_fields: Tuple[Base, ...]
    payload_size: int
    header_fields: Tuple[Base, ...]

    @classmethod
    def _length_of_fields(cls, fields: Tuple[Base, ...]) -> int:
        return sum(field.length for field in fields)

    @abstractproperty
    def HEADER_FIELDS_TEMPLATE(self) -> Tuple[Base]: pass

    @classproperty
    def HEADER_LENGTH(self) -> int:
        return self._length_of_fields(self.HEADER_FIELDS_TEMPLATE)

    def _update_header_value(self, field_name: str, field_value: Any) -> None:
        for header in self.header_fields:
            if header.name == field_name:
                header.value = field_value
                return
        raise PacketBaseValueError(self, f"Invalid field name {field_name!s}!")

    def __init__(self):
        self.header_fields = deepcopy(self.HEADER_FIELDS_TEMPLATE)
        if hasattr(self, 'payload_fields'):
            self.payload_size = self._length_of_fields(self.payload_fields)
            self._update_header_value('payload_size', self.payload_size)
        self._update_header_value('code', self.CODE)

    def __str__(self):
        """Returns string with basic attributes."""
        headers_str = ', '.join(str(f) for f in self.header_fields)
        payload_str = ', '.join(str(f) for f in self.payload_fields)
        return f"{self.__class__.__name__}" \
               f"(code={self.CODE}, " \
               f"header=({headers_str}), " \
               f"payload=({payload_str}))"

    def pack(self, **kwargs: Fields) -> bytes:
        all_fields = self.header_fields + self.payload_fields
        fields_bytes = []

        import logging
        logging.debug(self)

        for field in all_fields:
            name = field.name
            try:
                field_value = kwargs.pop(name)
            except KeyError:
                if field.value is None:
                    raise PacketBaseValueError(
                        self, f"Missing field {name!s}.")
                field_value = field.value
            logging.debug(f"Packing {field} with {field_value}")
            # if not isinstance(field_value, Tuple):
            #     field_values = [field_value]
            # for field_value in field_values:
            field_bytes = field.pack(field_value)
            fields_bytes.append(field_bytes)
        return b''.join(fields_bytes)

    def _validate_header_length(self, packet: bytes) -> None:
        if len(packet) < self.HEADER_LENGTH:
            raise PacketBaseValueError(
                self,
                f"Packet length {len(packet)} is lower then expected "
                f"header length {self.HEADER_LENGTH}.")

    @classmethod
    def _unpack_fields(
            cls, packet_iter: Iterable[bytes],
            expected_fields: OrderedDict[str, Base], bytes_length: int,
    ) -> OrderedDict[str, Base]:
        fields = OrderedDict()
        for field in expected_fields:
            field_value = field.unpack(packet_iter, bytes_length)
            fields[field.name] = field_value
        return fields

    def _validate_payload_length(
            self, payload: bytes, expected_payload_length: int,
    ) -> None:
        if len(payload) != expected_payload_length:
            raise PacketBaseValueError(
                self,
                f"Payload length is {len(payload)}, "
                f"expected {expected_payload_length}.")

    def unpack_header(self, packet: bytes) -> Fields:
        self._validate_header_length(packet)
        packet_iter = iter(packet)
        return self._unpack_fields(
            packet_iter, self.header_fields, len(packet))

    def unpack_payload(
            self, header_fields: Fields, payload: bytes,
    ) -> Fields:
        if self.__class__.__name__ == 'PacketBase':
            raise NotImplementedError(f'Should be called from child class.')
        expected_payload_length = header_fields['payload_size']

        self._validate_payload_length(payload, expected_payload_length)
        packet_iter = iter(payload)

        payload_fields = self._unpack_fields(
            packet_iter, self.payload_fields, len(payload))
        return payload_fields
