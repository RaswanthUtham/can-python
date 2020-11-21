"""
    created on oct 2020

    :file: bus.py
    :platform: Windows
    :synopsis:
        Vector CAN bus implementation
        Refer vector hardware driver documentation (XL Driver) for further details
        https://assets.vector.com/cms/content/products/XL_Driver_Library/Docs/XL_Driver_Library_Manual_EN.pdf
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""

# Import Standard Python Modules
# ==============================
# pylint:disable=line-too-long, wildcard-import, invalid-name, unused-wildcard-import
from ctypes import *
import logging
import time
import os
from copy import deepcopy
import typing

try:
    # Try builtin Python 3 Windows API
    from _winapi import WaitForSingleObject, INFINITE

    HAS_EVENTS = True
except ImportError:
    try:
        # Try pywin32 package
        from win32event import WaitForSingleObject, INFINITE

        HAS_EVENTS = True
    except ImportError:
        # Use polling instead
        HAS_EVENTS = False

# Import CAN utils
# ==============
from ...utils_can import TypeCheck
from ...utils_can import CanBus, CanMessage
from ...utils_can import len2dlc, dlc2len

# Import Vector utils
# ========================
from .. import VectorError
from .. import vc_class
from .. import v_class
from .. import v_def
from .. import VectorCanApi

# Define Module Logger
# ====================
LOG = logging.getLogger(__name__)


class VectorCanBus(CanBus):
    """Vector CAN bus implementation"""

    # pylint:disable=too-many-instance-attributes, too-many-arguments, too-many-locals
    def __init__(self,
                 channel: TypeCheck.v_channel,
                 can_filters: typing.Optional[TypeCheck.CanFilters] = None,
                 poll_interval: float = 0.01,
                 receive_own_messages: bool = False,
                 bitrate: int = None,
                 rx_queue_size: int = 2 ** 14,
                 app_name: str = "CANoe",
                 serial: int = None,
                 fd: bool = False,
                 data_bitrate: int = None,
                 sjw_abr: int = 2,
                 tseg1_abr: int = 6,
                 tseg2_abr: int = 3,
                 sjw_dbr: int = 2,
                 tseg1_dbr: int = 6,
                 tseg2_dbr: int = 3,
                 ):
        """
                :param list channel:
                    The channel indexes to create this bus with.
                    Can also be a single integer or a comma separated string.
                :param float poll_interval:
                    Poll interval in seconds.
                :param int bitrate:
                    Bitrate in bits/s.
                :param int rx_queue_size:
                    Number of messages in receive queue (power of 2).
                    CAN: range 16…32768
                    CAN-FD: range 8192…524288
                :param str app_name:
                    Name of application in Hardware Config.
                    If set to None, the channel should be a global channel index.
                :param int serial:
                    Serial number of the hardware to be used.
                    If set, the channel parameter refers to the channels ONLY on the specified hardware.
                    If set, the app_name is unused.
                :param bool fd:
                    If CAN-FD frames should be supported.
                :param int data_bitrate:
                    Which bitrate to use for data phase in CAN FD.
                    Defaults to arbitration bitrate.
                :param int sjw_abr:
                    Bus timing value sample jump width (arbitration).
                :param int tseg1_abr:
                    Bus timing value tseg1 (arbitration)
                :param int tseg2_abr:
                    Bus timing value tseg2 (arbitration)
                :param int sjw_dbr:
                    Bus timing value sample jump width (data)
                :param int tseg1_dbr:
                    Bus timing value tseg1 (data)
                :param int tseg2_dbr:
                    Bus timing value tseg2 (data)
                """
        if os.name != "nt":
            raise OSError(
                f'The Vector interface is only supported on Windows, but you are running "{os.name}"'
            )
        self.poll_interval = poll_interval
        self.channels = self._init_channel(deepcopy(channel))
        self._app_name = app_name.encode() if app_name is not None else b""
        self.channel_info = "app: %s\nch: %s" % (app_name, ", ".join("CAN %d" % (ch + 1) for ch in self.channels))

        if serial is not None:
            app_name = None
            self.channels = self._get_channel_index(serial)

        VectorCanApi.xlOpenDriver()

        self.port_handle = v_def.XLportHandle(v_def.XL_INVALID_PORTHANDLE)
        self.mask = 0
        self.fd = fd
        # Get channels masks
        self.channel_masks = {}
        self.index_to_channel = {}

        self._config_channel_attrs(app_name)

        self.permission_mask = v_def.XLaccess()
        if bitrate or fd:
            self.permission_mask.value = self.mask

        self._open_port(rx_queue_size)

        if self.mask == self.permission_mask.value:
            # has init access
            self._config_baud_rate(bitrate, data_bitrate, sjw_abr, tseg1_abr, tseg2_abr,
                                   sjw_dbr, tseg1_dbr, tseg2_dbr)
        else:
            LOG.info("No init access!")

        self._activate_channel(receive_own_messages)
        self._time_offset = self._calculate_time_offset()

        self._is_filtered = False
        super().__init__(can_filters=can_filters)

    @staticmethod
    def _init_channel(channel: TypeCheck.v_channel):
        if isinstance(channel, (list, tuple)):
            return channel
        if isinstance(channel, int):
            return [channel]
        # Assume comma separated string of channels
        return [int(ch.strip()) for ch in channel.split(",")]

    def _get_channel_index(self, serial):
        """
        Invoked from __init__ iff hw serial number is given
        :param serial: hw serial number
        :return: channel index
        """
        channel_index = []
        channel_configs = get_channel_configs()
        for channel_config in channel_configs:
            if channel_config.serialNumber == serial:
                if channel_config.hwChannel in self.channels:
                    channel_index.append(channel_config.channelIndex)
        if channel_index:
            if len(channel_index) != len(self.channels):
                LOG.info(
                    "At least one defined channel wasn't found on the specified hardware."
                )
            return channel_index
        raise Exception("None of the configured channels could be found on the specified hardware.")

    def _config_channel_attrs(self, app_name):
        for channel in self.channels:
            if app_name:
                # Get global channel index from application channel
                hw_type, hw_index, hw_channel = self.get_application_config(
                    app_name, channel, v_def.XL_BusTypes.XL_BUS_TYPE_CAN
                )
                LOG.debug("Channel index %d found", channel)
                idx = VectorCanApi.xlGetChannelIndex(hw_type.value, hw_index, hw_channel)
                if idx < 0:
                    # Undocumented behavior! See issue #353.
                    # If hardware is unavailable, this function returns -1.
                    # Raise an exception as if the driver
                    # would have signalled XL_ERR_HW_NOT_PRESENT.
                    raise VectorError(
                        v_def.XL_Status.XL_ERR_HW_NOT_PRESENT.value,
                        v_def.XL_Status.XL_ERR_HW_NOT_PRESENT.name,
                        "xlGetChannelIndex",
                    )
            else:
                # Channel already given as global channel
                idx = channel
            mask = 1 << idx
            self.channel_masks[channel] = mask
            self.index_to_channel[idx] = channel
            self.mask |= mask

    def _open_port(self, queue_size):
        if self.fd:
            VectorCanApi.xlOpenPort(
                self.port_handle,
                self._app_name,
                self.mask,
                self.permission_mask,
                queue_size,
                v_def.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4.value,
                v_def.XL_BusTypes.XL_BUS_TYPE_CAN.value,
            )
        else:
            VectorCanApi.xlOpenPort(
                self.port_handle,
                self._app_name,
                self.mask,
                self.permission_mask,
                queue_size,
                v_def.XL_InterfaceVersion.XL_INTERFACE_VERSION.value,
                v_def.XL_BusTypes.XL_BUS_TYPE_CAN.value,
            )
        LOG.debug(
            "Open Port: PortHandle: %d, PermissionMask: 0x%X",
            self.port_handle.value,
            self.permission_mask.value,
        )

    def _config_baud_rate(self, bitrate, data_bitrate, sjw_abr, tseg1_abr, tseg2_abr,
                          sjw_dbr, tseg1_dbr, tseg2_dbr):
        if self.fd:
            self.canFdConf = vc_class.XLcanFdConf()
            if bitrate:
                self.canFdConf.arbitrationBitRate = int(bitrate)
            else:
                self.canFdConf.arbitrationBitRate = 500000
            self.canFdConf.sjwAbr = int(sjw_abr)
            self.canFdConf.tseg1Abr = int(tseg1_abr)
            self.canFdConf.tseg2Abr = int(tseg2_abr)
            if data_bitrate:
                self.canFdConf.dataBitRate = int(data_bitrate)
            else:
                self.canFdConf.dataBitRate = self.canFdConf.arbitrationBitRate
            self.canFdConf.sjwDbr = int(sjw_dbr)
            self.canFdConf.tseg1Dbr = int(tseg1_dbr)
            self.canFdConf.tseg2Dbr = int(tseg2_dbr)

            VectorCanApi.xlCanFdSetConfiguration(
                self.port_handle, self.mask, self.canFdConf
            )
            LOG.info(
                "SetFdConfig.: ABaudr.=%u, DBaudr.=%u",
                self.canFdConf.arbitrationBitRate,
                self.canFdConf.dataBitRate,
            )
            LOG.info(
                "SetFdConfig.: sjwAbr=%u, tseg1Abr=%u, tseg2Abr=%u",
                self.canFdConf.sjwAbr,
                self.canFdConf.tseg1Abr,
                self.canFdConf.tseg2Abr,
            )
            LOG.info(
                "SetFdConfig.: sjwDbr=%u, tseg1Dbr=%u, tseg2Dbr=%u",
                self.canFdConf.sjwDbr,
                self.canFdConf.tseg1Dbr,
                self.canFdConf.tseg2Dbr,
            )
        else:
            if bitrate:
                VectorCanApi.xlCanSetChannelBitrate(
                    self.port_handle, self.permission_mask, bitrate
                )
                LOG.info("SetChannelBitrate: baudr.=%u", bitrate)

    def _activate_channel(self, receive_own_messages):
        # Enable/disable TX receipts
        tx_receipts = 1 if receive_own_messages else 0
        VectorCanApi.xlCanSetChannelMode(self.port_handle, self.mask, tx_receipts, 0)

        if HAS_EVENTS:
            self.event_handle = v_def.XLhandle()
            VectorCanApi.xlSetNotification(self.port_handle, self.event_handle, 1)
        else:
            LOG.info("Install pywin32 to avoid polling")

        try:
            VectorCanApi.xlActivateChannel(
                self.port_handle,
                self.mask,
                v_def.XL_BusTypes.XL_BUS_TYPE_CAN.value,
                0,
            )
        except VectorError:
            self.shutdown()
            raise Exception("Error in channel activation")

    def _calculate_time_offset(self):
        # Calculate time offset for absolute timestamps
        offset = v_def.XLuint64()
        try:
            try:
                VectorCanApi.xlGetSyncTime(self.port_handle, offset)
            except VectorError:
                VectorCanApi.xlGetChannelTime(self.port_handle, self.mask, offset)
            return time.time() - offset.value * 1e-9
        except VectorError:
            return 0.0

    def _apply_filters(self, filters):
        """
        Invoked from super class method: set_filter
        :param filters: message filter
        :return: None
        """
        if filters:
            # Only up to one filter per ID type allowed
            if len(filters) == 1 or (len(filters) == 2 and filters[0].get("extended") != filters[1].get("extended")):
                try:
                    for can_filter in filters:
                        VectorCanApi.xlCanSetChannelAcceptance(
                            self.port_handle,
                            self.mask,
                            can_filter["can_id"],
                            can_filter["can_mask"],
                            v_def.XL_AcceptanceFilter.XL_CAN_EXT.value
                            if can_filter.get("extended")
                            else v_def.XL_AcceptanceFilter.XL_CAN_STD.value,
                        )
                except VectorError as exc:
                    LOG.warning("Could not set filters: %s", exc)
                    # go to fallback
                else:
                    self._is_filtered = True
                    return
            else:
                LOG.warning("Only up to one filter per extended or standard ID allowed")
                # go to fallback

        # fallback: reset filters
        self._reset_filters()

    def _reset_filters(self):
        self._is_filtered = False
        try:
            VectorCanApi.xlCanSetChannelAcceptance(
                self.port_handle,
                self.mask,
                0x0,
                0x0,
                v_def.XL_AcceptanceFilter.XL_CAN_EXT.value,
            )
            VectorCanApi.xlCanSetChannelAcceptance(
                self.port_handle,
                self.mask,
                0x0,
                0x0,
                v_def.XL_AcceptanceFilter.XL_CAN_STD.value,
            )
        except VectorError as exc:
            LOG.warning("Could not reset filters: %s", exc)

    def _receive_from_interface(self,
                                timeout: typing.Optional[float]
                                ) -> typing.Tuple[typing.Optional[CanMessage], bool]:

        end_time = time.time() + timeout if timeout is not None else None

        while True:
            try:
                if self.fd:
                    msg = self._recv_canfd()
                else:
                    msg = self._recv_can()

            except VectorError as exc:
                if exc.error_code != v_def.XL_Status.XL_ERR_QUEUE_IS_EMPTY.value:
                    raise
            else:
                if msg:
                    return msg, self._is_filtered

            # if no message was received, wait or return on timeout
            if end_time is not None and time.time() > end_time:
                return None, self._is_filtered

            if HAS_EVENTS:
                # Wait for receive event to occur
                if end_time is None:
                    time_left_ms = INFINITE
                else:
                    time_left = end_time - time.time()
                    time_left_ms = max(0, int(time_left * 1000))
                WaitForSingleObject(self.event_handle.value, time_left_ms)
            else:
                # Wait a short time until we try again
                time.sleep(self.poll_interval)

    def _recv_can(self) -> typing.Optional[CanMessage]:
        xl_event = v_class.XLevent()
        event_count = c_uint(1)
        VectorCanApi.xlReceive(self.port_handle, event_count, xl_event)

        if xl_event.tag != v_def.XL_EventTags.XL_RECEIVE_MSG.value:
            self.handle_can_event(xl_event)
            return None

        msg_id = xl_event.tagData.msg.id
        dlc = xl_event.tagData.msg.dlc
        flags = xl_event.tagData.msg.flags
        timestamp = xl_event.timeStamp * 1e-9
        channel = self.index_to_channel.get(xl_event.chanIndex, None)

        msg = CanMessage(
            timestamp=timestamp + self._time_offset,
            arbitration_id=msg_id & 0x1FFFFFFF,
            is_extended_id=bool(
                msg_id & v_def.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID.value
            ),
            is_remote_frame=bool(
                flags & v_def.XL_MessageFlags.XL_CAN_MSG_FLAG_REMOTE_FRAME.value
            ),
            is_error_frame=bool(
                flags & v_def.XL_MessageFlags.XL_CAN_MSG_FLAG_ERROR_FRAME.value
            ),
            is_rx=not bool(
                flags & v_def.XL_MessageFlags.XL_CAN_MSG_FLAG_TX_COMPLETED.value
            ),
            is_fd=False,
            dlc=dlc,
            data=xl_event.tagData.msg.data[:dlc],
            channel=channel,
        )
        return msg

    def _recv_canfd(self) -> typing.Optional[CanMessage]:
        xl_can_rx_event = vc_class.XLcanRxEvent()
        VectorCanApi.xlCanReceive(self.port_handle, xl_can_rx_event)

        if xl_can_rx_event.tag == v_def.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_RX_OK.value:
            is_rx = True
            data_struct = xl_can_rx_event.tagData.canRxOkMsg
        elif xl_can_rx_event.tag == v_def.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_TX_OK.value:
            is_rx = False
            data_struct = xl_can_rx_event.tagData.canTxOkMsg
        else:
            self.handle_canfd_event(xl_can_rx_event)
            return None

        msg_id = data_struct.canId
        dlc = dlc2len(data_struct.dlc)
        flags = data_struct.msgFlags
        timestamp = xl_can_rx_event.timeStamp * 1e-9
        channel = self.index_to_channel.get(xl_can_rx_event.chanIndex)

        msg = CanMessage(
            timestamp=timestamp + self._time_offset,
            arbitration_id=msg_id & 0x1FFFFFFF,
            is_extended_id=bool(
                msg_id & v_def.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID.value
            ),
            is_remote_frame=bool(
                flags & v_def.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_RTR.value
            ),
            is_error_frame=bool(
                flags & v_def.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_EF.value
            ),
            is_fd=bool(
                flags & v_def.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_EDL.value
            ),
            bitrate_switch=bool(
                flags & v_def.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_BRS.value
            ),
            error_state_indicator=bool(
                flags & v_def.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_ESI.value
            ),
            is_rx=is_rx,
            channel=channel,
            dlc=dlc,
            data=data_struct.data[:dlc],
        )
        return msg

    def handle_can_event(self, event: v_class.XLevent) -> None:
        """Handle non-message CAN events.

        Method is called by :meth:`~can_comm.interfaces.vector.VectorBus._recv_internal`
        when `event.tag` is not `XL_RECEIVE_MSG`. Subclasses can_comm implement this method.

        :param event: XLevent that could have a `XL_CHIP_STATE`, `XL_TIMER` or `XL_SYNC_PULSE` tag.
        :return: None
        """
        raise NotImplementedError

    def handle_canfd_event(self, event: vc_class.XLcanRxEvent) -> None:
        """Handle non-message CAN FD events.

        Method is called by :meth:`~can_comm.interfaces.vector.VectorBus._recv_internal`
        when `event.tag` is not `XL_CAN_EV_TAG_RX_OK` or `XL_CAN_EV_TAG_TX_OK`.
        Subclasses can_comm implement this method.

        :param event: `XLcanRxEvent` that could have a `XL_CAN_EV_TAG_RX_ERROR`, `XL_CAN_EV_TAG_TX_ERROR`,
            `XL_TIMER` or `XL_CAN_EV_TAG_CHIP_STATE` tag.
        :return: None
        """
        raise NotImplementedError

    def send(self, msgs: CanMessage) -> int:  # pylint:disable=arguments-differ
        """Send messages and return number of successful transmissions."""
        if self.fd:
            return self._send_can_fd_msg_sequence([msgs])
        return self._send_can_msg_sequence([msgs])

    def _send_can_msg_sequence(self, msgs: typing.Sequence[CanMessage]) -> int:
        """Send CAN messages and return number of successful transmissions."""
        mask = self._get_tx_channel_mask(msgs)
        message_count = c_uint(len(msgs))

        xl_event_array = (v_class.XLevent * message_count.value)(
            *map(self._build_xl_event, msgs)
        )

        VectorCanApi.xlCanTransmit(self.port_handle, mask, message_count, xl_event_array)
        return message_count.value

    def _get_tx_channel_mask(self, msgs: typing.Sequence[CanMessage]) -> int:
        if len(msgs) == 1:
            return self.channel_masks.get(msgs[0].channel, self.mask)
        return self.mask

    @staticmethod
    def _build_xl_event(msg: CanMessage) -> v_class.XLevent:
        msg_id = msg.arbitration_id
        if msg.is_extended_id:
            msg_id |= v_def.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID.value

        flags = 0
        if msg.is_remote_frame:
            flags |= v_def.XL_MessageFlags.XL_CAN_MSG_FLAG_REMOTE_FRAME.value

        xl_event = v_class.XLevent()
        xl_event.tag = v_def.XL_EventTags.XL_TRANSMIT_MSG.value
        xl_event.tagData.msg.id = msg_id
        xl_event.tagData.msg.dlc = msg.dlc
        xl_event.tagData.msg.flags = flags
        xl_event.tagData.msg.data = tuple(msg.data)

        return xl_event

    def _send_can_fd_msg_sequence(self, msgs: typing.Sequence[CanMessage]) -> int:
        """Send CAN FD messages and return number of successful transmissions."""
        mask = self._get_tx_channel_mask(msgs)
        message_count = c_uint(len(msgs))

        xl_can_tx_event_array = (vc_class.XLcanTxEvent * message_count.value)(
            *map(self._build_xl_can_tx_event, msgs)
        )

        msg_count_sent = c_uint(0)
        VectorCanApi.xlCanTransmitEx(
            self.port_handle, mask, message_count, msg_count_sent, xl_can_tx_event_array
        )
        return msg_count_sent.value

    @staticmethod
    def _build_xl_can_tx_event(msg: CanMessage) -> vc_class.XLcanTxEvent:
        msg_id = msg.arbitration_id
        if msg.is_extended_id:
            msg_id |= v_def.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID.value

        flags = 0
        if msg.is_fd:
            flags |= v_def.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_EDL.value
        if msg.bitrate_switch:
            flags |= v_def.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_BRS.value
        if msg.is_remote_frame:
            flags |= v_def.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_RTR.value

        xl_can_tx_event = vc_class.XLcanTxEvent()
        xl_can_tx_event.tag = v_def.XL_CANFD_TX_EventTags.XL_CAN_EV_TAG_TX_MSG.value
        xl_can_tx_event.transId = 0xFFFF

        xl_can_tx_event.tagData.canMsg.canId = msg_id
        xl_can_tx_event.tagData.canMsg.msgFlags = flags
        xl_can_tx_event.tagData.canMsg.dlc = len2dlc(msg.dlc)
        xl_can_tx_event.tagData.canMsg.data = tuple(msg.data)

        return xl_can_tx_event

    def flush_tx_buffer(self):
        VectorCanApi.xlCanFlushTransmitQueue(self.port_handle, self.mask)

    def shutdown(self):
        VectorCanApi.xlDeactivateChannel(self.port_handle, self.mask)
        VectorCanApi.xlClosePort(self.port_handle)
        VectorCanApi.xlCloseDriver()

    def reset(self):
        """
        resets the channel
        """
        VectorCanApi.xlDeactivateChannel(self.port_handle, self.mask)
        VectorCanApi.xlActivateChannel(
            self.port_handle, self.mask, v_def.XL_BusTypes.XL_BUS_TYPE_CAN.value, 0
        )

    @staticmethod
    def _detect_available_configs():
        configs = []
        channel_configs = get_channel_configs()
        LOG.info("Found %d channels", len(channel_configs))
        for channel_config in channel_configs:
            if not channel_config.channelBusCapabilities & v_def.XL_BusCapabilities.XL_BUS_ACTIVE_CAP_CAN.value:
                continue
            LOG.info(
                "Channel index %d: %s",
                channel_config.channelIndex,
                channel_config.name.decode("ascii"),
            )
            configs.append(
                {
                    "interface": "vector",
                    "app_name": None,
                    "channel": channel_config.channelIndex,
                    "supports_fd": bool(
                        channel_config.channelBusCapabilities
                        & v_def.XL_ChannelCapabilities.XL_CHANNEL_FLAG_CANFD_ISO_SUPPORT.value
                    ),
                }
            )
        return configs

    @staticmethod
    def popup_vector_hw_configuration(wait_for_finish: int = 0) -> None:
        """Open vector hardware configuration window.

        :param int wait_for_finish:
            Time to wait for user input in milliseconds.
        """
        VectorCanApi.xlPopupHwConfig(c_char_p(), c_uint(wait_for_finish))

    @staticmethod
    def get_application_config(
            app_name: str, app_channel: int, bus_type: v_def.XL_BusTypes
    ) -> typing.Tuple[v_def.XL_HardwareType, int, int]:
        """Retrieve information for an application in Vector Hardware Configuration.

        :param app_name:
            The name of the application.
        :param app_channel:
            The channel of the application.
        :param bus_type:
            The bus type Enum e.g. `XL_BusTypes.XL_BUS_TYPE_CAN`
        :return:
            Returns a tuple of the hardware type, the hardware index and the
            hardware channel.
        :raises VectorError:
            Raises a VectorError when the application name does not exist in
            Vector Hardware Configuration.
        """
        hw_type = c_uint()
        hw_index = c_uint()
        hw_channel = c_uint()

        VectorCanApi.xlGetApplConfig(
            app_name.encode(),
            app_channel,
            hw_type,
            hw_index,
            hw_channel,
            bus_type.value,
        )
        return v_def.XL_HardwareType(hw_type.value), hw_index.value, hw_channel.value

    @staticmethod
    def set_application_config(
            app_name: str,
            app_channel: int,
            hw_type: v_def.XL_HardwareType,
            hw_index: int,
            hw_channel: int,
            bus_type: v_def.XL_BusTypes,
    ) -> None:
        """Modify the application settings in Vector Hardware Configuration.

        :param app_name:
            The name of the application. Creates a new application if it does
            not exist yet.
        :param app_channel:
            The channel of the application.
        :param hw_type:
            The hardware type of the interface.
            E.g XL_HardwareType.XL_HWTYPE_VIRTUAL
        :param hw_index:
            The index of the interface if multiple interface with the same
            hardware type are present.
        :param hw_channel:
            The channel index of the interface.
        :param bus_type:
            The bus type of the interfaces, which should be
            XL_BusTypes.XL_BUS_TYPE_CAN for most cases.
        """
        VectorCanApi.xlSetApplConfig(
            app_name.encode(),
            app_channel,
            hw_type.value,
            hw_index,
            hw_channel,
            bus_type.value,
        )

    def set_timer_rate(self, timer_rate_ms: int) -> None:
        """Set the cyclic event rate of the port.

        Once set, the port will generate a cyclic event with the tag XL_EventTags.XL_TIMER.
        This timer can_comm be used to keep an application alive. See XL Driver Library Description
        for more information

        :param timer_rate_ms:
            The timer rate in ms. The minimal timer rate is 1ms, a value of 0 deactivates
            the timer events.
        """
        timer_rate_10us = timer_rate_ms * 100
        VectorCanApi.xlSetTimerRate(self.port_handle, timer_rate_10us)


def get_channel_configs() -> typing.List[v_class.XLchannelConfig]:
    """
    Method invoked to get the channel configuration
    :returns channel numbers and name: if present else empty list.
    """
    driver_config = v_class.XLdriverConfig()
    try:
        VectorCanApi.xlOpenDriver()
        VectorCanApi.xlGetDriverConfig(driver_config)
        VectorCanApi.xlCloseDriver()
    except VectorError as err:
        LOG.error("Exception occurred while getting channel config %s", err)
        return list()  # returns an empty list
    return [driver_config.channel[i] for i in range(driver_config.channelCount)]
