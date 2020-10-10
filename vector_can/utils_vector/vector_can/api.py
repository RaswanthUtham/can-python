# from .driver import *
from ctypes import *
from . import vc_class
from . import driver as vc_driver
from .. import v_def
from .. import v_class
from .. import VectorApi


class VectorCanApi(VectorApi):
    """
    This class provides the api for vector can
    """

    @staticmethod
    def xlCanSetChannelMode(portHandle: v_def.XLportHandle,
                            accessMask: v_def.XLaccess,
                            tx: c_int,
                            txrq: c_int):
        """
        This function specifies whether the caller will get a Tx and/or a TxRq receipt for transmitted messages
        (for CAN channels defined by accessMask). The default is TxRq deactivated and Tx activated
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed. Typically, the access
                            mask can be directly retrieved from the Vector Hardware Configuration tool if
                            there is a prepared application setup
        :param tx: A flag specifying whether the channel should generate receipts when a message
                    is transmitted by the CAN chip.
                    - ‘1’ = generate receipts
                    - ‘0’ = deactivated.
                    Sets the XL_MessageFlags.XL_CAN_MSG_FLAG_TX_COMPLETED flag.

        :param txrq: A flag specifying whether the channel should generate receipts when a message
                    is ready for transmission by the CAN chip.
                    - ‘1’ = generate receipts,
                    - ‘0’ = deactivated.
                    Sets the XL_MessageFlags.XL_CAN_MSG_FLAG_TX_REQUEST flag.

        :return: Returns an error code
        """
        return vc_driver.xlCanSetChannelMode(portHandle, accessMask, tx, txrq)

    @staticmethod
    def xlReceive(portHandle: v_def.XLportHandle,
                  pEventCount: POINTER(c_uint),
                  pEventList: POINTER(v_class.XLevent)):
        """
        Reads the received events from the message queue.
        Supported bus types:
        ► CAN
        ► LIN
        ► K-Line
        ► DAIO
        An application should read all available messages to be sure to re-enable the event.
        An overrun of the receive queue can be determined by the message flag XL_EVENT_
        FLAG_OVERRUN in v_class.XLevent.flags.

        :param portHandle: The port handle retrieved by xlOpenPort()
        :param pEventCount: Pointer to an event counter. On input, the variable must be set to the size (in messages)
                            of the received buffer. On output, the variable contains the number of received messages.
        :param pEventList: Pointer to the application allocated receive event buffer The buffer must be large enough
                            to hold the requested messages (pEventCount).
        :return: Returns an error code
        """
        return vc_driver.xlReceive(portHandle, pEventCount, pEventList)

    @staticmethod
    def xlCanSetChannelBitrate(portHandle: v_def.XLportHandle,
                               accessMask: v_def.XLaccess,
                               bitrate: c_ulong):
        """
        This function provides a simple way to specify the bit rate. The sample point is about 69 % (SJW=1, samples=1).
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :param bitrate: Bit rate in BPS. May be in the range 15000 … 1000000
        :return: Returns an error code
        """
        return vc_driver.xlCanSetChannelBitrate(portHandle, accessMask, bitrate)

    @staticmethod
    def xlCanSetChannelParams(portHandle: v_def.XLportHandle,
                              accessMask: v_def.XLaccess,
                              pChipParams: POINTER(vc_class.XLchipParams)):
        """
        This function initializes the channels defined by accessMask with the given parameters. In order to call this
        function the port must have init access, and the selected channels must  be deactivated.
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :param pChipParams: Pointer to an array of chip parameters
        :return: Returns an error code
        """
        return vc_driver.xlCanSetChannelParams(portHandle, accessMask, pChipParams)

    @staticmethod
    def xlCanTransmit(portHandle: v_def.XLportHandle,
                      accessMask: v_def.XLaccess,
                      messageCount: POINTER(c_uint),
                      pMessages: POINTER(v_class.XLevent)):
        """
        This function transmits CAN messages on the selected channels. It is possible to transmit more messages with
        only one function call
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :param messageCount: Points to the amount of messages to be transmitted or returns the number of transmitted
                                messages.
        :param pMessages: Points to a user buffer with messages to be transmitted,
                            e. g. v_class.XLevent xlEvent[100];
                            At least the buffer must have the size of messageCount.
                            or Returns the number of successfully transmitted messages.
        :return: Returns XL_SUCCESS if all requested messages have been successfully transmitted.
                If no message or not all requested messages have been transmitted because the
                internal transmit queue is full, XL_ERR_QUEUE_IS_FULL is returned
        """
        return vc_driver.xlCanTransmit(portHandle, accessMask, messageCount, pMessages)

    @staticmethod
    def xlCanFlushTransmitQueue(portHandle: v_def.XLportHandle,
                                accessMask: v_def.XLaccess):
        """
        The function flushes the transmit queues of the selected channels.
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :return: Returns an error code
        """
        return vc_driver.xlCanFlushTransmitQueue(portHandle, accessMask)

    @staticmethod
    def xlCanSetChannelAcceptance(portHandle: v_def.XLportHandle,
                                  accessMask: v_def.XLaccess,
                                  code: c_ulong,
                                  mask: c_ulong,
                                  idRange: c_uint):
        """
        A filter lets pass messages. Different ports may have different filters for a channel. If
        the CAN hardware cannot implement the filter, the driver virtualizes filtering.
        However, in some configurations with multiple ports, the application will receive messages although
        it has installed a filter blocking those message IDs.

        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :param code: The acceptance code for id filtering.
        :param mask: The acceptance mask for id filtering, bit = 1 means relevant.
        :param idRange: To distinguish whether the filter is for standard or extended identifiers:
                        XL_CAN_STD
                        XL_CAN_EXT
        :return: Returns an error code
        """
        return vc_driver.xlCanSetChannelAcceptance(portHandle, accessMask, code, mask, idRange)

    @staticmethod
    def xlCanResetAcceptance(portHandle: v_def.XLportHandle,
                             accessMask: v_def.XLaccess,
                             idRange: c_uint):
        """
        Resets the acceptance filter. The selected filters (depending on the idRange flag) are open
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :param idRange: In order to distinguish whether the filter is reset for standard or extended identifiers.
                        XL_CAN_STD
                        Opens the filter for standard message IDs.
                        XL_CAN_EXT
                        Opens the filter for extended message IDs.
        :return: Returns an error code
        """
        return vc_driver.xlCanResetAcceptance(portHandle, accessMask, idRange)

    @staticmethod
    def xlCanRequestChipState(portHandle: v_def.XLportHandle,
                              accessMask: v_def.XLaccess):
        """
        This function requests a CAN controller chipstate for all selected channels. For each
        channel an XL_CHIPSTATE event can be received by calling xlReceive().

        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :return: Returns an error code
        """
        return vc_driver.xlCanRequestChipState(portHandle, accessMask)

    @staticmethod
    def xlCanSetChannelOutput(portHandle: v_def.XLportHandle,
                              accessMask: v_def.XLaccess,
                              mode: c_char):
        """
        If mode is XL_OUTPUT_MODE_SILENT the CAN chip will not generate any acknowledges when a CAN message is received.
        It is not possible to transmit messages, but they can be received in the silent mode.
        Normal mode is the default mode if this function is not called.

        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :param mode: Specifies the output mode of the CAN chip.
                    XL_OUTPUT_MODE_SILENT
                    No acknowledge will be generated on receive (silent mode).
                    Note: With driver version V5.5, the silent mode has been changed. The Tx pin is
                    switched off now (the ‘SJA1000 silent mode’ is not used anymore).
                    XL_OUTPUT_MODE_NORMAL
                    Acknowledge (normal mode)
        :return: Returns an error code
        """
        return vc_driver.xlCanSetChannelOutput(portHandle, accessMask, mode)

    # ------------------------------------- CAN-FD -----------------------------------------------------

    @staticmethod
    def xlCanFdSetConfiguration(portHandle: v_def.XLportHandle,
                                accessMask: v_def.XLaccess,
                                pCanFdConf: POINTER(vc_class.XLcanFdConf)):
        """
        Sets up a CAN FD channel. The structure differs between the arbitration part and the data part of a CAN message
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :param pCanFdConf: Points to the CAN FD configuration structure to set up a CAN FD channel
        :return: Returns an error code
        """
        return vc_driver.xlCanFdSetConfiguration(portHandle, accessMask, pCanFdConf)

    @staticmethod
    def xlCanReceive(portHandle: v_def.XLportHandle,
                     pXlCanRxEvt: POINTER(vc_class.XLcanRxEvent)):
        """
        The function receives the CAN FD messages on the selected port.
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param pXlCanRxEvt: Pointer to the application allocated receive event buffer
        :return: XL_ERR_QUEUE_IS_EMPTY: No event is available
        """
        return vc_driver.xlCanReceive(portHandle, pXlCanRxEvt)

    @staticmethod
    def xlCanTransmitEx(portHandle: v_def.XLportHandle,
                        accessMask: v_def.XLaccess,
                        msgCnt: c_uint,
                        pMsgCntSent: POINTER(c_uint),
                        pXlCanTxEvt: POINTER(vc_class.XLcanTxEvent)):
        """
        The function transmits CAN FD messages on the selected channels. It is possible to send multiple messages
        in a row (with a single call).

        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed.
        :param msgCnt: Amount of messages to be transmitted by the user.
        :param pMsgCntSent: Amount of messages which were transmitted.
        :param pXlCanTxEvt: Points to a user buffer with messages to be transmitted At least the buffer must have the
        size of msgCnt.
        :return: Returns XL_SUCCESS if all requested messages have been successfully transmitted.
                If no message or not all requested messages have been transmitted because the
                internal transmit queue is full, XL_ERR_QUEUE_IS_FULL is returned
        """
        return vc_driver.xlCanTransmitEx(portHandle, accessMask, msgCnt, pMsgCntSent, pXlCanTxEvt)

    @staticmethod
    def xlCanGetEventString(pEv: vc_class.XLcanRxEvent):
        """
        This function returns a string based on the passed CAN Rx event data.
        :param pEv: Points the CAN Rx event buffer to be parsed
        :return: Returns an error code
        """
        return vc_driver.xlCanGetEventString(pEv)
