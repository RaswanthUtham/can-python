"""
    created on oct 2020

    :file: bus.py
    :platform: Windows
    :synopsis:
        can_comm related vector classes
        Refer vector hardware driver documentation (XL Driver) for further details
        https://assets.vector.com/cms/content/products/XL_Driver_Library/Docs/XL_Driver_Library_Manual_EN.pdf
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""
# pylint: disable=wildcard-import, unused-wildcard-import, too-few-public-methods, invalid-name
from ctypes import *
from .. import v_def


# CAN configuration structure
class XLchipParams(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [
        ("bitRate", c_ulong),
        ("sjw", c_ubyte),
        ("tseg1", c_ubyte),
        ("tseg2", c_ubyte),
        ("sam", c_ubyte),
    ]


# structure for XL_RECEIVE_MSG, XL_TRANSMIT_MSG
class s_xl_can_msg(Structure):
    """
    This structure is used for received CAN events as well as for CAN messages to be transmitted.
    """
    _fields_ = [
        ("id", c_ulong),
        ("flags", c_ushort),
        ("dlc", c_ushort),
        ("res1", v_def.XLuint64),
        ("data", c_ubyte * v_def.MAX_MSG_LEN),
        ("res2", v_def.XLuint64),
    ]


class s_xl_chip_state(Structure):
    """
    This event occurs after calling xlCanRequestChipState().
    """
    _fields_ = [
        ("busStatus", c_ubyte),
        ("txErrorCounter", c_ubyte),
        ("rxErrorCounter", c_ubyte),
    ]


# CAN FD configuration structure
class XLcanFdConf(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [
        ("arbitrationBitRate", c_uint),
        ("sjwAbr", c_uint),
        ("tseg1Abr", c_uint),
        ("tseg2Abr", c_uint),
        ("dataBitRate", c_uint),
        ("sjwDbr", c_uint),
        ("tseg1Dbr", c_uint),
        ("tseg2Dbr", c_uint),
        ("reserved", c_ubyte),
        ("options", c_ubyte),
        ("reserved1", c_ubyte * 2),
        ("reserved2", c_ubyte),
    ]


# CAN FD messages
class s_xl_can_ev_rx_msg(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    _fields_ = [
        ("canId", c_uint),
        ("msgFlags", c_uint),
        ("crc", c_uint),
        ("reserved1", c_ubyte * 12),
        ("totalBitCnt", c_ushort),
        ("dlc", c_ubyte),
        ("reserved", c_ubyte * 5),
        ("data", c_ubyte * v_def.XL_CAN_MAX_DATA_LEN),
    ]


class s_xl_can_ev_error(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [("errorCode", c_ubyte), ("reserved", c_ubyte * 95)]


class s_xl_can_ev_chip_state(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [
        ("busStatus", c_ubyte),
        ("txErrorCounter", c_ubyte),
        ("rxErrorCounter", c_ubyte),
        ("reserved", c_ubyte),
        ("reserved0", c_uint),
    ]


class s_xl_can_ev_tx_request(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [
        ("canId", c_uint),
        ("msgFlags", c_uint),
        ("dlc", c_ubyte),
        ("txAttemptConf", c_ubyte),
        ("reserved", c_ushort),
        ("data", c_ubyte * v_def.XL_CAN_MAX_DATA_LEN),
    ]


class s_xl_can_ev_sync_pulse(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [
        ("triggerSource", c_uint),
        ("reserved", c_uint),
        ("time", v_def.XLuint64),
    ]


# CAN FD events
class s_xl_can_tx_msg(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [
        ("canId", c_uint),
        ("msgFlags", c_uint),
        ("dlc", c_ubyte),
        ("reserved", c_ubyte * 7),
        ("data", c_ubyte * v_def.XL_CAN_MAX_DATA_LEN),
    ]


class s_txTagData(Union):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [("canMsg", s_xl_can_tx_msg)]


class XLcanTxEvent(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [
        ("tag", c_ushort),
        ("transId", c_ushort),
        ("chanIndex", c_ubyte),
        ("reserved", c_ubyte * 3),
        ("tagData", s_txTagData),
    ]


class s_rxTagData(Union):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [
        ("canRxOkMsg", s_xl_can_ev_rx_msg),
        ("canTxOkMsg", s_xl_can_ev_rx_msg),
        ("canTxRequest", s_xl_can_ev_tx_request),
        ("canError", s_xl_can_ev_error),
        ("canChipState", s_xl_can_ev_chip_state),
        ("canSyncPulse", s_xl_can_ev_sync_pulse),
    ]


class XLcanRxEvent(Structure):
    """
    Refer vector hardware driver documentation (XL Driver)
    """

    _fields_ = [
        ("size", c_int),
        ("tag", c_ushort),
        ("chanIndex", c_ubyte),
        ("reserved", c_ubyte),
        ("userHandle", c_int),
        ("flagsChip", c_ushort),
        ("reserved0", c_ushort),
        ("reserved1", v_def.XLuint64),
        ("timeStamp", v_def.XLuint64),
        ("tagData", s_rxTagData),
    ]
