"""
    created on oct 2020

    :file: vector_defines.py
    :platform: Windows
    :synopsis:
        Macros / CONSTANTS for vector device.
        Refer vector hardware driver documentation (XL Driver) for further details
        https://assets.vector.com/cms/content/products/XL_Driver_Library/Docs/XL_Driver_Library_Manual_EN.pdf
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""
# pylint: disable=wildcard-import, unused-wildcard-import, too-few-public-methods, invalid-name
# Import Python Modules
# ==============================
from enum import Enum
from ctypes import *

XLuint64 = c_int64
XLaccess = XLuint64
XLhandle = c_void_p
XLstatus = c_short
XLportHandle = c_long
XLeventTag = c_ubyte
XLstringType = c_char_p

MAX_MSG_LEN = 8
XL_CAN_MAX_DATA_LEN = 64
XL_INVALID_PORTHANDLE = -1


class XL_AC_Flags(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_ACTIVATE_NONE = 0
    XL_ACTIVATE_RESET_CLOCK = 8


class XL_AcceptanceFilter(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CAN_STD = 1
    XL_CAN_EXT = 2


class XL_BusCapabilities(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_BUS_COMPATIBLE_CAN = 1
    XL_BUS_ACTIVE_CAP_CAN = 65536


class XL_BusStatus(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CHIPSTAT_BUSOFF = 1
    XL_CHIPSTAT_ERROR_PASSIVE = 2
    XL_CHIPSTAT_ERROR_WARNING = 4
    XL_CHIPSTAT_ERROR_ACTIVE = 8


class XL_BusTypes(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_BUS_TYPE_NONE = 0
    XL_BUS_TYPE_CAN = 1


class XL_CANFD_BusParams_CanOpMode(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_BUS_PARAMS_CANOPMODE_CAN20 = 1
    XL_BUS_PARAMS_CANOPMODE_CANFD = 2
    XL_BUS_PARAMS_CANOPMODE_CANFD_NO_ISO = 8


class XL_CANFD_ConfigOptions(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    CANFD_CONFOPT_NO_ISO = 8


class XL_CANFD_RX_EV_ERROR_errorCode(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CAN_ERRC_BIT_ERROR = 1
    XL_CAN_ERRC_FORM_ERROR = 2
    XL_CAN_ERRC_STUFF_ERROR = 3
    XL_CAN_ERRC_OTHER_ERROR = 4
    XL_CAN_ERRC_CRC_ERROR = 5
    XL_CAN_ERRC_ACK_ERROR = 6
    XL_CAN_ERRC_NACK_ERROR = 7
    XL_CAN_ERRC_OVLD_ERROR = 8
    XL_CAN_ERRC_EXCPT_ERROR = 9


class XL_CANFD_RX_EventTags(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_SYNC_PULSE = 11
    XL_CAN_EV_TAG_RX_OK = 1024
    XL_CAN_EV_TAG_RX_ERROR = 1025
    XL_CAN_EV_TAG_TX_ERROR = 1026
    XL_CAN_EV_TAG_TX_REQUEST = 1027
    XL_CAN_EV_TAG_TX_OK = 1028
    XL_CAN_EV_TAG_CHIP_STATE = 1033


class XL_CANFD_RX_MessageFlags(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CAN_RXMSG_FLAG_NONE = 0
    XL_CAN_RXMSG_FLAG_EDL = 1
    XL_CAN_RXMSG_FLAG_BRS = 2
    XL_CAN_RXMSG_FLAG_ESI = 4
    XL_CAN_RXMSG_FLAG_RTR = 16
    XL_CAN_RXMSG_FLAG_EF = 512
    XL_CAN_RXMSG_FLAG_ARB_LOST = 1024
    XL_CAN_RXMSG_FLAG_WAKEUP = 8192
    XL_CAN_RXMSG_FLAG_TE = 16384


class XL_CANFD_TX_EventTags(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CAN_EV_TAG_TX_MSG = 1088  # =0x0440
    XL_CAN_EV_TAG_TX_ERRFR = 1089  # =0x0441


class XL_CANFD_TX_MessageFlags(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CAN_TXMSG_FLAG_NONE = 0
    XL_CAN_TXMSG_FLAG_EDL = 1
    XL_CAN_TXMSG_FLAG_BRS = 2
    XL_CAN_TXMSG_FLAG_RTR = 16
    XL_CAN_TXMSG_FLAG_HIGHPRIO = 128
    XL_CAN_TXMSG_FLAG_WAKEUP = 512


class XL_ChannelCapabilities(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CHANNEL_FLAG_TIME_SYNC_RUNNING = 1
    XL_CHANNEL_FLAG_NO_HWSYNC_SUPPORT = 1024
    XL_CHANNEL_FLAG_SPDIF_CAPABLE = 16384
    XL_CHANNEL_FLAG_CANFD_BOSCH_SUPPORT = 536870912
    XL_CHANNEL_FLAG_CMACTLICENSE_SUPPORT = 1073741824
    XL_CHANNEL_FLAG_CANFD_ISO_SUPPORT = 2147483648


class XL_EventTags(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_NO_COMMAND = 0
    XL_RECEIVE_MSG = 1
    XL_CHIP_STATE = 4
    XL_TRANSCEIVER = 6
    XL_TIMER = 8
    XL_TRANSMIT_MSG = 10
    XL_SYNC_PULSE = 11
    XL_APPLICATION_NOTIFICATION = 15


class XL_InterfaceVersion(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_INTERFACE_VERSION_V2 = 2
    XL_INTERFACE_VERSION_V3 = 3
    XL_INTERFACE_VERSION = XL_INTERFACE_VERSION_V3
    XL_INTERFACE_VERSION_V4 = 4


class XL_MessageFlags(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CAN_MSG_FLAG_NONE = 0
    XL_CAN_MSG_FLAG_ERROR_FRAME = 1
    XL_CAN_MSG_FLAG_OVERRUN = 2
    XL_CAN_MSG_FLAG_NERR = 4
    XL_CAN_MSG_FLAG_WAKEUP = 8
    XL_CAN_MSG_FLAG_REMOTE_FRAME = 16
    XL_CAN_MSG_FLAG_RESERVED_1 = 32
    XL_CAN_MSG_FLAG_TX_COMPLETED = 64
    XL_CAN_MSG_FLAG_TX_REQUEST = 128
    XL_CAN_MSG_FLAG_SRR_BIT_DOM = 512
    XL_EVENT_FLAG_OVERRUN = 1


class XL_MessageFlagsExtended(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_CAN_EXT_MSG_ID = 2147483648


class XL_OutputMode(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_OUTPUT_MODE_SILENT = 0
    XL_OUTPUT_MODE_NORMAL = 1
    XL_OUTPUT_MODE_TX_OFF = 2
    XL_OUTPUT_MODE_SJA_1000_SILENT = 3


class XL_Sizes(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_MAX_LENGTH = 31
    XL_MAX_APPNAME = 32
    XL_MAX_NAME_LENGTH = 48
    XLEVENT_SIZE = 48
    XL_CONFIG_MAX_CHANNELS = 64
    XL_APPLCONFIG_MAX_CHANNELS = 256


class XL_Status(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_SUCCESS = 0  # =0x0000
    XL_PENDING = 1  # =0x0001
    XL_ERR_QUEUE_IS_EMPTY = 10  # =0x000A
    XL_ERR_QUEUE_IS_FULL = 11  # =0x000B
    XL_ERR_TX_NOT_POSSIBLE = 12  # =0x000C
    XL_ERR_NO_LICENSE = 14  # =0x000E
    XL_ERR_WRONG_PARAMETER = 101  # =0x0065
    XL_ERR_TWICE_REGISTER = 110  # =0x006E
    XL_ERR_INVALID_CHAN_INDEX = 111  # =0x006F
    XL_ERR_INVALID_ACCESS = 112  # =0x0070
    XL_ERR_PORT_IS_OFFLINE = 113  # =0x0071
    XL_ERR_CHAN_IS_ONLINE = 116  # =0x0074
    XL_ERR_NOT_IMPLEMENTED = 117  # =0x0075
    XL_ERR_INVALID_PORT = 118  # =0x0076
    XL_ERR_HW_NOT_READY = 120  # =0x0078
    XL_ERR_CMD_TIMEOUT = 121  # =0x0079
    XL_ERR_HW_NOT_PRESENT = 129  # =0x0081
    XL_ERR_NOTIFY_ALREADY_ACTIVE = 131  # =0x0083
    XL_ERR_NO_RESOURCES = 152  # =0x0098
    XL_ERR_WRONG_CHIP_TYPE = 153  # =0x0099
    XL_ERR_WRONG_COMMAND = 154  # =0x009A
    XL_ERR_INVALID_HANDLE = 155  # =0x009B
    XL_ERR_RESERVED_NOT_ZERO = 157  # =0x009D
    XL_ERR_INIT_ACCESS_MISSING = 158  # =0x009E
    XL_ERR_CANNOT_OPEN_DRIVER = 201  # =0x00C9
    XL_ERR_WRONG_BUS_TYPE = 202  # =0x00CA
    XL_ERR_DLL_NOT_FOUND = 203  # =0x00CB
    XL_ERR_INVALID_CHANNEL_MASK = 204  # =0x00CC
    XL_ERR_NOT_SUPPORTED = 205  # =0x00CD
    XL_ERR_CONNECTION_BROKEN = 210  # =0x00D2
    XL_ERR_CONNECTION_CLOSED = 211  # =0x00D3
    XL_ERR_INVALID_STREAM_NAME = 212  # =0x00D4
    XL_ERR_CONNECTION_FAILED = 213  # =0x00D5
    XL_ERR_STREAM_NOT_FOUND = 214  # =0x00D6
    XL_ERR_STREAM_NOT_CONNECTED = 215  # =0x00D7
    XL_ERR_QUEUE_OVERRUN = 216  # =0x00D8
    XL_ERROR = 255  # =0x00FF

    # CAN FD Error Codes
    XL_ERR_INVALID_DLC = 513  # =0x0201
    XL_ERR_INVALID_CANID = 514  # =0x0202
    XL_ERR_INVALID_FDFLAG_MODE20 = 515  # =0x203
    XL_ERR_EDL_RTR = 516  # =0x204
    XL_ERR_EDL_NOT_SET = 517  # =0x205
    XL_ERR_UNKNOWN_FLAG = 518  # =0x206


class XL_TimeSyncNewValue(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_SET_TIMESYNC_NO_CHANGE = 0
    XL_SET_TIMESYNC_ON = 1
    XL_SET_TIMESYNC_OFF = 2


class XL_HardwareType(Enum):
    """
    Refer vector hardware driver documentation (XL Driver)
    """
    XL_HWTYPE_NONE = 0
    XL_HWTYPE_VIRTUAL = 1
    XL_HWTYPE_CANCARDX = 2
    XL_HWTYPE_CANAC2PCI = 6
    XL_HWTYPE_CANCARDY = 12
    XL_HWTYPE_CANCARDXL = 15
    XL_HWTYPE_CANCASEXL = 21
    XL_HWTYPE_CANCASEXL_LOG_OBSOLETE = 23
    XL_HWTYPE_CANBOARDXL = 25
    XL_HWTYPE_CANBOARDXL_PXI = 27
    XL_HWTYPE_VN2600 = 29
    XL_HWTYPE_VN2610 = XL_HWTYPE_VN2600
    XL_HWTYPE_VN3300 = 37
    XL_HWTYPE_VN3600 = 39
    XL_HWTYPE_VN7600 = 41
    XL_HWTYPE_CANCARDXLE = 43
    XL_HWTYPE_VN8900 = 45
    XL_HWTYPE_VN8950 = 47
    XL_HWTYPE_VN2640 = 53
    XL_HWTYPE_VN1610 = 55
    XL_HWTYPE_VN1630 = 57
    XL_HWTYPE_VN1640 = 59
    XL_HWTYPE_VN8970 = 61
    XL_HWTYPE_VN1611 = 63
    XL_HWTYPE_VN5610 = 65
    XL_HWTYPE_VN5620 = 66
    XL_HWTYPE_VN7570 = 67
    XL_HWTYPE_IPCLIENT = 69
    XL_HWTYPE_IPSERVER = 71
    XL_HWTYPE_VX1121 = 73
    XL_HWTYPE_VX1131 = 75
    XL_HWTYPE_VT6204 = 77
    XL_HWTYPE_VN1630_LOG = 79
    XL_HWTYPE_VN7610 = 81
    XL_HWTYPE_VN7572 = 83
    XL_HWTYPE_VN8972 = 85
    XL_HWTYPE_VN0601 = 87
    XL_HWTYPE_VN5640 = 89
    XL_HWTYPE_VX0312 = 91
    XL_HWTYPE_VH6501 = 94
    XL_HWTYPE_VN8800 = 95
    XL_HWTYPE_IPCL8800 = 96
    XL_HWTYPE_IPSRV8800 = 97
    XL_HWTYPE_CSMCAN = 98
    XL_HWTYPE_VN5610A = 101
    XL_HWTYPE_VN7640 = 102
    XL_HWTYPE_VX1135 = 104
    XL_HWTYPE_VN4610 = 105
    XL_HWTYPE_VT6306 = 107
    XL_HWTYPE_VT6104A = 108
    XL_HWTYPE_VN5430 = 109
    XL_HWTYPE_VN1530 = 112
    XL_HWTYPE_VN1531 = 113
    XL_MAX_HWTYPE = 113
