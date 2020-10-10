def c_wrap(lib, func_name, restype, argtypes, errcheck=None):
    func = lib.__getattr__(func_name)
    func.restype = restype
    func.argtypes = argtypes
    if errcheck is not None:
        func.errcheck = errcheck
    return func
