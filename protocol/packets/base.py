import abc
from collections import OrderedDict
from typing import Tuple, Any, Type, NewType, Iterable

from protocol.utils import abstractproperty
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

    # TODO: make one generic PacketBaseValueError instead of too many

    @abstractproperty
    def CODE(self) -> int: pass

    payload_fields: Tuple[Base, ...]
    payload_size: int
    header_fields: Tuple[Base, ...]

    def length_of_fields(self, fields: Tuple[Base, ...]) -> int:
        return sum(field.length for field in fields)

    def __str__(self):
        """Returns string with basic attributes."""
        return f"{self.__class__.__name__}" \
               f"(code={self.CODE}, " \
               f"header={self.header_fields}, " \
               f"payload={self.payload_fields})"

    def pack(self, **kwargs: OrderedDict[str, Any]) -> bytes:
        fields_bytes = []
        all_fields = self.header_fields + self.payload_fields
        for field in all_fields:
            name = field.name
            print(f"{name}:{field}")
            try:
                field_value = kwargs.pop(name)
            except KeyError:
                # raise ValueError(f"Missing field {name}.")
                fields_bytes = field.pack()
            else:
                field_bytes = field.pack(field_value)
            fields_bytes.append(field_bytes)
        return b''.join(fields_bytes)

    def _validate_header_length(self, packet: bytes) -> None:
        if len(packet) < self.HEADER_LENGTH:
            raise ValueError(f"Packet length {len(packet)} is higher then "
                             f"expected header length {self.HEADER_LENGTH}.")

    def _unpack_fields(
            self, packet_iter: Iterable[bytes],
            fields: OrderedDict[str, Base],
            expected_fields: OrderedDict[str, Base],
    ) -> None:
        for field in expected_fields:
            field_value = field.unpack(packet_iter)
            fields[field.name] = field_value

    def _validate_payload_length(
            self, packet: bytes, expected_payload_length: int,
    ) -> None:
        expected_packet_length = self.HEADER_LENGTH + expected_payload_length
        if len(packet) != expected_packet_length:
            raise ValueError(f"Packet length is {len(packet)}, expected "
                             f"{expected_packet_length}.")

    def unpack_header(self, packet: bytes) -> OrderedDict[str, Any]:
        self._validate_header_length()
        fields = OrderedDict()
        packet_iter = iter(packet)
        self._unpack_fields(packet_iter, fields, self.header_fields)
        expected_payload_length = fields['payload_size']
        self._validate_payload_length(packet, expected_payload_length)
        return fields

    @classmethod
    def get_concrete_packet_type(cls, code: int) -> Type[PacketBase]:
        for packet in cls.ALL:
            if code == packet.CODE:
                return packet
        raise ValueError(f"Unexpected code {code}!")

    def unpack_payload(self, packet: bytes) -> OrderedDict[str, Any]:
        if self.__class__.__name__ == 'PacketBase':
            raise NotImplementedError(f'Should be called from child class.')
        fields = OrderedDict()
        packet_iter = iter(packet)
        self._unpack_fields(packet_iter, fields, self.payload_fields)
        return fields
