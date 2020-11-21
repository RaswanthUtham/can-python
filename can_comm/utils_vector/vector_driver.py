"""
    created on oct 2020

    :file: vector_driver.py
    :platform: Windows
    :synopsis:
        Ctypes wrapper module for Vector hardware Interface on win32/win64 systems..
        Refer vector hardware driver documentation (XL Driver) for further details
        https://assets.vector.com/cms/content/products/XL_Driver_Library/Docs/XL_Driver_Library_Manual_EN.pdf
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""
# pylint:disable=wildcard-import, invalid-name, unused-wildcard-import
# Import Standard Python Modules
# ==============================
import logging
import platform
from ctypes import *
from ..utils_common import c_wrap
from . import v_def
from . import v_class
from . import VectorError

# Define Module Logger
# ====================
LOG = logging.getLogger(__name__)

# Load Windows DLL
try:
    DLL = "vxlapi64" if platform.architecture()[0] == "64bit" else "vxlapi"
    lib_v = windll.LoadLibrary(DLL)
except Exception as exc:
    DLL = None
    lib_v = None
    raise IOError("vector_dll is not loaded {}".format(exc))


def check_status(result, function, args):  # pylint:disable=unused-argument
    """
    checks the return value of a function call
    :param result: 0 if success, Non-Zero value otherwise
    :param function: function which has been executed
    :param args: arguments of the function which has been executed
    :return: 0 on success
    :raises VectorError: if result is Non-Zero
    """
    if result > 0:
        raise VectorError(result, xlGetErrorString(result).decode(), function.__name__)
    return result


# wrapping for API functions
xlGetErrorString = c_wrap(lib=lib_v,
                          func_name="xlGetErrorString",
                          restype=v_def.XLstringType,
                          argtypes=[v_def.XLstatus])

xlGetDriverConfig = c_wrap(lib=lib_v,
                           func_name="xlGetDriverConfig",
                           restype=v_def.XLstatus,
                           argtypes=[POINTER(v_class.XLdriverConfig)],
                           errcheck=check_status)

xlOpenDriver = c_wrap(lib=lib_v,
                      func_name="xlOpenDriver",
                      argtypes=[],
                      restype=v_def.XLstatus,
                      errcheck=check_status)

xlCloseDriver = c_wrap(lib=lib_v,
                       func_name="xlCloseDriver",
                       argtypes=[],
                       restype=v_def.XLstatus,
                       errcheck=check_status)

xlGetApplConfig = c_wrap(lib=lib_v,
                         func_name="xlGetApplConfig",
                         argtypes=[
                             c_char_p,
                             c_uint,
                             POINTER(c_uint),
                             POINTER(c_uint),
                             POINTER(c_uint),
                             c_uint,
                         ],
                         restype=v_def.XLstatus,
                         errcheck=check_status)

xlSetApplConfig = c_wrap(lib=lib_v,
                         func_name="xlSetApplConfig",
                         argtypes=[
                             c_char_p,
                             c_uint,
                             c_uint,
                             c_uint,
                             c_uint,
                             c_uint,
                         ],
                         restype=v_def.XLstatus,
                         errcheck=check_status)

xlGetChannelIndex = c_wrap(lib=lib_v,
                           func_name="xlGetChannelIndex",
                           argtypes=[c_int, c_int, c_int],
                           restype=c_int)

xlGetChannelMask = c_wrap(lib=lib_v,
                          func_name="xlGetChannelMask",
                          argtypes=[c_int, c_int, c_int],
                          restype=v_def.XLaccess)

xlOpenPort = c_wrap(lib=lib_v,
                    func_name="xlOpenPort",
                    argtypes=[
                        POINTER(v_def.XLportHandle),
                        c_char_p,
                        v_def.XLaccess,
                        POINTER(v_def.XLaccess),
                        c_uint,
                        c_uint,
                        c_uint,
                    ],
                    restype=v_def.XLstatus,
                    errcheck=check_status)

xlGetSyncTime = c_wrap(lib=lib_v,
                       func_name="xlGetSyncTime",
                       argtypes=[v_def.XLportHandle, POINTER(v_def.XLuint64)],
                       restype=v_def.XLstatus,
                       errcheck=check_status)

xlGetChannelTime = c_wrap(lib=lib_v,
                          func_name="xlGetChannelTime",
                          argtypes=[
                              v_def.XLportHandle,
                              v_def.XLaccess,
                              POINTER(v_def.XLuint64),
                          ],
                          restype=v_def.XLstatus,
                          errcheck=check_status)

xlClosePort = c_wrap(lib=lib_v,
                     func_name="xlClosePort",
                     argtypes=[v_def.XLportHandle],
                     restype=v_def.XLstatus,
                     errcheck=check_status)

xlSetNotification = c_wrap(lib=lib_v,
                           func_name="xlSetNotification",
                           argtypes=[
                               v_def.XLportHandle,
                               POINTER(v_def.XLhandle),
                               c_int,
                           ],
                           restype=v_def.XLstatus,
                           errcheck=check_status)

xlActivateChannel = c_wrap(lib=lib_v,
                           func_name="xlActivateChannel",
                           argtypes=[
                               v_def.XLportHandle,
                               v_def.XLaccess,
                               c_uint,
                               c_uint,
                           ],
                           restype=v_def.XLstatus,
                           errcheck=check_status)

xlDeactivateChannel = c_wrap(lib=lib_v,
                             func_name="xlDeactivateChannel",
                             argtypes=[v_def.XLportHandle, v_def.XLaccess],
                             restype=v_def.XLstatus,
                             errcheck=check_status)

xlPopupHwConfig = c_wrap(lib=lib_v,
                         func_name="xlPopupHwConfig",
                         argtypes=[c_char_p, c_uint],
                         restype=v_def.XLstatus,
                         errcheck=check_status)

xlSetTimerRate = c_wrap(lib=lib_v,
                        func_name="xlSetTimerRate",
                        argtypes=[v_def.XLportHandle, c_ulong],
                        restype=v_def.XLstatus,
                        errcheck=check_status)

xlGetEventString = c_wrap(lib=lib_v,
                          func_name="xlGetEventString",
                          argtypes=[POINTER(v_class.XLevent)],
                          restype=v_def.XLstringType)
