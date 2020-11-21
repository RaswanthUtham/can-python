"""
    created on oct 2020

    :file: can_message.py
    :platform: Linux, Windows
    :synopsis:
        Implementation of CAN message.
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""

from typing import Optional, Union
from copy import deepcopy
from math import isinf, isnan

from . import TypeCheck


# pylint:disable=c0301
class CanMessage:
    # pylint:disable=R0902, R0913, R0914, R1705
    """
    The :class:`~CanMessage` object is used to represent CAN messages for
    sending, receiving and other purposes like converting between different
    logging formats.

    Messages can_comm use extended identifiers, be remote or error frames, contain
    data and may be associated to a channel.

    Messages are always compared by identity and never by value, because that
    may introduce unexpected behaviour.

    :func:`~copy.copy`/:func:`~copy.deepcopy` is supported as well.
    """

    __slots__ = ("timestamp", "arbitration_id", "is_extended_id", "is_remote_frame", "is_error_frame", "channel", "dlc",
                 "data", "is_fd", "is_rx", "bitrate_switch", "error_state_indicator", "__weakref__",)

    def __init__(self, timestamp: float = 0.0, arbitration_id: int = 0, is_extended_id: bool = True,
                 is_remote_frame: bool = False, is_error_frame: bool = False, dlc: Optional[int] = None,
                 channel: Optional[TypeCheck.Channel] = None, data: Optional[TypeCheck.CanData] = None,
                 is_fd: bool = False, is_rx: bool = True, bitrate_switch: bool = False, check: bool = False,
                 error_state_indicator: bool = False,
                 ):
        """
        To create a message object, simply provide any of the below attributes
        together with additional parameters as keyword arguments to the constructor.

        :param check: By default, the constructor of this class does not strictly check the input.
                      Thus, the caller must prevent the creation of invalid messages or
                      set this parameter to `True`, to raise an Error on invalid inputs.
                      Possible problems include the `dlc` field not matching the length of `data`
                      or creating a message with both `is_remote_frame` and `is_error_frame` set to `True`.

        :raises ValueError: iff `check` is set to `True` and one or more arguments were invalid
        """
        self.timestamp = timestamp
        self.arbitration_id = arbitration_id
        self.is_extended_id = is_extended_id
        self.is_remote_frame = is_remote_frame
        self.is_error_frame = is_error_frame
        self.channel = channel
        self.is_fd = is_fd
        self.is_rx = is_rx
        self.bitrate_switch = bitrate_switch
        self.error_state_indicator = error_state_indicator

        if data is None or is_remote_frame:
            self.data = bytearray()
        elif isinstance(data, bytearray):
            self.data = data
        else:
            try:
                self.data = bytearray(data)
            except TypeError:
                err = "Couldn't create message from {} ({})".format(data, type(data))
                raise TypeError(err)

        if dlc is None:
            self.dlc = len(self.data)
        else:
            self.dlc = dlc

        if check:
            self._validate_message()

    def __eq__(self, other: "CanMessage") -> bool:
        return self.compare_with(other)

    def __str__(self) -> str:

        extended = "TRUE" if self.is_extended_id else "FALSE"
        direction = "Rx" if self.is_rx else "Tx"
        error = "TRUE" if self.is_error_frame else "FALSE"
        remote = "TRUE" if self.is_remote_frame else "FALSE"
        can_fd = "TRUE" if self.is_fd else "FALSE"
        bit_rate_switch = "TRUE" if self.bitrate_switch else "FALSE"
        error_indicator = "TRUE" if self.error_state_indicator else "FALSE"

        data_strings = []
        if self.data is not None:
            for index in range(0, min(self.dlc, len(self.data))):
                data_strings.append("{0:02x}".format(self.data[index]))
        if data_strings:  # if not empty
            data_strings = " ".join(data_strings).ljust(24, " ")
        else:
            data_strings = " " * 24

        if (self.data is not None) and (self.data.isalnum()):
            raw_data = "'{}'".format(self.data.decode("utf-8", "replace"))
        else:
            raw_data = "None"

        if self.channel is not None:
            try:
                channel = "Channel: {}".format(self.channel)
            except UnicodeEncodeError:
                pass
        else:
            channel = "None"

        if self.is_extended_id:
            msg_id = "{0:08x}".format(self.arbitration_id)
        else:
            msg_id = "{0:04x}".format(self.arbitration_id)

        timestamp = "{0:>15.6f}".format(self.timestamp)
        dlc = "{0:2d}".format(self.dlc)

        message_details = "TIME_STAMP: {}\nMESSAGE_DETAILS:\n\tMSG_ID: {}\tDLC: {}\tTX/RX: {}\tRAW_DATA: {}" \
                          "\nFRAME_DETAILS:\n\tIS_EXTENDED: {}\tIS_ERROR_FRAME: {}\tIS_REMOTE_FRAME: {}\n\t" \
                          "IS_CAN_FD: {}\tBIT_RATE_SWITCH: {}\tERROR_INDICATOR: {}\nDATA: {}\n" \
                          "\nCHANNEL: {}".format(timestamp, msg_id, dlc, direction, raw_data, extended, error, remote,
                                                 can_fd, bit_rate_switch, error_indicator, data_strings, channel)
        return message_details.strip()

    def __len__(self) -> int:
        # return the dlc such that it also works on remote frames
        return self.dlc

    def __bool__(self) -> bool:
        return True

    def __format__(self, format_spec: Optional[str]) -> str:
        if not format_spec:
            return self.__str__()
        else:
            raise ValueError("non empty format_specs are not supported")

    def __bytes__(self) -> bytes:
        return bytes(self.data)

    def __copy__(self) -> "CanMessage":
        new = CanMessage(
            timestamp=self.timestamp,
            arbitration_id=self.arbitration_id,
            is_extended_id=self.is_extended_id,
            is_remote_frame=self.is_remote_frame,
            is_error_frame=self.is_error_frame,
            channel=self.channel,
            dlc=self.dlc,
            data=self.data,
            is_fd=self.is_fd,
            is_rx=self.is_rx,
            bitrate_switch=self.bitrate_switch,
            error_state_indicator=self.error_state_indicator,
        )
        return new

    def __deepcopy__(self, memo: dict) -> "CanMessage":
        new = CanMessage(
            timestamp=self.timestamp,
            arbitration_id=self.arbitration_id,
            is_extended_id=self.is_extended_id,
            is_remote_frame=self.is_remote_frame,
            is_error_frame=self.is_error_frame,
            channel=deepcopy(self.channel, memo),
            dlc=self.dlc,
            data=deepcopy(self.data, memo),
            is_fd=self.is_fd,
            is_rx=self.is_rx,
            bitrate_switch=self.bitrate_switch,
            error_state_indicator=self.error_state_indicator,
        )
        return new

    def compare_with(
            self,
            other: "CanMessage",
            timestamp_delta: Optional[Union[float, int]] = 1.0e-6,
            check_direction: bool = True,
    ) -> bool:
        """
        Compares a given message with this one.

        :param other: the message to compare with

        :param timestamp_delta: the maximum difference at which two timestamps are
                                still considered equal or None to not compare timestamps

        :param check_direction: do we compare the messages' directions (Tx/Rx)

        :return: True iff the given message equals this one
        """
        # see https://github.com/hardbyte/python-can/pull/413 for a discussion
        # on why a delta of 1.0e-6 was chosen
        return (self is other  # check for identity first and finish fast
                or  # then check for equality by value
                (
                        (
                                timestamp_delta is None
                                or abs(self.timestamp - other.timestamp) <= timestamp_delta
                        )
                        and (self.is_rx == other.is_rx or not check_direction)
                        and self.arbitration_id == other.arbitration_id
                        and self.is_extended_id == other.is_extended_id
                        and self.dlc == other.dlc
                        and self.data == other.data
                        and self.is_remote_frame == other.is_remote_frame
                        and self.is_error_frame == other.is_error_frame
                        and self.channel == other.channel
                        and self.is_fd == other.is_fd
                        and self.bitrate_switch == other.bitrate_switch
                        and self.error_state_indicator == other.error_state_indicator
                )
                )

    def _validate_message(self):
        """Checks if the message parameters are valid.
        Assumes that the types are already correct.

        :raises ValueError: iff one or more attributes are invalid
        """
        self._timestamp_check()
        self._frame_check()
        self._id_check()
        self._dlc_check()
        self._can_fd_check()

    def _timestamp_check(self):
        if self.timestamp < 0.0:
            raise ValueError("the timestamp may not be negative")
        if isinf(self.timestamp):
            raise ValueError("the timestamp may not be infinite")
        if isnan(self.timestamp):
            raise ValueError("the timestamp may not be NaN")

    def _frame_check(self):
        if self.is_remote_frame and self.is_error_frame:
            raise ValueError(
                "a message cannot be a remote and an error frame at the sane time"
            )
        if self.is_remote_frame:
            if self.data:
                raise ValueError("remote frames may not carry any data")

    def _id_check(self):
        if self.arbitration_id < 0:
            raise ValueError("arbitration IDs may not be negative")

        if self.is_extended_id:
            if self.arbitration_id >= 0x20000000:
                raise ValueError("Extended arbitration IDs must be less than 2^29")
        elif self.arbitration_id >= 0x800:
            raise ValueError("Normal arbitration IDs must be less than 2^11")

    def _dlc_check(self):
        if self.dlc < 0:
            raise ValueError("DLC may not be negative")
        if self.is_fd:
            if self.dlc > 64:
                raise ValueError(
                    "DLC was {} but it should be <= 64 for CAN FD frames".format(
                        self.dlc
                    )
                )
        elif self.dlc > 8:
            raise ValueError(
                "DLC was {} but it should be <= 8 for normal CAN frames".format(
                    self.dlc
                )
            )
        if not self.is_remote_frame:
            if self.dlc != len(self.data):
                raise ValueError(
                    "the DLC and the length of the data must match up for non remote frames"
                )

    def _can_fd_check(self):
        if not self.is_fd:
            if self.bitrate_switch:
                raise ValueError("bitrate switch is only allowed for CAN FD frames")
            if self.error_state_indicator:
                raise ValueError(
                    "error state indicator is only allowed for CAN FD frames"
                )
