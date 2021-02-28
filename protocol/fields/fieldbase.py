import abc
from itertools import islice, cycle
from typing import Type, Iterator, Tuple, Sequence, Any


class FieldBase(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def TYPE(self) -> Type: pass

    def __init__(self, name: str, length: int):
        self.name = name
        self.length = length

    def _validate_type(self, field: TYPE) -> None:
        if isinstance(field, property):
            return  # assumes properties are valid
        if not isinstance(field, self.TYPE):
            raise ValueError(f"Invalid type {type(field)!r}, "
                             f"expected {self.TYPE!r}.")

    def _validate_length(self, field: Sequence) -> None:
        if len(field) > self.length:
            raise ValueError(
                f"{field!r} exceeds the {self.length!r} "
                f"bytes length of field.")

    def _validate_encoding(self, field: bytes) -> None: pass

    def _validate_field_to_pack(self, field: TYPE) -> None:
        self._validate_type(field)
        self._validate_length(field)
        self._validate_encoding(field)

    @abc.abstractmethod
    def pack(self, field: TYPE) -> bytes: pass

    def _slice_bytes_iter(self, bytes_iter: Iterator[bytes]) -> bytes:
        """assumes the length is valid (enough for islice)"""
        return bytes(islice(bytes_iter, self.length))

    @abc.abstractmethod
    def unpack(self, bytes_iter: Iterator[bytes]) -> TYPE: pass
    # assumes the bytes are validated by all above validators


class IntField(FieldBase, metaclass=abc.ABCMeta):

    TYPE = int
    BITS_IN_BYTE = 8

    def _validate_length(self, field: int) -> None:
        bits_count = self.length * self.BITS_IN_BYTE
        max_value = 2 ** bits_count - 1
        if field > max_value:
            raise ValueError(
                f"{field!r} exceeds the {self.length!r} "
                f"bytes length of field.")

    def pack(self, field: int) -> bytes:
        self._validate_field_to_pack(field)
        return field.to_bytes(
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


class StaticIntField(IntField, metaclass=abc.ABCMeta):

    def __init__(self, name: str, value: int, length: int):
        super(StaticIntField, self).__init__(name=name, length=length)
        self.value = value

    def pack(self) -> bytes:
        return super(StaticIntField, self).pack(self.value)

    def unpack(self, bytes_iter: Iterator[bytes]) -> int:
        field_value = super(StaticIntField, self).unpack()
        if field_value != self.value:
            raise ValueError(f"Invalid field value {field_value!r}, "
                             f"expected {self.value!r}.")
        return field_value


class StringField(FieldBase, metaclass=abc.ABCMeta):

    TYPE = str

    def pack(self, field: str) -> bytes:
        self._validate_field_to_pack(field)
        return field.encode().zfill(self.length)

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        field_bytes = self._slice_bytes_iter(bytes_iter)
        return field_bytes.decode().lstrip('0')


class UnboundedStringField(StringField, metaclass=abc.ABCMeta):
    
    def __init__(self, name: str):
        super(UnboundedStringField, self).__init__(
            name=name, length=float('inf'))

    def pack(self, field: str) -> bytes:
        self._validate_field_to_pack(field)
        return field.encode()

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        return bytes(bytes_iter).decode()


class BytesField(FieldBase, metaclass=abc.ABCMeta):

    TYPE = bytes

    def pack(self, field: bytes) -> bytes:
        self._validate_field_to_pack(field)
        return field

    def unpack(self, bytes_iter: Iterator[bytes]) -> bytes:
        return bytes(self._slice_bytes_iter(bytes_iter))


class PublicKeyField(BytesField):

    def _validate_encoding(self, field: bytes) -> None:
        import base64
        try:
            return base64.b64encode(base64.b64decode(field)) == field
        except Exception as e:
            raise ValueError(f"Invalid encoding: {e!r}")

    def unpack(self, bytes_iter: Iterator[bytes]) -> bytes:
        return bytes(self._slice_bytes_iter(bytes_iter))


class UnboundedBytesField(BytesField, metaclass=abc.ABCMeta):

    def __init__(self, name: str):
        super(UnboundedBytesField, self).__init__(
            name=name, length=float('inf'))

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        return bytes(bytes_iter)


class CompoundField(FieldBase, metaclass=abc.ABCMeta):

    @property
    def TYPE(self) -> Type: Tuple

    def __init__(
            self, fields: Tuple[FieldBase, ...], name: str,
    ):
        compound_length = sum(field.length for field in fields)
        super(CompoundField, self).__init__(name=name, length=compound_length)
        self.fields = fields

    def _validate_type(self, fields_values: Tuple[Any]) -> None:
        super(CompoundField, self)._validate_type(fields_values)
        fields_values_iter = iter(fields_values)
        for field in cycle(self.fields):
            field_value = next(fields_values_iter)
            field._validate_type(field_value)

    def _validate_length(self, fields_values: Tuple[Any]) -> None:
        # TODO: make method _get_length(field_value)
        # TODO: also use field_value and field_bytes OR unpacked_field and
        #  packed_field
        # super(CompoundField, self)._validate_length(fields_values)
        pass
        # TODO: validate field count, and each field length and total length (overkill?)

    def _validate_encoding(self, field: bytes) -> None:
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
