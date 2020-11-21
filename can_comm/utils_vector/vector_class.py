"""
    created on oct 2020

    :file: vector_class.py
    :platform: Windows
    :synopsis:
        Common vector classes.
        Refer vector hardware driver documentation (XL Driver) for further details
        https://assets.vector.com/cms/content/products/XL_Driver_Library/Docs/XL_Driver_Library_Manual_EN.pdf
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""
# pylint: disable=wildcard-import, unused-wildcard-import, too-few-public-methods, invalid-name
# Import Standard Python Modules
# ==============================

from ctypes import *
from . import v_def
from . import vc_class


# BASIC bus message structure
class s_xl_tag_data(Union):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [("msg", vc_class.s_xl_can_msg), ("chipState", vc_class.s_xl_chip_state)]


class XLevent(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [
        ("tag", v_def.XLeventTag),
        ("chanIndex", c_ubyte),
        ("transId", c_ushort),
        ("portHandle", c_ushort),
        ("flags", c_ubyte),
        ("reserved", c_ubyte),
        ("timeStamp", v_def.XLuint64),
        ("tagData", s_xl_tag_data),
    ]


# channel configuration structures
class s_xl_bus_params_data_can(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [
        ("bitRate", c_uint),
        ("sjw", c_ubyte),
        ("tseg1", c_ubyte),
        ("tseg2", c_ubyte),
        ("sam", c_ubyte),
        ("outputMode", c_ubyte),
        ("reserved", c_ubyte * 7),
        ("canOpMode", c_ubyte),
    ]


class s_xl_bus_params_data_canfd(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [
        ("arbitrationBitRate", c_uint),
        ("sjwAbr", c_ubyte),
        ("tseg1Abr", c_ubyte),
        ("tseg2Abr", c_ubyte),
        ("samAbr", c_ubyte),
        ("outputMode", c_ubyte),
        ("sjwDbr", c_ubyte),
        ("tseg1Dbr", c_ubyte),
        ("tseg2Dbr", c_ubyte),
        ("dataBitRate", c_uint),
        ("canOpMode", c_ubyte),
    ]


class s_xl_bus_params_data(Union):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [
        ("can_comm", s_xl_bus_params_data_can),
        ("canFD", s_xl_bus_params_data_canfd),
        ("most", c_ubyte * 12),
        ("flexray", c_ubyte * 12),
        ("ethernet", c_ubyte * 12),
        ("a429", c_ubyte * 28),
    ]


class XLbusParams(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [("busType", c_uint), ("data", s_xl_bus_params_data)]


class XLchannelConfig(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _pack_ = 1
    _fields_ = [
        ("name", c_char * 32),
        ("hwType", c_ubyte),
        ("hwIndex", c_ubyte),
        ("hwChannel", c_ubyte),
        ("transceiverType", c_ushort),
        ("transceiverState", c_ushort),
        ("configError", c_ushort),
        ("channelIndex", c_ubyte),
        ("channelMask", v_def.XLuint64),
        ("channelCapabilities", c_uint),
        ("channelBusCapabilities", c_uint),
        ("isOnBus", c_ubyte),
        ("connectedBusType", c_uint),
        ("busParams", XLbusParams),
        ("_doNotUse", c_uint),
        ("driverVersion", c_uint),
        ("interfaceVersion", c_uint),
        ("raw_data", c_uint * 10),
        ("serialNumber", c_uint),
        ("articleNumber", c_uint),
        ("transceiverName", c_char * 32),
        ("specialCabFlags", c_uint),
        ("dominantTimeout", c_uint),
        ("dominantRecessiveDelay", c_ubyte),
        ("recessiveDominantDelay", c_ubyte),
        ("connectionInfo", c_ubyte),
        ("currentlyAvailableTimestamps", c_ubyte),
        ("minimalSupplyVoltage", c_ushort),
        ("maximalSupplyVoltage", c_ushort),
        ("maximalBaudrate", c_uint),
        ("fpgaCoreCapabilities", c_ubyte),
        ("specialDeviceStatus", c_ubyte),
        ("channelBusActiveCapabilities", c_ushort),
        ("breakOffset", c_ushort),
        ("delimiterOffset", c_ushort),
        ("reserved", c_uint * 3),
    ]


class XLdriverConfig(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [
        ("dllVersion", c_uint),
        ("channelCount", c_uint),
        ("reserved", c_uint * 10),
        ("channel", XLchannelConfig * 64),
    ]
