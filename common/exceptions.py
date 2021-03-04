from django.core.exceptions import ValidationError


class ClientAppException(ValueError):
    """Raised when ClientApp raised an exception."""
    pass





class ServerAppEnvironmentError(RuntimeError):
    """Raised when ServerApp resources (files, ports) are unavailable or not
    functioning."""
    pass


class ClientValidationError(ValidationError):
    """Raised when Client failed validation upon save."""
    pass


class MessageValidationError(ValidationError):
    """Raised when Message failed validation upon save."""
    pass


class ClientAppInvalidRequestError(ValueError):
    """Raised when ClientApp receives invalid request from user."""
    pass


class PacketBaseValueError(ValueError):
    """Raised when validation of packet base fails."""

    def __init__(self, packet, message: str):
        super(PacketBaseValueError, self).__init__(f"{packet!s:}: {message}")


class PackerValueError(ValueError):
    """Raised when packing of a packet fails."""

    def __init__(self, kwargs, message: str):
        super(PackerValueError, self).__init__(f"{kwargs!s:}: {message}")


class UnpackerValueError(ValueError):
    """Raised when unpacking of a packet fails."""

    def __init__(self, packet, message: str):
        super(UnpackerValueError, self).__init__(f"{packet!s:}: {message}")


class FieldBaseValueError(ValueError):
    """Raised when validation of field base fails."""

    def __init__(self, field, message: str):
        super(FieldBaseValueError, self).__init__(f"{field!s:}: {message}")


class ConnectionException(Exception):
    """Raised when an exception with connection occurred."""
    pass
