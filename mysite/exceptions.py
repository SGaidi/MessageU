from django.core.exceptions import ValidationError


class ServerAppEnvironmentError(RuntimeError):
    """Raised when ServerApp resources (files, ports) are unavailable or not
    functioning."""
    pass


class ServerAppConfigurationError(ValueError):
    """Raised when ServerApp configuration file contents are invalid."""
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
