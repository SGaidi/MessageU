import abc
import logging
from itertools import cycle
from typing import Type, Iterator, Tuple, Sequence, Any, Optional

from common.utils import abstractproperty, islice
from common.exceptions import FieldBaseValueError


class FieldBase(metaclass=abc.ABCMeta):

    @abstractproperty
    def TYPE(self) -> Type: pass

    logger = logging.getLogger(__name__)

    def __init__(
            self, name: str, length: int, value: Optional[Any] = None,
    ):
        self.name = name
        self.length = length
        self.value = value

    def __str__(self):
        return f'{self.name}(value={self.value!s}, length={self.length})'

    def _validate_type(self, field_value: TYPE) -> None:
        if field_value != float('inf') and \
                not isinstance(field_value, self.TYPE):
            raise FieldBaseValueError(
                self, f"Invalid type {type(field_value)!r}, expected "
                      f"{self.TYPE!r}.")

    def _validate_value_expected_length(self, field_value: TYPE) -> None: pass

    def _validate_field_to_pack(self, field_value: TYPE) -> None:
        self._validate_type(field_value)
        self._validate_value_expected_length(field_value)

    @abc.abstractmethod
    def pack(self, field_value: TYPE) -> bytes: pass

    def _validate_static_value(self, field_value: TYPE) -> None:
        if self.value not in [None, float('inf')] \
                and field_value != self.value:
            raise FieldBaseValueError(
                self, f"Invalid field value {field_value!r}, expected "
                      f"{self.value!r}.")

    @abc.abstractmethod
    def unpack(self, bytes_iter: Iterator[bytes]) -> TYPE: pass


class SequenceMixin:

    @abstractproperty
    def TYPE(self) -> Sequence: pass

    def _validate_value_expected_length(self, field_value: Sequence) -> None:
        if field_value != float('inf') and len(field_value) > self.length:
            raise FieldBaseValueError(
                self, f"{field_value!r} exceeds the {self.length!r} "
                      f"bytes length of field.")


class BoundedMixin:

    length: int

    def _slice_bytes_iter(self, bytes_iter: Iterator[bytes]) -> bytes:
        FieldBase.logger.debug(f"_slice_bytes_iter of length {self.length}")
        if self.length == 0:
            assert bytes(bytes_iter) == b''
            return b''
        sliced_bytes = bytes(islice(bytes_iter, self.length))
        if sliced_bytes == b'':
            raise StopIteration
        return sliced_bytes


class Int(FieldBase, BoundedMixin, metaclass=abc.ABCMeta):

    TYPE = int
    BITS_IN_BYTE = 8

    def _validate_value_expected_length(self, field_value: int) -> None:
        bits_count = self.length * self.BITS_IN_BYTE
        max_value = 2 ** bits_count - 1
        if field_value != float('inf') and field_value > max_value:
            raise FieldBaseValueError(
                self, f"{field_value!r} exceeds the {self.length!r} "
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
        field_value = int.from_bytes(
            bytes=field_bytes,
            byteorder="little",
            signed=False,
        )
        self._validate_static_value(field_value)
        return field_value


class String(FieldBase, SequenceMixin, BoundedMixin, metaclass=abc.ABCMeta):

    TYPE = str

    def pack(self, field: str) -> bytes:
        self._validate_field_to_pack(field)
        return field.encode().zfill(self.length)

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        field_bytes = self._slice_bytes_iter(bytes_iter)
        field_value = field_bytes.decode().lstrip('0')
        self._validate_static_value(field_value)
        return field_value


class UnboundedString(String, metaclass=abc.ABCMeta):

    def pack(self, field: str) -> bytes:
        self._validate_field_to_pack(field)
        return field.encode()

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        return bytes(bytes_iter).decode()


class Bytes(FieldBase, SequenceMixin, metaclass=abc.ABCMeta):

    TYPE = bytes

    def pack(self, field: bytes) -> bytes:
        self._validate_field_to_pack(field)
        return field


class BoundedBytes(Bytes, BoundedMixin, metaclass=abc.ABCMeta):

    def unpack(self, bytes_iter: Iterator[bytes]) -> bytes:
        self.logger.debug(f"BoundedBytes.unpack")
        from itertools import tee
        bytes_iter, bytes_iter_copy = tee(bytes_iter)
        field_value = self._slice_bytes_iter(bytes_iter)
        self.logger.debug(field_value)
        self._validate_static_value(field_value)
        return field_value


class UnboundedBytes(Bytes, metaclass=abc.ABCMeta):

    def __init__(self, name: str):
        super(UnboundedBytes, self).__init__(
            name=name, length=float('inf'))

    def unpack(self, bytes_iter: Iterator[bytes]) -> bytes:
        return bytes(bytes_iter)


class Compound(FieldBase, metaclass=abc.ABCMeta):

    @property
    def TYPE(self) -> Type: Tuple

    def __init__(
            self, fields: Tuple[FieldBase, ...], name: str,
    ):
        super(Compound, self).__init__(name=name, length=float('inf'))
        self.fields = fields

    @property
    def compound_length(self) -> int:
        return sum(field.length for field in self.fields)

    def _validate_value_expected_length(self, field_value: Tuple[Any]) -> None:
        expected_length = len(self.fields)
        for nested_values in field_value:
            actual_length = len(nested_values)
            if actual_length != expected_length:
                raise FieldBaseValueError(
                    self, f"Invalid nested values length "
                          f"({actual_length}), expected {expected_length}."
                )

    def pack(self, fields_values: Tuple[Any]) -> bytes:
        fields_values_iter = iter(fields_values)
        # TODO: update
        compound_bytes = []
        print(f"compound fields to pack: {self.fields}")
        for field in cycle(self.fields):
            try:
                field_value = next(fields_values_iter)
            except StopIteration:
                break
            if field.name.endswith('_size'):
                assert field_value != float('inf')
                name_to_update = field.name.replace('_size', '')
                for _field in self.fields:
                    if _field.name == name_to_update:
                        _field.length = field_value
            field_bytes = field.pack(field_value)
            compound_bytes.append(field_bytes)
            print(f'{field}: {field_value}')
        return b''.join(compound_bytes)

    def unpack(self, bytes_iter: Iterator[bytes]) -> TYPE:
        print("COMPOUND UNPACK")
        fields_values = []
        for field in cycle(self.fields):
            print(f"field: {field}")
            try:
                field_value = field.unpack(bytes_iter)
            except StopIteration:
                break
            if field.name.endswith('_size'):
                print("SIZE")
                assert field_value != float('inf')
                name_to_update = field.name.replace('_size', '')
                print(f"update: {name_to_update} => {field_value}")
                for _field in self.fields:
                    if _field.name == name_to_update:
                        _field.length = field_value
            print(f"value: {field_value}")
            fields_values.append(field_value)
        return tuple(fields_values)


class ClientID(Int):

    LENGTH = 16

    def __init__(self, name: str, client_id: int = None):
        super(ClientID, self).__init__(
            name=name, value=client_id, length=self.LENGTH)
