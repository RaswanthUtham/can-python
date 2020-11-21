"""
    created on oct 2020

    :file: dbc_value_calc.py
    :platform: Linux, Windows
    :synopsis:
        physical and raw value calculator
    :author:
        -Raswanth Utham <raswanth.a@gmail>
"""

from copy import deepcopy

BYTE_INDEX_MSB = (7, 15, 23, 31, 39, 47, 55, 63)
BYTE_INDEX_LSB = (0, 8, 16, 24, 32, 40, 48, 56)
MASK_VALUES_MSB = (0X1, 0X3, 0X7, 0XF, 0X1F, 0X3F, 0X7F)


def start_byte_bits(start_byte, start_bit, bit_length):
    """
    calculates the number of bits in the start_byte
    :param start_byte: byte in which the start_bit present
    :param start_bit: start bit of the signal (LSB)
    :param bit_length: length of the signal in bits
    :return: number of bits present in the first byte
    """
    bits = [x for x in range(start_byte * 8 + 7, start_byte * 8 - 1, -1)]
    end_bit = start_bit + bit_length - 1
    if end_bit in bits:
        return end_bit - start_bit + 1
    bits_present = bits.index(start_bit) + 1
    return bits_present


def find_byte_position(start_byte, start_bit, nof_start_bits, bit_length, data_length, little_endian=True):
    """
    determines the index of the bytes of message from which the signal value has to be parsed
    :param start_byte: signal start byte
    :param start_bit: signal start bit
    :param nof_start_bits: number of its in signal start byte
    :param bit_length: signal length
    :param data_length: message length
    :param little_endian: True for little endian and false for big endian
    :return: list of byte index from which the signal should be parsed
    """
    byte_position = []
    index = 0

    if start_bit != BYTE_INDEX_LSB[start_byte]:
        byte_position.append(start_byte)
        index += 1
        bit_length -= nof_start_bits

        if bit_length <= 0:
            return deepcopy(byte_position)

        if bit_length <= 8:
            if little_endian:
                if start_byte == data_length - 1:  # byte boundary check
                    return deepcopy(byte_position)
                byte_position.append(start_byte + 1)
            else:
                if start_byte == 0:  # byte boundary check
                    return deepcopy(byte_position)
                byte_position.append(start_byte - 1)
            return deepcopy(byte_position)

    if bit_length <= 8:
        return [start_byte]

    if little_endian:
        while bit_length // 8:
            if start_byte + index > data_length - 1:
                break
            byte_position.append(start_byte + index)
            index += 1
            bit_length -= 8
        if start_byte + index <= data_length - 1:
            if bit_length:
                byte_position.append(start_byte + index)

    else:  # big endian
        while bit_length // 8:
            if start_byte - index < 0:
                break
            byte_position.append(start_byte - index)
            index += 1
            bit_length -= 8
        if start_byte - index >= 0:
            if bit_length:
                byte_position.append(start_byte - index)

    return deepcopy(byte_position)


def mask_mapping(start_byte, start_bit, nof_start_bits, bit_length, nof_index):
    """
    determines the mask values corresponding to the byte index that needs to be parsed
    :param start_byte: signal start byte
    :param start_bit: signal start bit
    :param nof_start_bits: number of bits in start byte
    :param bit_length: signal length
    :param nof_index: number of byte index of signal that needs to be parsed from message
    :return: list of mask values corresponding to bytes
    """
    mask_index = []
    bits_range_in_start_byte = [x for x in range(start_byte * 8 + 7, start_byte * 8 - 1, -1)]
    bits_present_in_start_byte = [x for x in range(start_bit, start_byte * 8 + 8)]

    if start_bit != BYTE_INDEX_LSB[start_byte]:
        start_byte_mask = ['1' if x in bits_present_in_start_byte else '0' for x in bits_range_in_start_byte]
        start_byte_mask = ''.join(start_byte_mask)
        start_byte_mask = int(start_byte_mask, 2)
        mask_index.append(start_byte_mask)
        nof_index -= 1
        bit_length -= nof_start_bits

    for _ in range(nof_index):
        if 0 < bit_length < 8:
            mask_index.append(MASK_VALUES_MSB[bit_length - 1])
            break
        elif bit_length / 8 > 0:
            mask_index.append(0xFF)
        else:
            raise ValueError("Invalid number of bytes and (or) length")
        bit_length -= 8
    return deepcopy(mask_index)


def get_value(byte_index, mask_index, signed, data):
    """
    get the raw value of the signal based on the corresponding bytes and masks
    :param byte_index: list of bytes of signal
    :param mask_index: mask values for corresponding bytes
    :param signed: True if signed value, False otherwise
    :param data: raw data
    :return: raw value
    """
    raw_values = []
    for index, value in enumerate(byte_index):
        raw_values.append(data[value] & mask_index[index])
    raw_values.reverse()
    raw_value = bytearray(raw_values)
    hex_value = [hex(x) for x in raw_value]
    decimal = int(''.join(hex_value).replace('0x', ''), 16)
    if signed:
        if raw_value[0] & 0xF0:  # check for negative sign
            decimal -= (1 << decimal.bit_length())
    return decimal


def get_raw_value(start_bit, bit_length, data_length, signed=False, little_endian=True, data=None):
    """
    get the raw value of the signal
    :param start_bit: signal start bit
    :param bit_length: signal length
    :param data_length: message length
    :param signed: True if signal is a signed value, False otherwise
    :param little_endian: True if little_endian. False Otherwise
    :param data: raw data
    :return: raw value
    """
    if 0 < bit_length <= 64 and 0 < data_length <= 63 and 0 <= start_bit <= 8 * 64 - 1:
        start_byte = start_bit // 8
        nof_start_bits = start_byte_bits(start_byte, start_bit, bit_length)
        indexes = find_byte_position(start_byte, start_bit, nof_start_bits, bit_length, data_length, little_endian)
        mask_values = mask_mapping(start_byte, start_bit, nof_start_bits, bit_length, len(indexes))
    else:
        raise ValueError("invalid bit length and or data_length and or start_bit")
    return get_value(indexes, mask_values, signed, data)


def get_physical_value(start_bit, bit_length, data, scale=1.000, offset=0, signed=False, little_endian=True):
    """
    Calculates the physical value from raw value
    physical_value = offset + scale * raw_value
    :param start_bit: signal start
    :param bit_length: signal length
    :param data: raw data
    :param scale: signal attribute scale
    :param offset: signal attribute offset
    :param signed: True if signal is a signed value, False otherwise
    :param little_endian: True if little_endian. False Otherwise
    :return: physical value
    """
    data_length = len(data)
    value = get_raw_value(start_bit, bit_length, data_length, signed, little_endian, data)
    return scale * value + offset
