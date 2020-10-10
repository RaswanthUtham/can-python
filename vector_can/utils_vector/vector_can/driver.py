"""
Ctypes wrapper module for Vector CAN Interface on win32/win64 systems.
"""
from ctypes import *
from . import vc_class
from .. import v_def
from .. import v_class
from .. import v_driver

xlCanSetChannelMode = v_driver.c_wrap(lib=v_driver.lib_v,
                                      func_name="xlCanSetChannelMode",
                                      argtypes=[
                                          v_def.XLportHandle,
                                          v_def.XLaccess,
                                          c_int,
                                          c_int,
                                      ],
                                      restype=v_def.XLstatus,
                                      errcheck=v_driver.check_status)

xlReceive = v_driver.c_wrap(lib=v_driver.lib_v,
                            func_name="xlReceive",
                            argtypes=[
                                v_def.XLportHandle,
                                POINTER(c_uint),
                                POINTER(v_class.XLevent),
                            ],
                            restype=v_def.XLstatus,
                            errcheck=v_driver.check_status)

xlCanSetChannelBitrate = v_driver.c_wrap(lib=v_driver.lib_v,
                                         func_name="xlCanSetChannelBitrate",
                                         argtypes=[
                                             v_def.XLportHandle,
                                             v_def.XLaccess,
                                             c_ulong,
                                         ],
                                         restype=v_def.XLstatus,
                                         errcheck=v_driver.check_status)

xlCanSetChannelParams = v_driver.c_wrap(lib=v_driver.lib_v,
                                        func_name="xlCanSetChannelParams",
                                        argtypes=[
                                            v_def.XLportHandle,
                                            v_def.XLaccess,
                                            POINTER(vc_class.XLchipParams),
                                        ],
                                        restype=v_def.XLstatus,
                                        errcheck=v_driver.check_status)

xlCanTransmit = v_driver.c_wrap(lib=v_driver.lib_v,
                                func_name="xlCanTransmit",
                                argtypes=[
                                    v_def.XLportHandle,
                                    v_def.XLaccess,
                                    POINTER(c_uint),
                                    POINTER(v_class.XLevent),
                                ],
                                restype=v_def.XLstatus,
                                errcheck=v_driver.check_status)

xlCanFlushTransmitQueue = v_driver.c_wrap(lib=v_driver.lib_v,
                                          func_name="xlCanFlushTransmitQueue",
                                          argtypes=[v_def.XLportHandle, v_def.XLaccess],
                                          restype=v_def.XLstatus,
                                          errcheck=v_driver.check_status)

xlCanSetChannelAcceptance = v_driver.c_wrap(lib=v_driver.lib_v,
                                            func_name="xlCanSetChannelAcceptance",
                                            argtypes=[
                                                v_def.XLportHandle,
                                                v_def.XLaccess,
                                                c_ulong,
                                                c_ulong,
                                                c_uint,
                                            ],
                                            restype=v_def.XLstatus,
                                            errcheck=v_driver.check_status)

xlCanResetAcceptance = v_driver.c_wrap(lib=v_driver.lib_v,
                                       func_name="xlCanResetAcceptance",
                                       argtypes=[v_def.XLportHandle, v_def.XLaccess, c_uint],
                                       restype=v_def.XLstatus,
                                       errcheck=v_driver.check_status)

xlCanRequestChipState = v_driver.c_wrap(lib=v_driver.lib_v,
                                        func_name="xlCanRequestChipState",
                                        argtypes=[v_def.XLportHandle, v_def.XLaccess],
                                        restype=v_def.XLstatus,
                                        errcheck=v_driver.check_status)

xlCanSetChannelOutput = v_driver.c_wrap(lib=v_driver.lib_v,
                                        func_name="xlCanSetChannelOutput",
                                        argtypes=[v_def.XLportHandle, v_def.XLaccess, c_char],
                                        restype=v_def.XLstatus,
                                        errcheck=v_driver.check_status)

# ------------------------------------- CAN-FD -----------------------------------------------------

xlCanFdSetConfiguration = v_driver.c_wrap(lib=v_driver.lib_v,
                                          func_name="xlCanFdSetConfiguration",
                                          argtypes=[
                                              v_def.XLportHandle,
                                              v_def.XLaccess,
                                              POINTER(vc_class.XLcanFdConf),
                                          ],
                                          restype=v_def.XLstatus,
                                          errcheck=v_driver.check_status)

xlCanReceive = v_driver.c_wrap(lib=v_driver.lib_v,
                               func_name="xlCanReceive",
                               argtypes=[v_def.XLportHandle, POINTER(vc_class.XLcanRxEvent)],
                               restype=v_def.XLstatus,
                               errcheck=v_driver.check_status)

xlCanTransmitEx = v_driver.c_wrap(lib=v_driver.lib_v,
                                  func_name="xlCanTransmitEx",
                                  argtypes=[
                                      v_def.XLportHandle,
                                      v_def.XLaccess,
                                      c_uint,
                                      POINTER(c_uint),
                                      POINTER(vc_class.XLcanTxEvent),
                                  ],
                                  restype=v_def.XLstatus,
                                  errcheck=v_driver.check_status)

xlCanGetEventString = v_driver.c_wrap(lib=v_driver.lib_v,
                                      func_name="xlCanGetEventString",
                                      argtypes=[POINTER(vc_class.XLcanRxEvent)],
                                      restype=v_def.XLstringType)
