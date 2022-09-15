""" Defines Exception subclasses for errors raised by the workforce-python-api.
"""


class WorkforceError(Exception):
    """
    Abstract base class for exceptions thrown by the workforce-python-api
    """

    def __init__(self, message):
        """
        :param message: A human readable message describing the error.
        """

        super().__init__(self)
        self.message = message

    def __str__(self):
        return self.message


class WorkforceWarning(Warning):
    """
    Abstract base class for warnings thrown by the workforce module
    """

    def __init__(self, message):
        """
        :param message: A human readable message describing the error.
        """

        super().__init__(self)
        self.message = message

    def __str__(self):
        return self.message


class ServerError(WorkforceError):
    """
    An error that was generated by a service in the backend, such as a portal or feature service.
    """

    def __init__(self, errors):
        """:param errors: An array of error objects returned by the server."""
        err_lines = ["\n\t{}".format(error["description"]) for error in errors]
        message = "Server operation failed with errors:{}".format(err_lines)
        super().__init__(message)
        self.errors = errors

    def __repr__(self):
        return "ServerError({})".format(repr(self.errors))


class ValidationError(WorkforceError):
    """
    Indicates that an operation failed because a model object failed validation checks.
    """

    def __init__(self, message, subject):
        """:param message: A human-readable description of the validation failure.
        :param subject: The model that failed validation.
        """
        super().__init__(message)
        self.subject = subject

    def __repr__(self):
        return "ValidationError({}, {})".format(self.message, repr(self.subject))
