from django.core.exceptions import ValidationError


class ServerAppEnvironmentError(RuntimeError):
    """Raised when ServerApp resources (files, ports) are unavailable or not
    functioning."""
    pass


class ServerAppConfigurationError(ValueError):
    """Raised when ServerApp configuration file contents are invalid."""
    pass


class ClientAppEnvironmentException(ValueError):
    """Raised when ClientApp configuration file contents are invalid."""
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
    """Raised when validation of packet base failes."""

    def __init__(self, packet, message: str):
        super(PacketBaseValueError, self).__init__(f"{packet!s:}: {message}")


class ConnectionException(Exception):
    """Raised when an exception with connection occurred."""
    pass
