"""
    created on oct 2020

    :file: can_tp_frames.py
    :platform: Linux, Windows
    :synopsis:
        Implementation of ISO15765-2 can_comm-tp Frames (Single, First, Consecutive, Flow Control).

    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""

from typing import NamedTuple
from .. import CanMessage


# pylint:disable=line-too-long, too-many-instance-attributes
class CanFrame:
    """
    Converts a CAN Message into SingleFrame / FirstFrame / ConsecutiveFrame / FlowControl
    """
    __slots__ = 'type', 'length', 'data', 'block_size', 'st_min', 'st_min_sec', 'seq_num', 'name', \
                'flow_status', 'rx_dl', 'escape_sequence', 'can_dl', 'msg_data', 'data_len'

    class Type(NamedTuple):
        """
        Possible Frame types w.r.t ISO15767-2 protocol.
        """
        SINGLE_FRAME = 0
        FIRST_FRAME = 1
        CONSECUTIVE_FRAME = 2
        FLOW_CONTROL = 3

    class FlowStatus(NamedTuple):
        """
        Possible Flow Status w.r.t ISO15765-2 protocol.
        """
        ContinueToSend = 0
        Wait = 1
        Overflow = 2

    def __init__(self, msg: CanMessage = None, start_of_data: int = 0):

        """
        :param msg: can_comm message frame
        :param start_of_data: bit indicating the start of data
        """

        self.type = None
        self.name = None
        self.length = None
        self.data = None
        self.block_size = None
        self.st_min = None
        self.st_min_sec = None
        self.seq_num = None
        self.flow_status = None
        self.escape_sequence = False

        if msg is None:
            return

        if len(msg.data) < start_of_data:
            raise ValueError("Received message is missing data according to prefix size")

        self.can_dl = len(msg.data)
        self.rx_dl = max(8, self.can_dl)
        self.msg_data = msg.data[start_of_data:]
        self.data_len = len(self.msg_data)
        self._frame_type()
        if self.type == self.Type.SINGLE_FRAME:
            self.name = "SINGLE_FRAME"
            self._single_frame(start_of_data)

        elif self.type == self.Type.FIRST_FRAME:
            self.name = "FIRST_FRAME"
            self._first_frame(start_of_data)

        elif self.type == self.Type.CONSECUTIVE_FRAME:
            self.name = "CONSECUTIVE_FRAME"
            self.seq_num = int(self.msg_data[0]) & 0xF
            self.data = self.msg_data[1:]  # No need to check size as this will return empty data if overflow.

        elif self.type == self.Type.FLOW_CONTROL:
            self.name = "FLOW_CONTROL"
            self._flow_control(start_of_data)

    def __str__(self):
        return "Frame type: {}\n, length: {}\n, data: {}\n, frame_length:{}\n, actual_data:{}\n".format(self.name,
                                                                                                        self.length,
                                                                                                        self.data,
                                                                                                        self.data_len,
                                                                                                        self.msg_data)

    def _frame_type(self):
        """
        This method is invoked internally. Validates frame type
        :raises: value error if frame type is invalid
        :return: None
        """
        # Guarantee at least presence of byte #1
        if self.data_len > 0:
            type_ = (self.msg_data[0] >> 4) & 0xF
            if type_ > 3:
                raise ValueError('Received message with unknown frame type %d' % type_)
            self.type = int(type_)
        else:
            raise ValueError('Empty CAN frame')

    def _single_frame(self, start_of_data):
        """
        This method is invoked internally if frame type is SINGLE_FRAME and validates it.
        :param start_of_data: bit from which the data starts. (depends on the address mode)
        :return: None
        """
        length_placeholder = int(self.msg_data[0]) & 0xF
        if length_placeholder != 0:
            self.length = length_placeholder
            if self.length > self.data_len - 1:
                raise ValueError(
                    "Received Single Frame with length of %d while there is room for %d bytes "
                    "of data with this configuration" % (self.length, self.data_len - 1)
                )
            self.data = self.msg_data[1:][:self.length]

        else:  # Escape seuqence
            if self.data_len < 2:
                raise ValueError(
                    'Single frame with escape sequence must be at least %d bytes long with this configuration' %
                    (2 + start_of_data)
                )

            self.escape_sequence = True
            self.length = int(self.msg_data[1])
            if self.length == 0:
                raise ValueError("Received Single Frame with length of 0 bytes")
            if self.length > self.data_len - 2:
                raise ValueError(
                    "Received Single Frame with length of %d while there is room for %d bytes of data with this "
                    "configuration" % (self.length, self.data_len - 2)
                )
            self.data = self.msg_data[2:][:self.length]

    def _first_frame(self, start_of_data):
        """
        This method is invoked internally if frame type is FIRST_FRAME and validates it.
        :param start_of_data: bit from which the data starts. (depends on the address mode)
        :return: None
        """
        if self.data_len < 2:
            raise ValueError(
                'First frame without escape sequence must be at least %d bytes long with this configuration' %
                (2 + start_of_data)
            )

        length_placeholder = ((int(self.msg_data[0]) & 0xF) << 8) | int(self.msg_data[1])
        if length_placeholder != 0:  # Frame is maximum 4095 bytes
            self.length = length_placeholder
            self.data = self.msg_data[2:][:min(self.length, self.data_len - 2)]

        else:  # Frame is larger than 4095 bytes
            if self.data_len < 6:
                raise ValueError(
                    'First frame with escape sequence must be at least %d bytes long with this configuration' %
                    (6 + start_of_data)
                )
            self.escape_sequence = True
            self.length = (self.msg_data[2] << 24) | (self.msg_data[3] << 16) | (self.msg_data[4] << 8) | \
                          (self.msg_data[5] << 0)
            self.data = self.msg_data[6:][:min(self.length, self.data_len - 6)]

    def _flow_control(self, start_of_data):
        """
        This method is invoked internally if frame type is FLOW_CONTROL and validates it.
        :param start_of_data: bit from which the data starts. (depends on the address mode)
        :return: None
        """
        if self.data_len < 3:
            raise ValueError(
                'Flow Control frame must be at least %d bytes with the actual configuration' % (3 + start_of_data))

        self.flow_status = int(self.msg_data[0]) & 0xF
        if self.flow_status >= 3:
            raise ValueError('Unknown flow status')

        self.block_size = int(self.msg_data[1])
        st_min_temp = int(self.msg_data[2])

        if 0 <= st_min_temp <= 0x7F:
            self.st_min_sec = st_min_temp / 1000
        elif 0xf1 <= st_min_temp <= 0xF9:
            self.st_min_sec = (st_min_temp - 0xF0) / 10000

        if self.st_min_sec is None:
            raise ValueError('Invalid StMin received in Flow Control')
        self.st_min = st_min_temp

    @classmethod
    def craft_flow_control_data(cls, flow_status, block_size, st_min):
        """
        Assembles the flow-control message
        :param flow_status: Indicates the status of receiver. Refer ISO15765-2 for further details
        :param block_size: Number of consecutive-frames that can_comm be sent per block. Refer ISO15765-2 for further details
        :param st_min: time between 2 consecutive frames. Refer ISO15765-2 for further details.
        :return: Flow control message
        """
        return bytearray([(0x30 | flow_status & 0xF), block_size & 0xFF, st_min & 0xFF])
