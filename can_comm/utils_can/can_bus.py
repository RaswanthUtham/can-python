"""
    created on oct 2020

    :file: can_bus.py
    :platform: Linux, Windows
    :synopsis:
        Implementation of CAN bus. Contains ABC for CAN bus.
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""
import logging
from time import time
from typing import cast, Iterator, List, Optional, Tuple
from abc import ABCMeta, abstractmethod
from . import CanMessage as Message
from . import TypeCheck

LOG = logging.getLogger(__name__)


class CanBus(metaclass=ABCMeta):
    """The CAN Bus Abstract Base Class that serves as the basis
    for all concrete interfaces.

    This class may be used as an iterator over the received messages.
    """

    #: a string describing the underlying bus and/or channel
    channel_info = "unknown"


    @abstractmethod
    def __init__(
            self,
            can_filters: Optional[TypeCheck.CanFilters] = None,
    ):
        """Construct and open a CAN bus instance of the specified type.

        Subclasses should call though this method with all given parameters
        as it handles generic tasks like applying filters.


        :param can_filters:
            See :meth:`~can_comm.BusABC.set_filters` for details.
        """
        self.set_filters(can_filters)

    def __str__(self) -> str:
        return self.channel_info

    def receive(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Block waiting for a message from the Bus.

        :param timeout:
            seconds to wait for a message or None to wait indefinitely

        :return:
            None on timeout or a :class:`CanMessage` object.
        :raises can_comm.CanError:
            if an error occurred while reading
        """
        start = time()
        time_left = timeout

        while True:

            # try to get a message
            msg, already_filtered = self._receive_from_interface(timeout=time_left)

            # return it, if it matches
            if msg and (already_filtered or self._matches_filters(msg)):
                LOG.debug("Received: %s", msg)
                return msg

            # if not, and timeout is None, try indefinitely
            if timeout is None:
                continue

            # try next one only if there still is time, and with
            # reduced timeout
            else:

                time_left = timeout - (time() - start)

                if time_left > 0:
                    continue
                else:
                    return None

    @abstractmethod
    def _receive_from_interface(self, timeout: Optional[float]) -> Tuple[Optional[Message], bool]:
        """
        Read a message from the bus and tell whether it was filtered.
        This methods may be called by :meth:`~can_comm.BusABC.recv`
        to read a message multiple times if the filters set by
        :meth:`~can_comm.BusABC.set_filters` do not match and the call has
        not yet timed out.

        New implementations should always override this method instead of
        :meth:`~can_comm.BusABC.recv`, to be able to take advantage of the
        software based filtering provided by :meth:`~can_comm.BusABC.recv`
        as a fallback. This method should never be called directly.

        :param float timeout: seconds to wait for a message,
                              see :meth:`~can_comm.BusABC.send`

        :return:
            1.  a message that was read or None on timeout
            2.  a bool that is True if message filtering has already
                been done and else False

        :raises can_comm.CanError:
            if an error occurred while reading
        :raises NotImplementedError:
            if the bus provides it's own :meth:`~can_comm.BusABC.recv`
            implementation (legacy implementation)

        """

    @abstractmethod
    def send(self, msg: Message, timeout: Optional[float] = None):
        """Transmit a message to the CAN bus.

        Override this method to enable the transmit path.

        :param Message msg: A message object.

        :param timeout:
            If > 0, wait up to this many seconds for message to be ACK'ed or
            for transmit queue to be ready depending on driver implementation.
            If timeout is exceeded, an exception will be raised.
            Might not be supported by all interfaces.
            None blocks indefinitely.

        :raises can_comm.CanError:
            if the message could not be sent
        """

    def __iter__(self) -> Iterator[Message]:
        """Allow iteration on messages as they are received.
        :yields: :class:`CanMessage` msg objects.
        """
        while True:
            msg = self.receive(timeout=1.0)
            if msg is not None:
                yield msg

    @property
    def filters(self) -> Optional[TypeCheck.CanFilters]:
        """
        Modify the filters of this bus. See :meth:`self.set_filters`
        for details.
        """
        return self._filters

    @filters.setter
    def filters(self, filters: Optional[TypeCheck.CanFilters]):
        self.set_filters(filters)

    def set_filters(self, filters: Optional[TypeCheck.CanFilters] = None):
        """Apply filtering to all messages received by this Bus.

        All messages that match at least one filter are returned.
        If `filters` is `None` or a zero length sequence, all
        messages are matched.

        Calling without passing any filters will reset the applied
        filters to `None`.

        :param filters:
            A iterable of dictionaries each containing a "can_id",
            a "can_mask", and an optional "extended" key.

            >>> [{"can_id": 0x11, "can_mask": 0x21, "extended": False}]

            A filter matches, when
            ``<received_can_id> & can_mask == can_id & can_mask``.
            If ``extended`` is set as well, it only matches messages where
            ``<received_is_extended> == extended``. Else it matches every
            messages based only on the arbitration ID and mask.
        """
        self._filters = filters or None
        self._apply_filters(self._filters)

    @abstractmethod
    def _apply_filters(self, filters: Optional[TypeCheck.CanFilters]):
        """
        Hook for applying the filters to the underlying kernel or
        hardware if supported/implemented by the interface.

        :param filters:
            See :meth:`~can_comm.BusABC.set_filters` for details.
        """

    def _matches_filters(self, msg: Message) -> bool:
        """Checks whether the given message matches at least one of the
        current filters. See :meth:`~can_comm.BusABC.set_filters` for details
        on how the filters work.

        This method should not be overridden.

        :param msg:
            the message to check if matching
        :return: whether the given message matches at least one filter
        """

        # if no filters are set, all messages are matched
        if self._filters is None:
            return True

        for _filter in self._filters:
            # check if this filter even applies to the message
            if "extended" in _filter:
                _filter = cast(TypeCheck.CanFilterExtended, _filter)
                if _filter["extended"] != msg.is_extended_id:
                    continue

            # then check for the mask and id
            can_id = _filter["can_id"]
            can_mask = _filter["can_mask"]

            # basically, we compute
            # `msg.arbitration_id & can_mask == can_id & can_mask`
            # by using the shorter, but equivalent from below:
            if (can_id ^ msg.arbitration_id) & can_mask == 0:
                return True

        # nothing matched
        return False

    @abstractmethod
    def flush_tx_buffer(self):
        """Discard every message that may be queued in the output buffer(s).
        """

    @abstractmethod
    def shutdown(self):
        """
        Called to carry out any interface specific cleanup required
        in shutting down a bus.
        """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    @staticmethod
    def _detect_available_configs() -> List[TypeCheck.AutoDetectedConfig]:
        """Detect all configurations/channels that this interface could
        currently connect with.

        This might be quite time consuming.

        May not to be implemented by every interface on every platform.

        :return: an iterable of dicts, each being a configuration suitable
                 for usage in the interface's bus constructor.
        """
        raise NotImplementedError()
