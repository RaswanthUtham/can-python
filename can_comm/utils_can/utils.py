"""
    created on oct 2020

    :file: utils.py
    :platform: Linux, Windows
    :synopsis:
        can_comm utilities
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""
import re
import logging
from typing import Optional, Union

from . import TypeCheck

LOG = logging.getLogger("can_comm.util")

# tuple of valid data lengths for a CAN FD message
CAN_FD_DLC = (0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 16, 20, 24, 32, 48, 64)


def positive_number_2s_complement(num):
    """
    takes 2s complement of a positive number
    eg: oxFF -> 2s compliment is -1
    :param num: unsigned integer
    :return: 2s complement of the unsigned integer
    """
    return num - (1 << num.bit_length())


def negative_number_2s_compliment(num):
    """
    takes 2s complement of a negative number
    eg: -1 -> 2s compliment is 0xff
    :param num: negative number
    :return: 2s complement of negative number
    """
    bit_len = num.bit_length()
    byte_len = bit_len // 8
    if bit_len % 8:
        byte_len += 1
    bit_len = byte_len * 8
    return num + (1 << bit_len)


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
