import abc
from varname import nameof
from collections import OrderedDict
from typing import Tuple, Any, Type, NewType

from protocol.utils import classproperty, abstractproperty
from protocol.fields import FieldBase, IntField, StaticIntField, StringField, \
    UnboundedStringField, PublicKeyField, BytesField, UnboundedBytesField


class PacketBase(metaclass=abc.ABCMeta):
    """Abstract packet base class in MessageU protocol.

    Attributes:
      FIELDS_TO_TYPE_AND_LENGTH: Mapping from field name to it's corresponding
        Python type presentation, and the packet field length in bytes.
      VERSION: Unique version of server / client. Either 1 or 2.
      CODE: Unique packet code. Each full packet implementation has a
        different code.
    """

    PacketBase = NewType('PacketBase', type)  # only for type notations

    # TODO: make one generic PacketBaseValueError instead of too many

    @abstractproperty
    def VERSION(self) -> int: pass
    @abstractproperty
    def CODE(self) -> int: pass
    @property
    def MESSAGE_TYPE(self) -> int: pass

    CLIENT_ID_FIELD = IntField(length=16)
    VERSION_FIELD = StaticIntField(value=VERSION, length=1)
    @abstractproperty
    def CODE_FIELD(self) -> FieldBase: pass
    PAYLOAD_SIZE_FIELD = IntField(length=4)
    NAME_FIELD = StringField(length=255)
    PUBLIC_KEY_FIELD = PublicKeyField(length=160)
    MESSAGE_TYPE_FIELD = StaticIntField(value=MESSAGE_TYPE, length=1)
    CONTENT_SIZE_FIELD = IntField(length=4)
    MESSAGE_CONTENT_FIELD = UnboundedStringField()
    ENCRYPTED_SYMMETRIC_KEY_FIELD = BytesField(length=16)
    ENCRYPTED_MESSAGE_FIELD = UnboundedBytesField()
    ENCRYPTED_FILE_FIELD = UnboundedBytesField()

    FIELD_SUFFIX_LENGTH = len('_FIELD')

    @abstractproperty
    def HEADER_FIELDS(self) -> Tuple[FieldBase]: pass
    @classproperty
    def HEADER_LENGTH(self) -> int:
        return sum(field.length for field in self.HEADER_FIELDS)
    @classproperty
    def HEADER_FIELDS_KWARGS(self) -> OrderedDict[str, FieldBase]:
        return OrderedDict(
            (nameof(field)[:-self.FIELD_SUFFIX_LENGTH], field)
            for field in self.HEADER_FIELDS
        )

    @abstractproperty
    def PAYLOAD_FIELDS(self) -> Tuple[FieldBase]: pass
    @classproperty
    def PAYLOAD_FIELDS_KWARGS(self) -> OrderedDict[str, FieldBase]:
        return OrderedDict(
            (nameof(field)[:-self.FIELD_SUFFIX_LENGTH], field)
            for field in self.PAYLOAD_FIELDS
        )

    def __str__(self):
        """Returns string with basic attributes. Used for debug logging."""
        return f"{self.__class__.__name__}" \
               f"(code={self.CODE}, " \
               f"header={self.HEADER_FIELDS_KWARGS}, " \
               f"payload={self.PAYLOAD_FIELDS_KWARGS})"

    def pack(self, **kwargs: OrderedDict[str, Any]) -> bytes:
        fields_bytes = []
        all_fields = self.HEADER_FIELDS_KWARGS + self.PAYLOAD_FIELDS_KWARGS
        for name, field in all_fields.items():
            try:
                field_value = kwargs.pop(name)
            except KeyError:
                raise ValueError(f"Missing field {name}")
            field_bytes = field.pack(field_value)
            fields_bytes.append(field_bytes)
        return b''.join(fields_bytes)

    def _validate_header_length(self, packet: bytes) -> None:
        if len(packet) < self.HEADER_LENGTH:
            raise ValueError(f"Packet length {len(packet)} is higher then "
                             f"expected header length {self.HEADER_LENGTH}.")

    def _validate_payload_length(
            self, packet: bytes, expected_payload_length: int,
    ) -> None:
        expected_packet_length = self.HEADER_LENGTH + expected_payload_length
        if len(packet) != expected_packet_length:
            raise ValueError(f"Packet length is {len(packet)}, expected "
                             f"{expected_packet_length}.")

    def unpack(self, packet: bytes) -> OrderedDict[str, Any]:
        self._validate_header_length()
        fields = OrderedDict()
        packet_iter = iter(packet)
        for name, field in self.HEADER_FIELDS_KWARGS.items():
            field_value = field.unpack(packet_iter)
            fields[name] = field_value
        expected_payload_length = fields['payload_size']
        self._validate_payload_length(packet, expected_payload_length)
        for name, field in self.PAYLOAD_FIELDS_KWARGS.items():
            field_value = field.unpack(packet_iter)
            fields[name] = field_value
        return fields

    @classmethod
    def get_concrete_packet_type(cls, code: int) -> Type[PacketBase]:
        for packet in cls.ALL:
            if code == packet.CODE:
                return packet
        raise ValueError(f"Unexpected code {code}!")
