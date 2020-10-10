"""
Utilities and configuration file parsing.
"""
import re
import logging
from typing import Optional, Union

from .type_check import TypeCheck

log = logging.getLogger("can.util")

# tuple of valid data lengths for a CAN FD message
CAN_FD_DLC = (0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64)


def len2dlc(length: int) -> int:
    """Calculate the DLC from data length.

    :param int length: Length in number of bytes (0-64)

    :returns: DLC (0-15)
    """
    if length <= 8:
        return length
    for dlc, nof_bytes in enumerate(CAN_FD_DLC):
        if nof_bytes >= length:
            return dlc
    return 15


def dlc2len(dlc: int) -> int:
    """Calculate the data length from DLC.

    :param dlc: DLC (0-15)

    :returns: Data length in number of bytes (0-64)
    """
    return CAN_FD_DLC[dlc] if dlc <= 15 else 64


def channel2int(channel: Optional[Union[TypeCheck.Channel]]) -> Optional[int]:
    """Try to convert the channel to an integer.

    :param channel:
        Channel string (e.g. can0, CAN1) or integer

    :returns: Channel integer or `None` if unsuccessful
    """
    if channel is None:
        return None
    if isinstance(channel, int):
        return channel
    # String and byte objects have a lower() method
    if hasattr(channel, "lower"):
        match = re.match(r".*(\d+)$", channel)
        if match:
            return int(match.group(1))
    return None
