class ConfigError(Exception):
    """Raised when there's a configuration error."""
    pass


class RealFieldDoesNotExistError(Exception):
    """Raised when the real field cannot be found."""
    pass
