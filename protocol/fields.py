import abc
from itertools import islice
from typing import Type, Iterator


class FieldBase(metaclass=abc.ABCMeta):

    @property
    @abc.abstractmethod
    def TYPE(self) -> Type: pass

    def __init__(self, length: int):
        self.length = length

    def _validate_type(self, field: TYPE) -> None:
        if not isinstance(field, self.TYPE):
            raise ValueError(f"Invalid type {type(field)!r}, "
                             f"expected {self.TYPE!r}.")

    def _validate_length(self, field: str) -> None:
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


class IntField(FieldBase):

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


class StaticIntField(IntField):

    def __init__(self, value: int, length: int):
        super(StaticIntField, self).__init__(length=length)
        self.value = value

    def pack(self) -> bytes:
        return super(StaticIntField, self).pack(self.value)

    def unpack(self, bytes_iter: Iterator[bytes]) -> int:
        field_value = super(StaticIntField, self).unpack()
        if field_value != self.value:
            raise ValueError(f"Invalid field value {field_value!r}, "
                             f"expected {self.value!r}.")
        return field_value


class StringField(FieldBase):

    TYPE = str

    def pack(self, field: str) -> bytes:
        self._validate_field_to_pack(field)
        return field.encode().zfill(self.length)

    def unpack(self, bytes_iter: Iterator[bytes]) -> str:
        field_bytes = self._slice_bytes_iter(bytes_iter)
        return field_bytes.decode().lstrip('0')


class BytesField(FieldBase, metaclass=abc.ABCMeta):

    TYPE = bytes

    # def pack(self, field: bytes) -> bytes:
    #     self._validate_field_to_pack(field)
    #     return field
    #
    # def unpack(self, bytes_iter: Iterator[bytes]) -> bytes:
    #     return bytes(self._slice_bytes_iter(bytes_iter))


class PublicKeyField(BytesField):

    def _validate_encoding(self, field: bytes) -> None:
        import base64
        try:
            return base64.b64encode(base64.b64decode(field)) == field
        except Exception as e:
            raise ValueError(f"Invalid encoding: {e!r}")

    def pack(self, field: bytes) -> bytes:
        self._validate_field_to_pack(field)
        return field

    def unpack(self, bytes_iter: Iterator[bytes]) -> bytes:
        return bytes(self._slice_bytes_iter(bytes_iter))
