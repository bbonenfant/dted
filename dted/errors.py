""" Custom errors of the DTED package. """


class InvalidFileError(Exception):
    """Custom exception for an invalid DTED file."""


class NoElevationDataError(Exception):
    """Custom exception for when a DTED file does not contain elevation data for
    the specified location.
    """


class VoidDataWarning(UserWarning):
    """Warning that void data has been detected within the DTED file."""
