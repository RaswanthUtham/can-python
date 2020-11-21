"""
    created on oct 2020

    :file: exceptions.py
    :platform: Linux, Windows
    :synopsis:
        Implementation of CAN-TP Layer.
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""
import queue
import logging
import binascii
from typing import NamedTuple
from copy import copy
from .. import CAN_FD_DLC
from .. import CanMessage
from ...utils_common import Timer
from .can_tp_frames import CanFrame
from . import Address
from . import l4c_error


# pylint:disable=line-too-long
class Params:
    # pylint:disable=too-many-instance-attributes,
    """
    Class containing the configurable params for CAN-TP.
    """
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
        """
        setter method
        :param key: param name
        :param val: param value
        :param validate: if true, the params will be validated
        :return: None
        """
        setattr(self, key, val)
        if validate:
            self.validate()

    def validate(self):
        # pylint:disable=too-many-branches
        """
        Validates the CAN-TP params.
        :return: None
        :raises ValueError: if any of the params is invalid
        """
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


class RxState(NamedTuple):
    """
    CAN-TP rx state
    """
    IDLE = 0
    WAIT_CF = 1


class TxState(NamedTuple):
    """
    CAN-TP tx state
    """
    IDLE = 0
    WAIT_FC = 1
    TRANSMIT_CF = 2


class TransportLayer:
    # pylint:disable=too-many-instance-attributes, too-many-arguments, too-many-public-methods
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
        self._params = Params()
        self.logger = logging.getLogger(self.LOGGER_NAME)

        if params is not None:
            for key, value in params.items():
                self._params.set(key, value, validate=False)
        self._params.validate()

        self._remote_block_size = None  # Block size received in Flow Control message

        self._rxfn = rxfn  # Function to call to receive a CAN message
        self._txfn = txfn  # Function to call to transmit a CAN message

        self._address = None
        self._set_address(address)

        self._tx_queue = queue.Queue()  # Layer Input queue for IsoTP frame
        self._rx_queue = queue.Queue()  # Layer Output queue for IsoTP frame

        self._rx_state = RxState.IDLE  # State of the reception FSM
        self._tx_state = TxState.IDLE  # State of the transmission FSM

        self._rx_block_counter = 0
        self._last_seq_num = None  # Consecutive frame Sequence number of previous message
        self._rx_frame_length = 0  # Length of IsoTP frame being received at the moment
        self._tx_frame_length = 0  # Length of the data that we are sending
        self._last_flow_control_frame = None  # When a FlowControl is received. Put here
        self._tx_block_counter = 0  # Keeps track of how many block we've sent
        self._tx_seq_num = 0  # Keeps track of the actual sequence number while sending
        self._wft_counter = 0  # Keeps track of how many wait frame we've received

        # Flag indicating that we need to transmit a flow control message. Set by Rx Process, Cleared by Tx Process
        self._pending_flow_control_tx = False
        self._flow_control_status = None
        self._rx_buffer = bytearray()
        self._tx_buffer = bytearray()

        self._timer_tx_st_min = Timer(timeout=0)  # pylint:disable=not-callable
        self._timer_rx_fc = Timer(timeout=self._params.rx_flow_control_timeout / 1000)  # pylint:disable=not-callable
        self._timer_rx_cf = Timer(timeout=self._params.rx_consecutive_frame_timeout / 1000)  # pylint:disable=E1102

        self._error_handler = error_handler
        self._actual_rx_dl = None

    def _set_address(self, address: Address):
        """
        Sets the layer :class:`Address<Address>`. Can be set after initialization if needed.
        """
        if not isinstance(address, Address):
            raise ValueError('address must be a valid Address instance')

        self._address = address

        if self._address.tx_id is not None and (
                0x7F4 < self._address.tx_id < 0x7F6 or 0x7FA < self._address.tx_id < 0x7FB):
            self.logger.warning(
                'Used txid overlaps the range of ID reserved by ISO-15765 (0x7F4-0x7F6 and 0x7FA-0x7FB)')

        if self._address.rx_id is not None and (
                0x7F4 < self._address.rx_id < 0x7F6 or 0x7FA < self._address.rx_id < 0x7FB):
            self.logger.warning(
                'Used rxid overlaps the range of ID reserved by ISO-15765 (0x7F4-0x7F6 and 0x7FA-0x7FB)')

    def empty_rx_buffer(self):
        """
        Empty reception buffer
        :return: None
        """
        self._rx_buffer = bytearray()

    def empty_tx_buffer(self):
        """
        Empty transmission buffer
        :return: None
        """
        self._tx_buffer = bytearray()

    def empty_buffers(self):
        """
        Empty reception and transmission buffer
        :return: None
        """
        self.empty_rx_buffer()
        self.empty_tx_buffer()

    def send(self, data, target_address_type=Address.Type.Physical):
        """
        Enqueue an IsoTP frame to be sent over CAN network

        :param data: The data to be sent
        :type data: bytearray

        :param target_address_type: Optional parameter that can_comm be Physical (0) for 1-to-1 communication or Functional
                                        (1) for 1-to-n. See :class:`isotp.Address.Type<isotp.Address.Type>`
        :type target_address_type: int

        :raises ValueError: Input parameter is not a bytearray or not convertible to bytearray
        :raises RuntimeError: Transmit queue is full
        """
        if not isinstance(data, bytearray):
            try:
                data = bytearray(data)
            except Exception:
                raise ValueError('data must be a bytearray')

        if self._tx_queue.full():
            raise RuntimeError('Transmit queue is full')

        if target_address_type == Address.Type.Functional:
            length_bytes = 1 if self._params.tx_data_length == 8 else 2
            max_len = self._params.tx_data_length - length_bytes - len(self._address.tx_payload_prefix)

            if len(data) > max_len:
                raise ValueError('Cannot send multipacket frame with Functional Address.Type')

        self._tx_queue.put(
            {'data': data, 'target_address_type': target_address_type})  # frame is always an IsoTPFrame here

    def receive(self):
        """
        Dequeue an IsoTP frame from the reception queue if available.

        :return: The next available IsoTP frame
        :rtype: bytearray or None
        """
        if not self._rx_queue.empty():
            return self._rx_queue.get()
        return None

    def is_available(self):
        """
        Returns ``True`` if an IsoTP frame is awaiting in the reception ``queue``. ``False`` otherwise
        """
        return not self._rx_queue.empty()

    def is_transmitting(self):
        """
        Returns ``True`` if an IsoTP frame is being transmitted. ``False`` otherwise
        """
        return not self._tx_queue.empty() or self._tx_state != TxState.IDLE

    def process(self):
        """
        Function to be called periodically, as fast as possible.
        This function is non-blocking.
        """
        msg = True
        while msg is not None:
            msg = self._rxfn()
            if msg is not None:
                self.logger.debug(
                    "Receiving : <%03X> (%d)\t %s", msg.arbitration_id, len(msg.data), binascii.hexlify(msg.data))
                self._process_rx(msg)

        msg = True
        while msg is not None:
            msg = self._process_tx()
            if msg is not None:
                self.logger.debug(
                    "Sending : <%03X> (%d)\t %s", msg.arbitration_id, len(msg.data), binascii.hexlify(msg.data))
                self._txfn(msg)

    def _process_rx(self, msg):
        # pylint:disable=too-many-branches, too-many-statements
        """
        This is an internal invoked from self.process
        :param msg: message that is received from layer 2
        :return: None
        """

        if not self._address.is_for_me(msg):
            return

            # Decoding of message into PDU
        try:
            pdu = CanFrame(msg, start_of_data=self._address.rx_prefix_size)
        except Exception as exp:  # pylint:disable=broad-except
            self.error_callback(l4c_error.InvalidCanDataError("Received invalid CAN frame. %s" % (str(exp))))
            self.stop_receiving()
            return

        # Check timeout first
        if self._timer_rx_cf.is_timed_out():
            self.error_callback(l4c_error.ConsecutiveFrameTimeoutError("Reception of CONSECUTIVE_FRAME timed out."))
            self.stop_receiving()

        # Process Flow Control message
        if pdu.type == CanFrame.Type.FLOW_CONTROL:
            self._last_flow_control_frame = pdu  # Given to process_tx method. Queue of 1 message depth

            if self._rx_state == RxState.WAIT_CF:
                if pdu.flow_status == CanFrame.FlowStatus.Wait or pdu.flow_status == CanFrame.FlowStatus.ContinueToSend:
                    self.start_rx_cf_timer()
            return  # Nothing else to be done with FlowControl. Return and wait for next message

        if pdu.type == CanFrame.Type.SINGLE_FRAME:
            if pdu.can_dl > 8 and pdu.escape_sequence is False:
                self.error_callback(l4c_error.MissingEscapeSequenceError(
                    'For SingleFrames conveyed on a CAN message with data length (CAN_DL) > 8, '
                    'length should be encoded on byte #1 and byte #0 should be 0x00'))
                return

        # Process the state machine
        if self._rx_state == RxState.IDLE:
            self._rx_frame_length = 0
            self._timer_rx_cf.stop()
            if pdu.type == CanFrame.Type.SINGLE_FRAME:
                if pdu.data is not None:
                    self._rx_queue.put(copy(pdu.data))

            elif pdu.type == CanFrame.Type.FIRST_FRAME:
                self.start_reception_after_first_frame_if_valid(pdu)
            elif pdu.type == CanFrame.Type.CONSECUTIVE_FRAME:
                self.error_callback(l4c_error.UnexpectedConsecutiveFrameError(
                    'Received a ConsecutiveFrame while reception was idle. Ignoring'))

        elif self._rx_state == RxState.WAIT_CF:
            if pdu.type == CanFrame.Type.SINGLE_FRAME:
                if pdu.data is not None:
                    self._rx_queue.put(copy(pdu.data))
                    self._rx_state = RxState.IDLE
                    self.error_callback(l4c_error.ReceptionInterruptedWithSingleFrameError(
                        'Reception of IsoTP frame interrupted with a new SingleFrame'))

            elif pdu.type == CanFrame.Type.FIRST_FRAME:
                self.start_reception_after_first_frame_if_valid(pdu)
                self.error_callback(l4c_error.ReceptionInterruptedWithFirstFrameError(
                    'Reception of IsoTP frame interrupted with a new FirstFrame'))

            elif pdu.type == CanFrame.Type.CONSECUTIVE_FRAME:
                expected_seq_num = (self._last_seq_num + 1) & 0xF
                if expected_seq_num == pdu.seq_num:
                    bytes_to_receive = (self._rx_frame_length - len(self._rx_buffer))
                    if pdu.rx_dl != self._actual_rx_dl and pdu.rx_dl < bytes_to_receive:
                        self.error_callback(l4c_error.ChangingInvalidRXDLError(
                            "Received a ConsecutiveFrame with RX_DL=%d while expected RX_DL=%d. Ignoring frame" % (
                                pdu.rx_dl, self._actual_rx_dl)))
                        return

                    self.start_rx_cf_timer()  # Received a CF message. Restart counter. Timeout handled above.
                    self._last_seq_num = pdu.seq_num
                    self.append_rx_data(pdu.data[:bytes_to_receive])  # Python handle overflow
                    if len(self._rx_buffer) >= self._rx_frame_length:
                        self._rx_queue.put(copy(self._rx_buffer))  # Data complete
                        self.stop_receiving()  # Go back to IDLE. Reset all variables and timers.
                    else:
                        self._rx_block_counter += 1
                        if self._params.block_size > 0 and (self._rx_block_counter % self._params.block_size) == 0:
                            self.request_tx_flowcontrol()  # Sets a flag to 1. process_tx will send it for use.
                            self._timer_rx_cf.stop()  # Deactivate that timer while we wait for flow control
                else:
                    self.stop_receiving()
                    self.error_callback(l4c_error.WrongSequenceNumberError(
                        'Received a ConsecutiveFrame with wrong SequenceNumber. Expecting 0x%X, Received 0x%X' % (
                            expected_seq_num, pdu.seq_num)))

    def _process_tx(self):  # pylint:disable=inconsistent-return-statements
        # pylint:disable=too-many-branches, too-many-statements
        """
        This method is invoked internally by self.process
        :return: None
        """
        output_msg = None  # Value outputed.  If None, no subsequent call to process_tx will be done.

        # Sends flow control if process_rx requested it
        if self._pending_flow_control_tx:
            self._pending_flow_control_tx = False
            return self.make_flow_control(flow_status=self._flow_control_status)  # No need to wait.

        # Handle flow control reception
        flow_control_frame = self._last_flow_control_frame  # Reads the last message received and clears it.
        self._last_flow_control_frame = None

        if flow_control_frame is not None:
            if flow_control_frame.flow_status == CanFrame.FlowStatus.Overflow:  # Needs to stop sending.
                self.stop_sending()
                self.error_callback(l4c_error.OverFlowError(
                    'Received a FlowControl PDU indicating an Overflow. Stopping transmission.'))
                return

            if self._tx_state == TxState.IDLE:
                self.error_callback(l4c_error.UnexpectedFlowControlError(
                    'Received a FlowControl message while transmission was Idle. Ignoring'))
            else:
                if flow_control_frame.flow_status == CanFrame.FlowStatus.Wait:
                    if self._params.wft_max == 0:
                        self.error_callback(l4c_error.UnsuportedWaitFrameError(
                            'Received a FlowControl requesting to wait, but wft_max is set to 0'))
                    elif self._wft_counter >= self._params.wft_max:
                        self.error_callback(l4c_error.MaximumWaitFrameReachedError(
                            'Received %d wait frame which is the maximum set in params.wft_max' % self._wft_counter))
                        self.stop_sending()
                    else:
                        self._wft_counter += 1
                        if self._tx_state in [TxState.WAIT_FC, TxState.TRANSMIT_CF]:
                            self._tx_state = TxState.WAIT_FC
                            self.start_rx_fc_timer()

                elif flow_control_frame.flow_status == CanFrame.FlowStatus.ContinueToSend and not \
                        self._timer_rx_fc.is_timed_out():
                    self._wft_counter = 0
                    self._timer_rx_fc.stop()
                    self._timer_tx_st_min.set_timeout(flow_control_frame.st_min_sec)
                    self._remote_block_size = flow_control_frame.block_size

                    if self._tx_state == TxState.WAIT_FC:
                        self._tx_block_counter = 0
                        self._timer_tx_st_min.start()
                    elif self._tx_state == TxState.TRANSMIT_CF:
                        pass

                    self._tx_state = TxState.TRANSMIT_CF

        # ======= Timeouts ======
        if self._timer_rx_fc.is_timed_out():
            self.error_callback(
                l4c_error.FlowControlTimeoutError('Reception of FlowControl timed out. Stopping transmission'))
            self.stop_sending()

        # Check this first as we may have another isotp frame to send and we need to handle it right away without
        # waiting for next "process()" call
        if self._tx_state != TxState.IDLE and not self._tx_buffer:
            self.stop_sending()

        if self._tx_state == TxState.IDLE:
            while not self._tx_queue.empty():
                popped_object = self._tx_queue.get()
                if popped_object['data']:
                    self._tx_buffer = bytearray(popped_object['data'])
                    size_on_first_byte = len(self._tx_buffer) <= 7
                    size_offset = 1 if size_on_first_byte else 2

                    # Single frame
                    if len(self._tx_buffer) <= self._params.tx_data_length - size_offset - len(
                            self._address.tx_payload_prefix):
                        if size_on_first_byte:
                            msg_data = self._address.tx_payload_prefix + bytearray(
                                [0x0 | len(self._tx_buffer)]) + self._tx_buffer
                        else:
                            msg_data = self._address.tx_payload_prefix + bytearray(
                                [0x0, len(self._tx_buffer)]) + self._tx_buffer
                        arbitration_id = self._address.get_tx_arbitration_id(popped_object['target_address_type'])
                        output_msg = self.make_tx_msg(arbitration_id, msg_data)

                    # Multi frame - First Frame
                    else:
                        self._tx_frame_length = len(self._tx_buffer)
                        encode_length_on_2_first_bytes = self._tx_frame_length <= 0xFFF
                        if encode_length_on_2_first_bytes:
                            data_length = self._params.tx_data_length - 2 - len(self._address.tx_payload_prefix)
                            msg_data = self._address.tx_payload_prefix + bytearray(
                                [0x10 | ((self._tx_frame_length >> 8) & 0xF),
                                 self._tx_frame_length & 0xFF]) + self._tx_buffer[:data_length]
                        else:
                            data_length = self._params.tx_data_length - 6 - len(self._address.tx_payload_prefix)
                            msg_data = self._address.tx_payload_prefix + bytearray(
                                [0x10, 0x00, (self._tx_frame_length >> 24) & 0xFF,
                                 (self._tx_frame_length >> 16) & 0xFF, (self._tx_frame_length >> 8) & 0xFF,
                                 (self._tx_frame_length >> 0) & 0xFF]) + self._tx_buffer[:data_length]
                        arbitration_id = self._address.get_tx_arbitration_id()
                        output_msg = self.make_tx_msg(arbitration_id, msg_data)
                        self._tx_buffer = self._tx_buffer[data_length:]
                        self._tx_state = TxState.WAIT_FC
                        self._tx_seq_num = 1
                        self.start_rx_fc_timer()

        elif self._tx_state == TxState.WAIT_FC:
            pass  # Nothing to do. Flow control will make the FSM switch state by calling init_tx_consecutive_frame

        elif self._tx_state == TxState.TRANSMIT_CF:
            if self._timer_tx_st_min.is_timed_out() or self._params.squash_st_min_requirement:
                data_length = self._params.tx_data_length - 1 - len(self._address.tx_payload_prefix)
                msg_data = self._address.tx_payload_prefix + \
                           bytearray([0x20 | self._tx_seq_num]) + self._tx_buffer[:data_length]
                arbitration_id = self._address.get_tx_arbitration_id()
                output_msg = self.make_tx_msg(arbitration_id, msg_data)
                self._tx_buffer = self._tx_buffer[data_length:]
                self._tx_seq_num = (self._tx_seq_num + 1) & 0xF
                self._timer_tx_st_min.start()
                self._tx_block_counter += 1
            if not self._tx_buffer:
                self.stop_sending()

            elif self._remote_block_size != 0 and self._tx_block_counter >= self._remote_block_size:
                self._tx_state = TxState.WAIT_FC
                self.start_rx_fc_timer()

        return output_msg

    def pad_message_data(self, msg_data):
        """
        This method is invoked for padding the can_comm message
        :param msg_data: can_comm payload
        :return: None
        """
        must_pad = False
        padding_byte = 0xCC if self._params.tx_padding is None else self._params.tx_padding

        if self._params.tx_data_length == 8:
            if self._params.tx_data_min_length is None:
                if self._params.tx_padding is not None:  # ISO-15765:2016 - 10.4.2.1
                    must_pad = True
                    target_length = 8
                else:  # ISO-15765:2016 - 10.4.2.2
                    pass

            else:  # issue #27
                must_pad = True
                target_length = self._params.tx_data_min_length

        elif self._params.tx_data_length > 8:
            if self._params.tx_data_min_length is None:  # ISO-15765:2016 - 10.4.2.3
                target_length = self.get_can_fd_size(len(msg_data))
                must_pad = True
            else:  # Issue #27
                must_pad = True
                target_length = max(self._params.tx_data_min_length, self.get_can_fd_size(len(msg_data)))

        if must_pad and len(msg_data) < target_length:
            msg_data.extend(bytearray([padding_byte & 0xFF] * (target_length - len(msg_data))))

        # print("msg_data in must_pad", msg_data, " length ", hex(len(msg_data)))
        return msg_data

    def start_rx_fc_timer(self):
        """
        Method is invoked to start flow control timer
        :return: None
        """
        # pylint:disable=not-callable
        self._timer_rx_fc = Timer(timeout=float(self._params.rx_flow_control_timeout) / 1000)
        self._timer_rx_fc.start()

    def start_rx_cf_timer(self):
        """
        Method is invoked to start consecutive frame timer
        :return:
        """
        # pylint:disable=not-callable
        self._timer_rx_cf = Timer(timeout=float(self._params.rx_consecutive_frame_timeout) / 1000)
        self._timer_rx_cf.start()

    def append_rx_data(self, data):
        """
        Method to append received data from layer 2
        :param data: can_comm payload
        :return: None
        """
        self._rx_buffer.extend(data)

    def request_tx_flowcontrol(self, status=CanFrame.FlowStatus.ContinueToSend):
        """
        Method is invoked to send the flow control message while reception
        :param status: flow-control status
        :return: None
        """
        self._pending_flow_control_tx = True
        self._flow_control_status = status

    def stop_sending_flow_control(self):
        """
        Method is invoked to stop sending flow control
        :return: None
        """
        self._pending_flow_control_tx = False
        self._last_flow_control_frame = None

    def make_tx_msg(self, arbitration_id, data):
        """
        Method is invoked to assemble the message w.r.t layer 2
        :param arbitration_id: can_comm msg id
        :param data: can_comm payload
        :return: can_comm message
        """
        # print("msg_data in make_tx_msg b4", data, " length ", hex(len(data)))
        data = self.pad_message_data(data)
        # print("msg_data in make_tx_msg a4", data, " length ", hex(len(data)))
        return CanMessage(arbitration_id=arbitration_id, dlc=self.get_dlc(data, validate_tx=True), data=data,
                          is_extended_id=self._address.is_29bits, is_fd=self._params.can_fd)

    def get_dlc(self, data, validate_tx=False):
        """
        Method is invoked to get the dlc w.r.t can_comm payload length (layer 2)
        :param data: can_comm payload
        :param validate_tx: Boolean. if true: data is validated
        :returns: dlc
        :raises ValueError: if dlc is invalid.
        """
        fd_len = len(data)
        if validate_tx:
            if self._params.tx_data_length == 8:
                if fd_len < 2 or fd_len > 8:
                    raise ValueError("Impossible DLC size for payload of %d bytes with tx_data_length of %d" % (
                        len(data), self._params.tx_data_length))

        if fd_len <= 8:
            return fd_len
        for dlc, nof_bytes in enumerate(CAN_FD_DLC):
            if nof_bytes >= fd_len:
                return dlc
        raise ValueError("Impossible DLC size for payload of %d bytes with tx_data_length of %d" %
                         (fd_len, self._params.tx_data_length))

    @staticmethod
    def get_can_fd_size(size):
        """
        Method to get DLC of CAN message
        :param size: size of message in bytes
        :return: dlc
        """
        if size <= 8:
            return size
        for nof_bytes in CAN_FD_DLC:
            if nof_bytes >= size:
                return nof_bytes
        raise ValueError("Impossible data size for CAN FD : %d " % size)

    def make_flow_control(self, flow_status=CanFrame.FlowStatus.ContinueToSend, block_size=None, st_min=None):
        """
        Method to make the flow control frame
        :param flow_status: flow status
        :param block_size: block size
        :param st_min: seperation time
        :return: flow control frame
        """
        if block_size is None:
            block_size = self._params.block_size

        if st_min is None:
            st_min = self._params.st_min
        data = CanFrame.craft_flow_control_data(flow_status, block_size, st_min)

        return self.make_tx_msg(self._address.get_tx_arbitration_id(), self._address.tx_payload_prefix + data)

    def stop_sending(self):
        """
        Method is invoked when we need to stop sending
        """
        self.empty_tx_buffer()
        self._tx_state = TxState.IDLE
        self._tx_frame_length = 0
        self._timer_rx_fc.stop()
        self._timer_tx_st_min.stop()
        self._remote_block_size = None
        self._tx_block_counter = 0
        self._tx_seq_num = 0
        self._wft_counter = 0

    def stop_receiving(self):
        """
        Method is invoked when we need to stop receiving
        """
        self._actual_rx_dl = None
        self._rx_state = RxState.IDLE
        self.empty_rx_buffer()
        self.stop_sending_flow_control()
        self._timer_rx_cf.stop()

    # Init the reception of a multi-pdu frame.
    def start_reception_after_first_frame_if_valid(self, pdu):
        """
        validate first frame and start receiving consecutive frame after sending flow control
        :param pdu: first frame
        :return: None
        """
        self.empty_rx_buffer()
        if pdu.rx_dl not in [8, 12, 16, 20, 24, 32, 48, 64]:
            self.error_callback(l4c_error.InvalidCanFdFirstFrameRXDL(
                "Received a FirstFrame with a RX_DL value of %d which is invalid according to ISO-15765-2" %
                pdu.rx_dl))
            self.stop_receiving()
            return

        self._actual_rx_dl = pdu.rx_dl

        if pdu.length > self._params.max_frame_size:
            self.error_callback(l4c_error.FrameTooLongError(
                "Received a Frist Frame with a length of %d bytes, but params.max_frame_size is set to %d bytes. "
                "Ignoring" % (pdu.length, self._params.max_frame_size)))
            self.request_tx_flowcontrol(CanFrame.FlowStatus.Overflow)
            self._rx_state = RxState.IDLE
        else:
            self._rx_state = RxState.WAIT_CF
            self._rx_frame_length = pdu.length
            self.append_rx_data(pdu.data)
            self.request_tx_flowcontrol(CanFrame.FlowStatus.ContinueToSend)

        self.start_rx_cf_timer()
        self._last_seq_num = 0
        self._rx_block_counter = 0

    def error_callback(self, error):
        """
        error handler
        :param error: error message
        :return:
        """
        if self._error_handler is not None:
            if hasattr(self._error_handler, '__call__') and isinstance(error, l4c_error.IsoTpError):
                self._error_handler(error)
            else:
                self.logger.warning('Given error handler is not a callable object.')

        self.logger.warning(str(error))

    # Clears everything within the layer.
    def reset(self):
        """
        Reset the layer: Empty all buffers, set the internal state machines to Idle
        """
        while not self._tx_queue.empty():
            self._tx_queue.get()

        while not self._rx_queue.empty():
            self._rx_queue.get()

        self.stop_sending()
        self.stop_receiving()

    # Gives a time to pass to time.sleep() based on the state of the FSM. Avoid using too much CPU
    def sleep_time(self):
        """
        Returns a value in seconds that can_comm be passed to ``time.sleep()`` when the stack is processed in a different t
        hread.

        The value will change according to the internal state machine state, sleeping longer while idle and shorter
        when active.
        """
        timings = {
            (RxState.IDLE, TxState.IDLE): 0.05,
            (RxState.IDLE, TxState.WAIT_FC): 0.01,
        }

        key = (self._rx_state, self._tx_state)
        if key in timings:
            return timings[key]
        return 0.001


class CanStack(TransportLayer):
    """
    All parameters except the ``bus`` parameter will be given to the :class: "TransportLayer" initializer

    :param bus: A can_comm bus object implementing ``recv`` and ``send``
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
        """
        Method invoked to send the messages through CAN layer 2
        :param msg: CAN Message
        :return: None
        """
        self.bus.send(CanMessage(arbitration_id=msg.arbitration_id, data=msg.data, is_extended_id=msg.is_extended_id,
                                 is_fd=msg.is_fd))

    def rx_canbus(self):
        """
        ethod invoked to receive the messages from CAN layer 2
        :return: CAN Message
        """
        msg = self.bus.receive(0)
        if msg is not None:
            return CanMessage(arbitration_id=msg.arbitration_id, data=msg.data, is_extended_id=msg.is_extended_id,
                              is_fd=msg.is_fd)
        return None

    def __init__(self, bus, *args, **kwargs):
        """

        :param bus: can_comm bus eg: vector, goepel, kvsaer, etc...
        :param args: Positional args
        :param kwargs: key word args
        """
        self.bus = bus
        TransportLayer.__init__(self, rxfn=self.rx_canbus, txfn=self.tx_canbus, *args, **kwargs)
