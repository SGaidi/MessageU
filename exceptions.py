

class ServerEnvironmentError(RuntimeError):
    """Raised when server resources (files, ports) are unavailable or not
    functioning."""
    pass


class ServerConfigurationError(ValueError):
    """Raised when configuration file contents are invalid."""
    pass
