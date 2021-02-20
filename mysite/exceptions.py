

class ServerAppEnvironmentError(RuntimeError):
    """Raised when serverapp resources (files, ports) are unavailable or not
    functioning."""
    pass


class ServerAppConfigurationError(ValueError):
    """Raised when configuration file contents are invalid."""
    pass
