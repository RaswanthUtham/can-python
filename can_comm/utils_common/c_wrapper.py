"""
    created on oct 2020

    :file: c_wrapper.py
    :platform: Linux, Windows
    :synopsis:
        contains 'C' language function wrapper
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""


def c_wrap(lib, func_name, restype, argtypes, errcheck=None):
    """

    :param lib: 'C' shared library (.so, .dll, ...)
    :param func_name: 'C' function name
    :param restype: 'C' function return type
    :param argtypes: 'C' function argument types
    :param errcheck: error call back
    :return: object to call the 'C' function
    """
    func = lib.__getattr__(func_name)
    func.restype = restype
    func.argtypes = argtypes
    if errcheck is not None:
        func.errcheck = errcheck
    return func
