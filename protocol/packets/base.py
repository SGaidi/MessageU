import abc
from collections import OrderedDict
from typing import Tuple, Any, NewType, Iterable

from common.utils import abstractproperty, classproperty
from common.exceptions import PacketBaseValueError
from protocol.fields.base import Base
from protocol.fields.header import Version, RequestCode, StaticVersion, StaticCode


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
        fields_str = ', '.join(str(f) for f in fields)
        print(f'length of {fields_str}')
        print(sum(field.length for field in fields))
        return sum(field.length for field in fields)

    BASE_HEADER_FIELDS = (Version(), RequestCode(),)

    @classproperty
    def BASE_HEADER_LENGTH(cls) -> int:
        return cls._length_of_fields(cls.BASE_HEADER_FIELDS)
    @property
    def HEADER_LENGTH(self) -> int:
        return self._length_of_fields(self.header_fields)

    def __init__(self):
        self.header_fields = (
            StaticVersion(self.VERSION),
            StaticCode(self.CODE),
        )

    def __str__(self):
        """Returns string with basic attributes."""
        headers_str = ', '.join(str(f) for f in self.header_fields)
        payload_str = ', '.join(str(f) for f in self.payload_fields)
        return f"{self.__class__.__name__}" \
               f"(code={self.CODE}, " \
               f"header=({headers_str}), " \
               f"payload=({payload_str}))"

    def pack(self, **kwargs: OrderedDict[str, Any]) -> bytes:
        fields_bytes = []
        all_fields = self.header_fields + self.payload_fields
        print(all_fields)
        for field in all_fields:
            name = field.name
            print(f"{name}:{field}")
            try:
                field_value = kwargs.pop(name)
            except KeyError:
                # raise PacketBaseValueError(f"Missing field {name}.")
                print(f'using default={field.value}')
                field_bytes = field.pack()
            else:
                print(f'value={field_value}')
                field_bytes = field.pack(field_value)
            fields_bytes.append(field_bytes)
        return b''.join(fields_bytes)

    def _validate_header_length(self, packet: bytes) -> None:
        if len(packet) < self.HEADER_LENGTH:
            raise PacketBaseValueError(
                self,
                f"Packet length {len(packet)} is higher then expected "
                f"header length {self.HEADER_LENGTH}.")

    @classmethod
    def _unpack_fields(
            cls, packet_iter: Iterable[bytes],
            expected_fields: OrderedDict[str, Base],
    ) -> OrderedDict[str, Base]:
        fields = OrderedDict()
        for field in expected_fields:
            field_value = field.unpack(packet_iter)
            fields[field.name] = field_value
        return fields

    @classmethod
    def unpack_base_header(cls, packet: bytes) -> OrderedDict[str, Any]:
        packet_iter = iter(packet)
        return cls._unpack_fields(packet_iter, cls.BASE_HEADER_FIELDS)

    def _validate_payload_length(
            self, payload: bytes, expected_payload_length: int,
    ) -> None:
        if len(payload) != expected_payload_length:
            raise PacketBaseValueError(
                self,
                f"Payload length is {len(payload)}, "
                f"expected {expected_payload_length}.")

    def unpack_header(self, packet: bytes) -> OrderedDict[str, Any]:
        self._validate_header_length(packet)
        packet_iter = iter(packet)
        return self._unpack_fields(packet_iter, self.header_fields)

    def unpack_payload(
            self, header_fields: OrderedDict, payload: bytes,
    ) -> OrderedDict[str, Any]:
        if self.__class__.__name__ == 'PacketBase':
            raise NotImplementedError(f'Should be called from child class.')
        expected_payload_length = header_fields['payload_size']
        self._validate_payload_length(payload, expected_payload_length)
        packet_iter = iter(payload)
        payload_fields = self._unpack_fields(packet_iter, self.payload_fields)
        return payload_fields
