import abc
from itertools import islice, cycle
from typing import Type, Iterator, Tuple, Sequence, Any

from common.utils import abstractproperty


class Base(metaclass=abc.ABCMeta):

    @abstractproperty
    def TYPE(self) -> Type: pass

    def __init__(self, name: str, length: int):
        self.name = name
        self.length = length

    def __str__(self):
        return f'{self.name}({self.length})'

    def _validate_type(self, field_value: TYPE) -> None:
        if not isinstance(field_value, self.TYPE):
            raise ValueError(f"Invalid type {type(field_value)!r}, "
                             f"expected {self.TYPE!r}.")

    def _validate_length(self, field_value: TYPE) -> None: pass

    def _validate_encoding(self, field_value: bytes) -> None: pass

    def _validate_field_to_pack(self, field_value: TYPE) -> None:
        self._validate_type(field_value)
        self._validate_length(field_value)
        self._validate_encoding(field_value)

    @abc.abstractmethod
    def pack(self, field_value: TYPE) -> bytes: pass

    @abc.abstractmethod
    def unpack(self, bytes_iter: Iterator[bytes]) -> TYPE: pass
    # assumes the bytes are validated by all above validators


class SequenceMixin:

    @abstractproperty
    def TYPE(self) -> Sequence: pass

    def _validate_length(self, field_value: Sequence) -> None:
        if len(field_value) > self.length:
            raise ValueError(
                f"{field_value!r} exceeds the {self.length!r} "
                f"bytes length of field.")


class UnboundedMixin:

    def __init__(self, *args, **kwargs):
        super(UnboundedString, self).__init__(
            *args, **kwargs, length=float('inf'))


class BoundedMixin:

    def _slice_bytes_iter(self, bytes_iter: Iterator[bytes]) -> bytes:
        """assumes the length is valid (enough for islice)"""
        return bytes(islice(bytes_iter, self.length))


class Int(Base, BoundedMixin, metaclass=abc.ABCMeta):

    TYPE = int
    BITS_IN_BYTE = 8

    def _validate_length(self, field_value: int) -> None:
        bits_count = self.length * self.BITS_IN_BYTE
        max_value = 2 ** bits_count - 1
        if field_value > max_value:
            raise ValueError(
                f"{field_value!r} exceeds the {self.length!r} "
                f"bytes length of field.")

    def pack(self, field_value: int) -> bytes:
        self._validate_field_to_pack(field_value)
        return field_value.to_bytes(
            length=self.length,
            byteorder="little",
            signed=False,
        )

    def unpack(self, bytes_iter: Iterator[bytes]) -> int:
        field_bytes = self._slice_bytes_iter(bytes_iter)
        return int.from_bytes(
            bytes=field_bytes,
            byteorder="little",
            signed=False,
        )


class StaticInt(Int, metaclass=abc.ABCMeta):

    def __init__(self, name: str, value: int, length: int):
        super(StaticInt, self).__init__(name=name, length=length)
        self.value = value

    def pack(self) -> bytes:
        return super(StaticInt, self).pack(self.value)

    def unpack(self, bytes_iter: Iterator[bytes]) -> int:
        field_value = super(StaticInt, self).unpack(bytes_iter)
        if field_value != self.value:
            raise ValueError(f"Invalid field value {field_value!r}, "
                             f"expected {self.value!r}.")
        return field_value


class String(Base, SequenceMixin, BoundedMixin, metaclass=abc.ABCMeta):

    TYPE = str

    def pack(self, field: str) -> bytes:
        self._validate_field_to_pack(field)
        return field.encode().zfill(self.length)

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        field_bytes = self._slice_bytes_iter(bytes_iter)
        return field_bytes.decode().lstrip('0')


class UnboundedString(String, UnboundedMixin, metaclass=abc.ABCMeta):

    def pack(self, field: str) -> bytes:
        self._validate_field_to_pack(field)
        return field.encode()

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        return bytes(bytes_iter).decode()


class Bytes(Base, SequenceMixin, metaclass=abc.ABCMeta):

    TYPE = bytes

    def pack(self, field: bytes) -> bytes:
        self._validate_field_to_pack(field)
        return field


class BoundedBytes(Bytes, BoundedMixin, metaclass=abc.ABCMeta):

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        return self._slice_bytes_iter(bytes_iter)


class UnboundedBytes(Bytes, UnboundedMixin, metaclass=abc.ABCMeta):

    def __init__(self, name: str):
        super(UnboundedBytes, self).__init__(
            name=name, length=float('inf'))

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        return bytes(bytes_iter)


class Compound(Base, metaclass=abc.ABCMeta):

    @property
    def TYPE(self) -> Type: Tuple

    def __init__(
            self, fields: Tuple[Base, ...], name: str,
    ):
        compound_length = sum(field.length for field in fields)
        super(Compound, self).__init__(name=name, length=compound_length)
        self.fields = fields

    def _validate_type(self, fields_values: Tuple[Any]) -> None:
        super(Compound, self)._validate_type(fields_values)
        fields_values_iter = iter(fields_values)
        for field in cycle(self.fields):
            field_value = next(fields_values_iter)
            field._validate_type(field_value)

    def _validate_length(self, fields_values: Tuple[Any]) -> None:
        # TODO: make method _get_length(field_value)
        # TODO: also use field_value and field_bytes OR unpacked_field and
        #  packed_field
        # super(Compound, self)._validate_length(fields_values)
        pass
        # TODO: validate field count, and each field length and total length (overkill?)

    def _validate_encoding(self, field_value: bytes) -> None:
        # TODO: same, do this to each field separately
        pass

    def pack(self, fields_values: Tuple[Any]) -> bytes:
        fields_values_iter = iter(fields_values)
        compound_bytes = []
        for field in cycle(self.fields):
            field_value = next(fields_values_iter)
            field_bytes = field.pack(field_value)
            compound_bytes.append(field_bytes)
        return b''.join(compound_bytes)

    def unpack(self, bytes_iter: Iterator[bytes]) -> TYPE:
        fields_values = []
        for field in cycle(self.fields):
            field_value = field.unpack(bytes_iter)
            fields_values.append(field_value)
        return fields_values


class ClientID(Int):

    def __init__(self, name: str):
        super(ClientID, self).__init__(name=name, length=16)
