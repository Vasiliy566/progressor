class ProgressorError(Exception):
    """Base exception"""


class RecordNotFoundError(ProgressorError):
    """Exception raised when no record found"""



class IncorrectProgressValueError(ProgressorError):
    """Exception raised when progress value is incorrect"""
