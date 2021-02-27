import abc
import logging
from varname import nameof
from collections import OrderedDict
from typing import Tuple, Any, Type, NewType, Iterable

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

    # TODO: remove the assignments and move it directly to HEADER/PAYLOAD FIELDS
    #  this so names like VERSION would be loaded in child classes.
    SENDER_CLIENT_ID_FIELD = IntField(name='sender_client_id', length=16)
    RECEIVER_CLIENT_ID_FIELD = IntField(name='receiver_client_id', length=16)
    VERSION_FIELD = StaticIntField(name='version', value=VERSION, length=1)
    @abstractproperty
    def CODE_FIELD(self) -> FieldBase: pass
    PAYLOAD_SIZE_FIELD = IntField(name='payload_size', length=4)
    NAME_FIELD = StringField(name='client_name', length=255)
    PUBLIC_KEY_FIELD = PublicKeyField(name='public_key', length=160)
    MESSAGE_TYPE_FIELD = StaticIntField(
        name='message_type', value=MESSAGE_TYPE, length=1)
    CONTENT_SIZE_FIELD = IntField(name='content_size', length=4)
    MESSAGE_CONTENT_FIELD = UnboundedStringField(name='message_content')
    ENCRYPTED_SYMMETRIC_KEY_FIELD = BytesField(
        name='ecrypted_symmetric_key', length=16)
    ENCRYPTED_MESSAGE_FIELD = UnboundedBytesField(name='encrypted_message')
    ENCRYPTED_FILE_FIELD = UnboundedBytesField(name='encrypted_file')
    MESSAGE_ID_FIELD = IntField(name='message_id', length=5)

    FIELD_SUFFIX_LENGTH = len('FIELD')

    @abstractproperty
    def HEADER_FIELDS(self) -> Tuple[FieldBase]: pass
    @classproperty
    def HEADER_LENGTH(self) -> int:
        return sum(field.length for field in self.HEADER_FIELDS)

    @abstractproperty
    def PAYLOAD_FIELDS(self) -> Tuple[FieldBase]: pass

    def __str__(self):
        """Returns string with basic attributes. Used for debug logging."""
        return f"{self.__class__.__name__}" \
               f"(code={self.CODE}, " \
               f"header={self.HEADER_FIELDS}, " \
               f"payload={self.PAYLOAD_FIELDS})"

    def pack(self, **kwargs: OrderedDict[str, Any]) -> bytes:
        fields_bytes = []
        all_fields = self.HEADER_FIELDS + self.PAYLOAD_FIELDS
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
            fields: OrderedDict[str, FieldBase],
            expected_fields: OrderedDict[str, FieldBase],
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
        self._unpack_fields(packet_iter, fields, self.HEADER_FIELDS)
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
        self._unpack_fields(packet_iter, fields, self.PAYLOAD_FIELDS)
        return fields
