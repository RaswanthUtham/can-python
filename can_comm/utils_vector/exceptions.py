"""
    created on oct 2020

    :file: exceptions.py
    :platform: Windows
    :synopsis:
        Implementation of vector exceptions.
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""


class VectorError(IOError):
    """
    Vector Exception Class
    """
    def __init__(self, error_code, error_string, function):
        self.error_code = error_code
        super().__init__(f"{function} failed ({error_string})")

        # keep reference to args for pickling
        self._args = error_code, error_string, function

    def __reduce__(self):
        return VectorError, self._args, {}
