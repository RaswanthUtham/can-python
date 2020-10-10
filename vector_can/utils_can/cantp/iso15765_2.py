import time
import queue
import logging
import binascii
from typing import NamedTuple
from copy import copy
from . import Address, TargetAddressType
from . import l4c_error
from ..can_bus import CanBus
from ..utils import CAN_FD_DLC
from .. import CanMessage


class PDU:
    """
    Converts a CAN Message into a meaningful PDU such as SingleFrame, FirstFrame, ConsecutiveFrame, FlowControl
    """
    __slots__ = 'type', 'length', 'data', 'block_size', 'st_min', 'st_min_sec', 'seq_num', 'name', \
                'flow_status', 'rx_dl', 'escape_sequence', 'can_dl', 'msg_data', 'data_len'

    class Type(NamedTuple):
        SINGLE_FRAME = 0
        FIRST_FRAME = 1
        CONSECUTIVE_FRAME = 2
        FLOW_CONTROL = 3

    class FlowStatus(NamedTuple):
        ContinueToSend = 0
        Wait = 1
        Overflow = 2

    def __init__(self, msg: CanMessage = None, start_of_data: int = 0):

        """
        :param msg: can message frame
        :param start_of_data:
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
        # Guarantee at least presence of byte #1
        if self.data_len > 0:
            type_ = (self.msg_data[0] >> 4) & 0xF
            if type_ > 3:
                raise ValueError('Received message with unknown frame type %d' % type_)
            self.type = int(type_)
        else:
            raise ValueError('Empty CAN frame')

    def _single_frame(self, start_of_data):
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
                    'Single frame with escape sequence must be at least %d bytes long with this configuration' % (
                            2 + start_of_data)
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
        if self.data_len < 2:
            raise ValueError(
                'First frame without escape sequence must be at least %d bytes long with this configuration' % (
                        2 + start_of_data))

        length_placeholder = ((int(self.msg_data[0]) & 0xF) << 8) | int(self.msg_data[1])
        if length_placeholder != 0:  # Frame is maximum 4095 bytes
            self.length = length_placeholder
            self.data = self.msg_data[2:][:min(self.length, self.data_len - 2)]

        else:  # Frame is larger than 4095 bytes
            if self.data_len < 6:
                raise ValueError(
                    'First frame with escape sequence must be at least %d bytes long with this configuration' % (
                            6 + start_of_data))
            self.escape_sequence = True
            self.length = (self.msg_data[2] << 24) | (self.msg_data[3] << 16) | (self.msg_data[4] << 8) | (
                    self.msg_data[5] << 0)
            self.data = self.msg_data[6:][:min(self.length, self.data_len - 6)]

    def _flow_control(self, start_of_data):
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
        else:
            self.st_min = st_min_temp

    @classmethod
    def craft_flow_control_data(cls, flow_status, block_size, st_min):
        return bytearray([(0x30 | flow_status & 0xF), block_size & 0xFF, st_min & 0xFF])


class Params:
    __slots__ = ('st_min', 'block_size', 'squash_st_min_requirement', 'rx_flow_control_timeout',
                 'rx_consecutive_frame_timeout', 'tx_padding', 'wft_max', 'tx_data_length', 'tx_data_min_length',
                 'max_frame_size', 'can_fd'
                 )

    def __init__(self):
        self.st_min = 0
        self.block_size = 8
        self.squash_st_min_requirement = False
        self.rx_flow_control_timeout = 1000
        self.rx_consecutive_frame_timeout = 1000
        self.tx_padding = None
        self.wft_max = 0
        self.tx_data_length = 8
        self.tx_data_min_length = None
        self.max_frame_size = 4095
        self.can_fd = False

    def set(self, key, val, validate=True):
        param_alias = {
            'll_data_length': 'tx_data_length'  # For backward compatibility
        }
        if key in param_alias:
            key = param_alias[key]
        setattr(self, key, val)
        if validate:
            self.validate()

    def validate(self):
        if not isinstance(self.rx_flow_control_timeout, int):
            raise ValueError('rx_flow_control_timeout must be an integer')

        if self.rx_flow_control_timeout < 0:
            raise ValueError('rx_flow_control_timeout must be positive integer')

        if not isinstance(self.rx_consecutive_frame_timeout, int):
            raise ValueError('rx_consecutive_frame_timeout must be an integer')

        if self.rx_consecutive_frame_timeout < 0:
            raise ValueError('rx_consecutive_frame_timeout must be positive integer')

        if self.tx_padding is not None:
            if not isinstance(self.tx_padding, int):
                raise ValueError('tx_padding must be an integer')

            if self.tx_padding < 0 or self.tx_padding > 0xFF:
                raise ValueError('tx_padding must be an integer between 0x00 and 0xFF')

        if not isinstance(self.st_min, int):
            raise ValueError('st_min must be an integer')

        if self.st_min < 0 or self.st_min > 0xFF:
            raise ValueError('st_min must be positive integer between 0x00 and 0xFF')

        if not isinstance(self.block_size, int):
            raise ValueError('block_size must be an integer')

        if self.block_size < 0 or self.block_size > 0xFF:
            raise ValueError('block_size must be and integer between 0x00 and 0xFF')

        if not isinstance(self.squash_st_min_requirement, bool):
            raise ValueError('squash_st_min_requirement must be a boolean value')

        if not isinstance(self.wft_max, int):
            raise ValueError('wft_max must be an integer')

        if self.wft_max < 0:
            raise ValueError('wft_max must be and integer equal or greater than 0')

        if not isinstance(self.tx_data_length, int):
            raise ValueError('tx_data_length must be an integer')

        if self.tx_data_length not in [8, 12, 16, 20, 24, 32, 48, 64]:
            raise ValueError('tx_data_length must be one of these value : 8, 12, 16, 20, 24, 32, 48, 64 ')

        if self.tx_data_min_length is not None:
            if not isinstance(self.tx_data_min_length, int):
                raise ValueError('tx_data_min_length must be an integer')

            if self.tx_data_min_length not in [1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64]:
                raise ValueError(
                    'tx_data_min_length must be one of these value : '
                    '1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64 ')

            if self.tx_data_min_length > self.tx_data_length:
                raise ValueError('tx_data_min_length cannot be greater than tx_data_length')

        if not isinstance(self.max_frame_size, int):
            raise ValueError('max_frame_size must be an integer')

        if self.max_frame_size < 0:
            raise ValueError('max_frame_size must be a positive integer')

        if not isinstance(self.can_fd, bool):
            raise ValueError('can_fd must be a boolean value')


class Timer:
    def __init__(self, timeout):
        self.set_timeout(timeout)
        self.start_time = None

    def set_timeout(self, timeout):
        self.timeout = timeout

    def start(self, timeout=None):
        if timeout is not None:
            self.set_timeout(timeout)
        self.start_time = time.time()

    def stop(self):
        self.start_time = None

    def elapsed(self):
        if self.start_time is not None:
            return time.time() - self.start_time
        else:
            return 0

    def is_timed_out(self):
        if self.is_stopped():
            return False
        else:
            return self.elapsed() > self.timeout or self.timeout == 0

    def is_stopped(self):
        return self.start_time is None


class RxState(NamedTuple):
    IDLE = 0
    WAIT_CF = 1


class TxState(NamedTuple):
    IDLE = 0
    WAIT_FC = 1
    TRANSMIT_CF = 2


class TransportLayer:
    """
    The IsoTP transport layer implementation

    """

    LOGGER_NAME = 'isotp'

    def __init__(self,
                 rxfn: callable,
                 txfn: callable,
                 address: Address = None,
                 error_handler: callable = None,
                 params: dict = None):
        """
        :param rxfn: Function to be called by the transport layer to read the CAN layer.
                Must return a :class:`isotp.CanMessage<isotp.CanMessage>` or None if no message has been received.

        :param txfn: Function to be called by the transport layer to send a message on the CAN layer.
                    This function should receive a :class:`CanMessage<CanMessage>`

        :param address: The address information of CAN messages. Includes the addressing mode, txid/rxid, source/target
                        address and address extension. See :class:`Address<Address>` for more details.

        :param error_handler: A function to be called when an error has been detected.

        :param params: List of parameters for the transport layer
        """
        self.params = Params()
        self.logger = logging.getLogger(self.LOGGER_NAME)

        if params is not None:
            for k, v in params.items():
                self.params.set(k, v, validate=False)
        self.params.validate()

        self.remote_block_size = None  # Block size received in Flow Control message

        self.rxfn = rxfn  # Function to call to receive a CAN message
        self.txfn = txfn  # Function to call to transmit a CAN message

        self.address = None
        self.set_address(address)

        self.tx_queue = queue.Queue()  # Layer Input queue for IsoTP frame
        self.rx_queue = queue.Queue()  # Layer Output queue for IsoTP frame

        self.rx_state = RxState.IDLE  # State of the reception FSM
        self.tx_state = TxState.IDLE  # State of the transmission FSM

        self.rx_block_counter = 0
        self.last_seq_num = None  # Consecutive frame Sequence number of previous message
        self.rx_frame_length = 0  # Length of IsoTP frame being received at the moment
        self.tx_frame_length = 0  # Length of the data that we are sending
        self.last_flow_control_frame = None  # When a FlowControl is received. Put here
        self.tx_block_counter = 0  # Keeps track of how many block we've sent
        self.tx_seq_num = 0  # Keeps track of the actual sequence number while sending
        self.wft_counter = 0  # Keeps track of how many wait frame we've received

        # Flag indicating that we need to transmit a flow control message. Set by Rx Process, Cleared by Tx Process
        self.pending_flow_control_tx = False
        self.pending_flow_control_status = None
        self.rx_buffer = bytearray()
        self.tx_buffer = bytearray()

        self.timer_tx_st_min = Timer(timeout=0)
        self.timer_rx_fc = Timer(timeout=float(self.params.rx_flow_control_timeout) / 1000)
        self.timer_rx_cf = Timer(timeout=float(self.params.rx_consecutive_frame_timeout) / 1000)

        self.error_handler = error_handler
        self.actual_rx_dl = None

    def set_address(self, address: Address):
        """
        Sets the layer :class:`Address<Address>`. Can be set after initialization if needed.
        """
        if not isinstance(address, Address):
            raise ValueError('address must be a valid Address instance')

        self.address = address

        if self.address.tx_id is not None and (
                0x7F4 < self.address.tx_id < 0x7F6 or 0x7FA < self.address.tx_id < 0x7FB):
            self.logger.warning(
                'Used txid overlaps the range of ID reserved by ISO-15765 (0x7F4-0x7F6 and 0x7FA-0x7FB)')

        if self.address.rx_id is not None and (
                0x7F4 < self.address.rx_id < 0x7F6 or 0x7FA < self.address.rx_id < 0x7FB):
            self.logger.warning(
                'Used rxid overlaps the range of ID reserved by ISO-15765 (0x7F4-0x7F6 and 0x7FA-0x7FB)')

    def empty_rx_buffer(self):
        self.rx_buffer = bytearray()

    def empty_tx_buffer(self):
        self.tx_buffer = bytearray()

    def empty_buffers(self):
        self.empty_rx_buffer()
        self.empty_tx_buffer()

    def send(self, data, target_address_type=TargetAddressType.Physical):
        """
        Enqueue an IsoTP frame to be sent over CAN network

        :param data: The data to be sent
        :type data: bytearray

        :param target_address_type: Optional parameter that can be Physical (0) for 1-to-1 communication or Functional
                                        (1) for 1-to-n. See :class:`isotp.TargetAddressType<isotp.TargetAddressType>`
        :type target_address_type: int

        :raises ValueError: Input parameter is not a bytearray or not convertible to bytearray
        :raises RuntimeError: Transmit queue is full
        """
        if not isinstance(data, bytearray):
            try:
                data = bytearray(data)
            except Exception:
                raise ValueError('data must be a bytearray')

        if self.tx_queue.full():
            raise RuntimeError('Transmit queue is full')

        if target_address_type == TargetAddressType.Functional:
            length_bytes = 1 if self.params.tx_data_length == 8 else 2
            max_len = self.params.tx_data_length - length_bytes - len(self.address.tx_payload_prefix)

            if len(data) > max_len:
                raise ValueError('Cannot send multipacket frame with Functional TargetAddressType')

        self.tx_queue.put(
            {'data': data, 'target_address_type': target_address_type})  # frame is always an IsoTPFrame here

    def receive(self):
        """
        Dequeue an IsoTP frame from the reception queue if available.

        :return: The next available IsoTP frame
        :rtype: bytearray or None
        """
        if not self.rx_queue.empty():
            return self.rx_queue.get()

    def is_available(self):
        """
        Returns ``True`` if an IsoTP frame is awaiting in the reception ``queue``. ``False`` otherwise
        """
        return not self.rx_queue.empty()

    def is_transmitting(self):
        """
        Returns ``True`` if an IsoTP frame is being transmitted. ``False`` otherwise
        """
        return not self.tx_queue.empty() or self.tx_state != TxState.IDLE

    def process(self):
        """
        Function to be called periodically, as fast as possible.
        This function is non-blocking.
        """
        msg = True
        while msg is not None:
            msg = self.rxfn()
            if msg is not None:
                self.logger.debug(
                    "Receiving : <%03X> (%d)\t %s" % (msg.arbitration_id, len(msg.data), binascii.hexlify(msg.data)))
                self.process_rx(msg)

        msg = True
        while msg is not None:
            msg = self.process_tx()
            if msg is not None:
                self.logger.debug(
                    "Sending : <%03X> (%d)\t %s" % (msg.arbitration_id, len(msg.data), binascii.hexlify(msg.data)))
                self.txfn(msg)

    def process_rx(self, msg):

        if not self.address.is_for_me(msg):
            return

            # Decoding of message into PDU
        try:
            pdu = PDU(msg, start_of_data=self.address.rx_prefix_size)
        except Exception as e:
            self.trigger_error(l4c_error.InvalidCanDataError("Received invalid CAN frame. %s" % (str(e))))
            self.stop_receiving()
            return

        # Check timeout first
        if self.timer_rx_cf.is_timed_out():
            self.trigger_error(l4c_error.ConsecutiveFrameTimeoutError("Reception of CONSECUTIVE_FRAME timed out."))
            self.stop_receiving()

        # Process Flow Control message
        if pdu.type == PDU.Type.FLOW_CONTROL:
            self.last_flow_control_frame = pdu  # Given to process_tx method. Queue of 1 message depth

            if self.rx_state == RxState.WAIT_CF:
                if pdu.flow_status == PDU.FlowStatus.Wait or pdu.flow_status == PDU.FlowStatus.ContinueToSend:
                    self.start_rx_cf_timer()
            return  # Nothing else to be done with FlowControl. Return and wait for next message

        if pdu.type == PDU.Type.SINGLE_FRAME:
            if pdu.can_dl > 8 and pdu.escape_sequence is False:
                self.trigger_error(l4c_error.MissingEscapeSequenceError(
                    'For SingleFrames conveyed on a CAN message with data length (CAN_DL) > 8, '
                    'length should be encoded on byte #1 and byte #0 should be 0x00'))
                return

        # Process the state machine
        if self.rx_state == RxState.IDLE:
            self.rx_frame_length = 0
            self.timer_rx_cf.stop()
            if pdu.type == PDU.Type.SINGLE_FRAME:
                if pdu.data is not None:
                    self.rx_queue.put(copy(pdu.data))

            elif pdu.type == PDU.Type.FIRST_FRAME:
                self.start_reception_after_first_frame_if_valid(pdu)
            elif pdu.type == PDU.Type.CONSECUTIVE_FRAME:
                self.trigger_error(l4c_error.UnexpectedConsecutiveFrameError(
                    'Received a ConsecutiveFrame while reception was idle. Ignoring'))

        elif self.rx_state == RxState.WAIT_CF:
            if pdu.type == PDU.Type.SINGLE_FRAME:
                if pdu.data is not None:
                    self.rx_queue.put(copy(pdu.data))
                    self.rx_state = RxState.IDLE
                    self.trigger_error(l4c_error.ReceptionInterruptedWithSingleFrameError(
                        'Reception of IsoTP frame interrupted with a new SingleFrame'))

            elif pdu.type == PDU.Type.FIRST_FRAME:
                self.start_reception_after_first_frame_if_valid(pdu)
                self.trigger_error(l4c_error.ReceptionInterruptedWithFirstFrameError(
                    'Reception of IsoTP frame interrupted with a new FirstFrame'))

            elif pdu.type == PDU.Type.CONSECUTIVE_FRAME:
                expected_seq_num = (self.last_seq_num + 1) & 0xF
                if expected_seq_num == pdu.seq_num:
                    bytes_to_receive = (self.rx_frame_length - len(self.rx_buffer))
                    if pdu.rx_dl != self.actual_rx_dl and pdu.rx_dl < bytes_to_receive:
                        self.trigger_error(l4c_error.ChangingInvalidRXDLError(
                            "Received a ConsecutiveFrame with RX_DL=%d while expected RX_DL=%d. Ignoring frame" % (
                                pdu.rx_dl, self.actual_rx_dl)))
                        return

                    self.start_rx_cf_timer()  # Received a CF message. Restart counter. Timeout handled above.
                    self.last_seq_num = pdu.seq_num
                    self.append_rx_data(pdu.data[:bytes_to_receive])  # Python handle overflow
                    if len(self.rx_buffer) >= self.rx_frame_length:
                        self.rx_queue.put(copy(self.rx_buffer))  # Data complete
                        self.stop_receiving()  # Go back to IDLE. Reset all variables and timers.
                    else:
                        self.rx_block_counter += 1
                        if self.params.block_size > 0 and (self.rx_block_counter % self.params.block_size) == 0:
                            self.request_tx_flowcontrol()  # Sets a flag to 1. process_tx will send it for use.
                            self.timer_rx_cf.stop()  # Deactivate that timer while we wait for flow control
                else:
                    self.stop_receiving()
                    self.trigger_error(l4c_error.WrongSequenceNumberError(
                        'Received a ConsecutiveFrame with wrong SequenceNumber. Expecting 0x%X, Received 0x%X' % (
                            expected_seq_num, pdu.seq_num)))

    def process_tx(self):
        output_msg = None  # Value outputed.  If None, no subsequent call to process_tx will be done.

        # Sends flow control if process_rx requested it
        if self.pending_flow_control_tx:
            self.pending_flow_control_tx = False
            return self.make_flow_control(flow_status=self.pending_flow_control_status)  # No need to wait.

        # Handle flow control reception
        flow_control_frame = self.last_flow_control_frame  # Reads the last message received and clears it.
        self.last_flow_control_frame = None

        if flow_control_frame is not None:
            if flow_control_frame.flow_status == PDU.FlowStatus.Overflow:  # Needs to stop sending.
                self.stop_sending()
                self.trigger_error(l4c_error.OverFlowError(
                    'Received a FlowControl PDU indicating an Overflow. Stopping transmission.'))
                return

            if self.tx_state == TxState.IDLE:
                self.trigger_error(l4c_error.UnexpectedFlowControlError(
                    'Received a FlowControl message while transmission was Idle. Ignoring'))
            else:
                if flow_control_frame.flow_status == PDU.FlowStatus.Wait:
                    if self.params.wft_max == 0:
                        self.trigger_error(l4c_error.UnsuportedWaitFrameError(
                            'Received a FlowControl requesting to wait, but wft_max is set to 0'))
                    elif self.wft_counter >= self.params.wft_max:
                        self.trigger_error(l4c_error.MaximumWaitFrameReachedError(
                            'Received %d wait frame which is the maximum set in params.wft_max' % self.wft_counter))
                        self.stop_sending()
                    else:
                        self.wft_counter += 1
                        if self.tx_state in [TxState.WAIT_FC, TxState.TRANSMIT_CF]:
                            self.tx_state = TxState.WAIT_FC
                            self.start_rx_fc_timer()

                elif flow_control_frame.flow_status == PDU.FlowStatus.ContinueToSend and \
                        not self.timer_rx_fc.is_timed_out():
                    self.wft_counter = 0
                    self.timer_rx_fc.stop()
                    self.timer_tx_st_min.set_timeout(flow_control_frame.st_min_sec)
                    self.remote_block_size = flow_control_frame.block_size

                    if self.tx_state == TxState.WAIT_FC:
                        self.tx_block_counter = 0
                        self.timer_tx_st_min.start()
                    elif self.tx_state == TxState.TRANSMIT_CF:
                        pass

                    self.tx_state = TxState.TRANSMIT_CF

        # ======= Timeouts ======
        if self.timer_rx_fc.is_timed_out():
            self.trigger_error(
                l4c_error.FlowControlTimeoutError('Reception of FlowControl timed out. Stopping transmission'))
            self.stop_sending()

        # ======= FSM ======

        # Check this first as we may have another isotp frame to send and we need to handle it right away without
        # waiting for next "process()" call
        if self.tx_state != TxState.IDLE and len(self.tx_buffer) == 0:
            self.stop_sending()

        if self.tx_state == TxState.IDLE:
            read_tx_queue = True  # Read until we get non-empty frame to send
            while read_tx_queue:
                read_tx_queue = False
                if not self.tx_queue.empty():
                    popped_object = self.tx_queue.get()
                    if len(popped_object['data']) == 0:
                        read_tx_queue = True  # Read another frame from tx_queue
                    else:
                        self.tx_buffer = bytearray(popped_object['data'])
                        size_on_first_byte = True if len(self.tx_buffer) <= 7 else False
                        size_offset = 1 if size_on_first_byte else 2

                        # Single frame
                        if len(self.tx_buffer) <= self.params.tx_data_length - size_offset - len(
                                self.address.tx_payload_prefix):
                            if size_on_first_byte:
                                msg_data = self.address.tx_payload_prefix + bytearray(
                                    [0x0 | len(self.tx_buffer)]) + self.tx_buffer
                            else:
                                msg_data = self.address.tx_payload_prefix + bytearray(
                                    [0x0, len(self.tx_buffer)]) + self.tx_buffer
                            arbitration_id = self.address.get_tx_arbitration_id(popped_object['target_address_type'])
                            output_msg = self.make_tx_msg(arbitration_id, msg_data)

                        # Multi frame - First Frame
                        else:
                            self.tx_frame_length = len(self.tx_buffer)
                            encode_length_on_2_first_bytes = True if self.tx_frame_length <= 0xFFF else False
                            if encode_length_on_2_first_bytes:
                                data_length = self.params.tx_data_length - 2 - len(self.address.tx_payload_prefix)
                                msg_data = self.address.tx_payload_prefix + bytearray(
                                    [0x10 | ((self.tx_frame_length >> 8) & 0xF),
                                     self.tx_frame_length & 0xFF]) + self.tx_buffer[:data_length]
                            else:
                                data_length = self.params.tx_data_length - 6 - len(self.address.tx_payload_prefix)
                                msg_data = self.address.tx_payload_prefix + bytearray(
                                    [0x10, 0x00, (self.tx_frame_length >> 24) & 0xFF,
                                     (self.tx_frame_length >> 16) & 0xFF, (self.tx_frame_length >> 8) & 0xFF,
                                     (self.tx_frame_length >> 0) & 0xFF]) + self.tx_buffer[:data_length]
                            arbitration_id = self.address.get_tx_arbitration_id()
                            output_msg = self.make_tx_msg(arbitration_id, msg_data)
                            self.tx_buffer = self.tx_buffer[data_length:]
                            self.tx_state = TxState.WAIT_FC
                            self.tx_seq_num = 1
                            self.start_rx_fc_timer()

        elif self.tx_state == TxState.WAIT_FC:
            pass  # Nothing to do. Flow control will make the FSM switch state by calling init_tx_consecutive_frame

        elif self.tx_state == TxState.TRANSMIT_CF:
            if self.timer_tx_st_min.is_timed_out() or self.params.squash_st_min_requirement:
                data_length = self.params.tx_data_length - 1 - len(self.address.tx_payload_prefix)
                msg_data = self.address.tx_payload_prefix + bytearray([0x20 | self.tx_seq_num]) + self.tx_buffer[
                                                                                                  :data_length]
                arbitration_id = self.address.get_tx_arbitration_id()
                output_msg = self.make_tx_msg(arbitration_id, msg_data)
                self.tx_buffer = self.tx_buffer[data_length:]
                self.tx_seq_num = (self.tx_seq_num + 1) & 0xF
                self.timer_tx_st_min.start()
                self.tx_block_counter += 1
            if len(self.tx_buffer) == 0:
                self.stop_sending()

            elif self.remote_block_size != 0 and self.tx_block_counter >= self.remote_block_size:
                self.tx_state = TxState.WAIT_FC
                self.start_rx_fc_timer()

        return output_msg

    def pad_message_data(self, msg_data):
        must_pad = False
        padding_byte = 0xCC if self.params.tx_padding is None else self.params.tx_padding

        if self.params.tx_data_length == 8:
            if self.params.tx_data_min_length is None:
                if self.params.tx_padding is not None:  # ISO-15765:2016 - 10.4.2.1
                    must_pad = True
                    target_length = 8
                else:  # ISO-15765:2016 - 10.4.2.2
                    pass

            else:  # issue #27
                must_pad = True
                target_length = self.params.tx_data_min_length

        elif self.params.tx_data_length > 8:
            if self.params.tx_data_min_length is None:  # ISO-15765:2016 - 10.4.2.3
                target_length = self.get_nearest_can_fd_size(len(msg_data))
                must_pad = True
            else:  # Issue #27
                must_pad = True
                target_length = max(self.params.tx_data_min_length, self.get_nearest_can_fd_size(len(msg_data)))

        if must_pad and len(msg_data) < target_length:
            msg_data.extend(bytearray([padding_byte & 0xFF] * (target_length - len(msg_data))))

    def start_rx_fc_timer(self):
        self.timer_rx_fc = Timer(timeout=float(self.params.rx_flow_control_timeout) / 1000)
        self.timer_rx_fc.start()

    def start_rx_cf_timer(self):
        self.timer_rx_cf = Timer(timeout=float(self.params.rx_consecutive_frame_timeout) / 1000)
        self.timer_rx_cf.start()

    def append_rx_data(self, data):
        self.rx_buffer.extend(data)

    def request_tx_flowcontrol(self, status=PDU.FlowStatus.ContinueToSend):
        self.pending_flow_control_tx = True
        self.pending_flow_control_status = status

    def stop_sending_flow_control(self):
        self.pending_flow_control_tx = False
        self.last_flow_control_frame = None

    def make_tx_msg(self, arbitration_id, data):
        self.pad_message_data(data)
        return CanMessage(arbitration_id=arbitration_id, dlc=self.get_dlc(data, validate_tx=True), data=data,
                          is_extended_id=self.address.is_29bits, is_fd=self.params.can_fd)

    def get_dlc(self, data, validate_tx=False):
        fd_len = len(data)
        if validate_tx:
            if self.params.tx_data_length == 8:
                if fd_len < 2 or fd_len > 8:
                    raise ValueError("Impossible DLC size for payload of %d bytes with tx_data_length of %d" % (
                        len(data), self.params.tx_data_length))

        if fd_len <= 8:
            return fd_len
        for dlc, nof_bytes in enumerate(CAN_FD_DLC):
            if nof_bytes >= fd_len:
                return dlc
        raise ValueError("Impossible DLC size for payload of %d bytes with tx_data_length of %d" %
                         (fd_len, self.params.tx_data_length))

    @staticmethod
    def get_nearest_can_fd_size(size):
        if size <= 8:
            return size
        for nof_bytes in CAN_FD_DLC:
            if nof_bytes >= size:
                return nof_bytes
        raise ValueError("Impossible data size for CAN FD : %d " % size)

    def make_flow_control(self, flow_status=PDU.FlowStatus.ContinueToSend, block_size=None, st_min=None):
        if block_size is None:
            block_size = self.params.block_size

        if st_min is None:
            st_min = self.params.st_min
        data = PDU.craft_flow_control_data(flow_status, block_size, st_min)

        return self.make_tx_msg(self.address.get_tx_arbitration_id(), self.address.tx_payload_prefix + data)

    def request_wait_flow_control(self):
        self.must_wait_for_flow_control = True

    def stop_sending(self):
        self.empty_tx_buffer()
        self.tx_state = TxState.IDLE
        self.tx_frame_length = 0
        self.timer_rx_fc.stop()
        self.timer_tx_st_min.stop()
        self.remote_block_size = None
        self.tx_block_counter = 0
        self.tx_seq_num = 0
        self.wft_counter = 0

    def stop_receiving(self):
        self.actual_rx_dl = None
        self.rx_state = RxState.IDLE
        self.empty_rx_buffer()
        self.stop_sending_flow_control()
        self.timer_rx_cf.stop()

    # Init the reception of a multi-pdu frame.
    def start_reception_after_first_frame_if_valid(self, pdu):
        self.empty_rx_buffer()
        if pdu.rx_dl not in [8, 12, 16, 20, 24, 32, 48, 64]:
            self.trigger_error(l4c_error.InvalidCanFdFirstFrameRXDL(
                "Received a FirstFrame with a RX_DL value of %d which is invalid according to ISO-15765-2" % (
                    pdu.rx_dl)))
            self.stop_receiving()
            return

        self.actual_rx_dl = pdu.rx_dl

        if pdu.length > self.params.max_frame_size:
            self.trigger_error(l4c_error.FrameTooLongError(
                "Received a Frist Frame with a length of %d bytes, but params.max_frame_size is set to %d bytes. "
                "Ignoring" % (pdu.length, self.params.max_frame_size)))
            self.request_tx_flowcontrol(PDU.FlowStatus.Overflow)
            self.rx_state = RxState.IDLE
        else:
            self.rx_state = RxState.WAIT_CF
            self.rx_frame_length = pdu.length
            self.append_rx_data(pdu.data)
            self.request_tx_flowcontrol(PDU.FlowStatus.ContinueToSend)

        self.start_rx_cf_timer()
        self.last_seq_num = 0
        self.rx_block_counter = 0

    def trigger_error(self, error):
        if self.error_handler is not None:
            if hasattr(self.error_handler, '__call__') and isinstance(error, l4c_error.IsoTpError):
                self.error_handler(error)
            else:
                self.logger.warning('Given error handler is not a callable object.')

        self.logger.warning(str(error))

    # Clears everything within the layer.
    def reset(self):
        """
        Reset the layer: Empty all buffers, set the internal state machines to Idle
        """
        while not self.tx_queue.empty():
            self.tx_queue.get()

        while not self.rx_queue.empty():
            self.rx_queue.get()

        self.stop_sending()
        self.stop_receiving()

    # Gives a time to pass to time.sleep() based on the state of the FSM. Avoid using too much CPU
    def sleep_time(self):
        """
        Returns a value in seconds that can be passed to ``time.sleep()`` when the stack is processed in a different t
        hread.

        The value will change according to the internal state machine state, sleeping longer while idle and shorter
        when active.
        """
        timings = {
            (RxState.IDLE, TxState.IDLE): 0.05,
            (RxState.IDLE, TxState.WAIT_FC): 0.01,
        }

        key = (self.rx_state, self.tx_state)
        if key in timings:
            return timings[key]
        else:
            return 0.001


class CanStack(TransportLayer):
    """
    All parameters except the ``bus`` parameter will be given to the :class: "TransportLayer" initializer

    :param bus: A can bus object implementing ``recv`` and ``send``
    :type bus: BusABC

    :param address: The address information of CAN messages. Includes the addressing mode, txid/rxid,
                    source/target address and address extension.
    :type address: Address

    :param error_handler: A function to be called when an error has been detected.
    :type error_handler: Callable

    :param params: List of parameters for the transport layer
    :type params: dict

    """

    def tx_canbus(self, msg):
        self.bus.send(CanMessage(arbitration_id=msg.arbitration_id, data=msg.data, is_extended_id=msg.is_extended_id,
                                 is_fd=msg.is_fd))

    def rx_canbus(self):
        msg = self.bus.receive(0)
        if msg is not None:
            return CanMessage(arbitration_id=msg.arbitration_id, data=msg.data, is_extended_id=msg.is_extended_id,
                              is_fd=msg.is_fd)

    def __init__(self, bus, *args, **kwargs):

        self.bus = self.set_bus(bus)
        TransportLayer.__init__(self, rxfn=self.rx_canbus, txfn=self.tx_canbus, *args, **kwargs)

    @staticmethod
    def set_bus(bus: CanBus):
        if not isinstance(bus, CanBus):
            raise ValueError('bus must be a python-can BusABC object')
        return bus
