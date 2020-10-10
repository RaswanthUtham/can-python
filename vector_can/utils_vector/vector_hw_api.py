from ctypes import *
from . import vector_defines as v_def
from . import vector_class as v_class
from . import vector_driver as v_driver


class VectorApi:
    """
    This class provides the api for vector hw
    """

    @staticmethod
    def xlGetErrorString(err: v_def.XLstatus):
        """
         Returns the textual description of the given error code
        :param err: Error code
        :return: Error code as plain text string.
        """
        return v_driver.xlGetErrorString(err)

    @staticmethod
    def xlGetDriverConfig(pDriverConfig: POINTER(v_class.XLdriverConfig)):
        """
        Gets detailed information on the hardware configuration. This function can be called at
        any time after a successfully xlOpenDriver() call. The result describes the current
        state of the driver configuration after each call.
        :param pDriverConfig: Points to the information structure that is returned by the driver
        :return: Returns an error code
        """
        return v_driver.xlGetDriverConfig(pDriverConfig)

    @staticmethod
    def xlOpenDriver():
        """
        Each application must call this function to load the driver. If the function call is not successful
        (XLStatus = 0), no other API calls are possible.
        :return: Returns an error code
        """
        return v_driver.xlOpenDriver()

    @staticmethod
    def xlCloseDriver():
        """
        This function closes the driver
        :return: Returns an error code
        """
        return v_driver.xlCloseDriver()

    @staticmethod
    def xlGetApplConfig(appName: c_char_p,
                        appChannel: c_uint,
                        pHwType: POINTER(c_uint),
                        pHwIndex: POINTER(c_uint),
                        pHwChannel: POINTER(c_uint),
                        busType: c_uint):
        """
        Retrieves the hardware settings for an application which are configured in the Vector
        Hardware Configuration tool. The information can then be used to get the required channel mask
        (see section xlGetChannelMask). To open a port with multiple channels, the retrieved channel masks have to be
        combined before and then passed over to the open port function.
        :param appName: Name of the application to be read (e. g. "xlCANcontrol").
                        Application names are listed in the Vector Hardware Configuration tool.

        :param appChannel: Selects the application channel (0,1, …). An application can offer several channels
                            which are assigned to physical channels (e. g. “CANdemo CAN1” to VN1610
                            Channel 1 or “CANdemo CAN2” to VN1610 Channel 2). Such an assignment has
                            to be configured with the Vector Hardware Config tool.

        :param pHwType: Hardware type is returned eg: XL_HardwareType.XL_HWTYPE_CANCARDXL
        :param pHwIndex: Index of same hardware types is returned (0,1, ...),
                        e. g. for two CANcardXL on one system:
                        - CANcardXL 01: hwIndex = 0
                        - CANcardXL 02: hwIndex = 1

        :param pHwChannel: Channel index of same hardware types is returned (0,1, ...),
                            e. g. CANcardXL:
                            Channel 1: hwChannel = 0
                            Channel 2: hwChannel = 1
        :param busType: Specifies the bus type which is used by the application. eg XL_BUS_TYPE_CAN
        :return: Returns an error code
        """
        return v_driver.xlGetApplConfig(appName, appChannel, pHwType, pHwIndex, pHwChannel, busType)

    @staticmethod
    def xlSetApplConfig(appName: c_char_p,
                        appChannel: c_uint,
                        hwType: c_uint,
                        hwIndex: c_uint,
                        hwChannel: c_uint,
                        busType: c_uint):
        """
        Creates a new application in the Vector Hardware Config tool or sets the channel
        configuration in an existing application. To set an application channel to "not
        assigned" state set hwType, hwIndex and hwChannel to 0.

        :param appName: Name of the application to be set.
                        Application names are listed in the Vector Hardware Configuration tool.

        :param appChannel: Application channel (0,1, …) to be accessed.
                           If the channel number does not exist, it will be created.

        :param hwType: Contains the hardware type (see vxlapi.h),
                        e. g. CANcardXL:
                        XL_HWTYPE_CANCARDXL

        :param hwIndex: Index of same hardware types (0,1, ...),
                        e. g. for two CANcardXL on one system:
                        CANcardXL 01: hwIndex = 0
                        CANcardXL 02: hwIndex = 1

        :param hwChannel: Channel index on one physical device (0, 1, ...)
                            e. g. CANcardXL with hwIndex=0:
                            Channel 1: hwChannel = 0
                            Channel 2: hwChannel = 1
        :param busType: Specifies the bus type for the application, e. g.
                        XL_BusTypes.XL_BUS_TYPE_CAN
                        XL_BusTypes.XL_BUS_TYPE_LIN
                        XL_BusTypes.XL_BUS_TYPE_DAIO
        :return: Returns an error code
        """

        return v_driver.xlSetApplConfig(appName, appChannel, hwType, hwIndex, hwChannel, busType)

    @staticmethod
    def xlGetChannelIndex(hwType: c_int,
                          hwIndex: c_int,
                          hwChannel: c_int):
        """

        :param hwType:
        :param hwIndex:
        :param hwChannel:
        :return:
        """
        return v_driver.xlGetChannelIndex(hwType, hwIndex, hwChannel)

    @staticmethod
    def xlGetChannelMask(hwType: c_int,
                         hwIndex: c_int,
                         hwChannel: c_int):
        """

        :param hwType:
        :param hwIndex:
        :param hwChannel:
        :return:
        """
        return v_driver.xlGetChannelMask(hwType, hwIndex, hwChannel)

    @staticmethod
    def xlOpenPort(portHandle: POINTER(v_def.XLportHandle),
                   userName: c_char_p,
                   accessMaskL: v_def.XLaccess,
                   permissionMask: POINTER(v_def.XLaccess),
                   rxQueueSize: c_uint,
                   xlInterfaceVersion: c_uint,
                   busType: c_uint):
        """

        :param portHandle:
        :param userName:
        :param accessMaskL:
        :param permissionMask:
        :param rxQueueSize:
        :param xlInterfaceVersion:
        :param busType:
        :return:
        """
        return v_driver.xlOpenPort(portHandle, userName, accessMaskL, permissionMask, rxQueueSize, xlInterfaceVersion,
                                   busType)

    @staticmethod
    def xlGetSyncTime(portHandle: v_def.XLportHandle, time: POINTER(v_def.XLuint64)):
        """
        If the software time synchronization is active, the event time stamp is synchronized to the PC time.
        If the XL API function xlResetClock() was not called, the event time stamp can be compared to the time
        retrieved from xlGetSyncTime().
        Returns the current high precision PC time (in ns)
        :param portHandle: The port handle retrieved by xlOpenPort().
        :param time: Points to a variable that receives the sync time.
        :return: Returns an error code
        """
        return v_driver.xlGetSyncTime(portHandle, time)

    @staticmethod
    def xlGetChannelTime(portHandle: v_def.XLportHandle,
                         accessMask: v_def.XLaccess,
                         pChannelTime: POINTER(v_def.XLuint64)):
        """
        This function is available only on VN8900 devices and returns the 64 bit PC-based card time.

        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed
        :param pChannelTime: 64 bit PC-based card time.
        :return: Returns an error code
        """
        return v_driver.xlGetChannelTime(portHandle, accessMask, pChannelTime)

    @staticmethod
    def xlClosePort(portHandle: v_def.XLportHandle):
        """
        This function closes a port and deactivates its channels.
        :param portHandle: The port handle retrieved by xlOpenPort().
        :return: Returns an error code
        """
        return v_driver.xlClosePort(portHandle)

    @staticmethod
    def xlSetNotification(portHandle: v_def.XLportHandle,
                          handle: v_def.XLhandle,
                          queueLevel: c_int):
        """
        The function returns the notification handle. It notifies when messages are available in
        the receive queue. The handle is closed when unloading the library.
        The parameter queueLevel specifies the number of messages that triggers the
        event. Note that the event is triggered only once when the queueLevel is reached.
        An application should read all available messages by xlReceive() to be sure to reenable the event.

        :param portHandle: The port handle retrieved by xlOpenPort().
        :param handle: Pointer to a WIN32 event handle.
        :param queueLevel: Queue level that triggers this event. For LIN, this is fixed to ‘1’.
        :return: Returns the status
        """
        return v_driver.xlSetNotification(portHandle, handle, queueLevel)

    @staticmethod
    def xlActivateChannel(portHandle: v_def.XLportHandle,
                          accessMask: v_def.XLaccess,
                          busType: c_uint,
                          flags: c_uint):
        """
        Goes ‚on bus’ for the selected port and channels. At this point, the user can transmit
        and receive messages on the bus.

        :param portHandle: The port handle retrieved by xlOpenPort()
        :param accessMask: The access mask specifies the channels to be accessed. Typically, the access
                            mask can be directly retrieved from the Vector Hardware Configuration tool if
                            there is a prepared application setup
        :param busType: Bus type that has also been used for xlOpenPort().
        :param flags: Additional flags for activating the channels
                        eg: XL_AC_Flags.XL_ACTIVATE_RESET_CLOCK
                      Resets the internal clock after activating the channel
        :return: Returns an error code
        """
        return v_driver.xlActivateChannel(portHandle, accessMask, busType, flags)

    @staticmethod
    def xlDeactivateChannel(portHandle: v_def.XLportHandle, accessMask: v_def.XLstatus):
        """
        The selected channels go off the bus. The channels are deactivated if there is no further port that activates
        the channels.

        :param portHandle: The port handle retrieved by xlOpenPort().
        :param accessMask: The access mask specifies the channels to be accessed. Typically, the access
                            mask can be directly retrieved from the Vector Hardware Configuration tool if
                            there is a prepared application setup
        :return: Returns an error code
        """
        return v_driver.xlDeactivateChannel(portHandle, accessMask)

    @staticmethod
    def xlPopupHwConfig(callSign: c_char_p = None,
                        waitForFinish: c_uint = 0):
        """
        Call this function to pop up the Vector Hardware Config tool
        :param callSign: Reserved type
        :param waitForFinish: Timeout (for the application) to wait for the user entry within Vector Hardware
                                Config in milliseconds.
                                0: The application does not wait.
        :return: Returns an error code
        """
        return v_driver.xlPopupHwConfig(callSign, waitForFinish)

    @staticmethod
    def xlSetTimerRate(portHandle: v_def.XLportHandle,
                       timerRate: c_ulong):
        """
        This call sets the rate for the port‘s cyclic timer events. The resolution of timeRate is 10 µs, but the
        internal step width is 1000 µs. Values less than multiples of 1000 µs will be rounded down (truncated) to
        the next closest value.
        Examples:   timerRate = 105: 1050 µs → 1000 µs
                    timerRate = 140: 1400 µs → 1000 µs
                    timerRate = 240: 2400 µs → 2000 µs
                    timerRate = 250: 2500 µs → 2000 µs

        The minimum timer rate value is 1000 µs (timerRate = 100).
        If more than one application uses the timer events the lowest value will be used for all.
        Example:
        Application 1 timerRate = 150 (1000 µs)
        Application 2 timerRate = 350 (3000 µs)
        Used timer rate → 1000 µs

        :param portHandle: The port handle retrieved by xlOpenPort().
        :param timerRate: Value specifying the interval for cyclic timer events generated by a port. If 0 is passed,
                            no cyclic timer events will be generated.
        :return: Returns an error cod
        """
        return v_driver.xlSetTimerRate(portHandle, timerRate)

    @staticmethod
    def xlGetEventString(event: POINTER(v_class.XLevent)):
        """
        Returns the textual description of the given event.
        Supported bus types and events:
        ► CAN
        ► LIN
        ► partly DAIO
        ► common events (e. g. TIMER events)

        :param event: Points to the event
        :return: Text string.
        """
        return v_driver.xlGetEventString(event)
