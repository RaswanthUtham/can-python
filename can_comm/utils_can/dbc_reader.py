"""
1. Message Syntax
    BO_ 32_BIT_DBC_ID MSG_NAME: DATA_LENGTH [SENDER]
     SG_ SIGNAL_NAME : START_BIT|BIT_LENGTH@<1 or 0><+ or -> (SCALE, OFFSET) [MIN|MAX] "UNIT" [RECEIVER]

    A message starts with BO_ and the ID must be unique and in decimal (not hexadecimal)
    The DBC ID adds adds 3 extra bits for 29 bit CAN IDs to serve as an ‘extended ID’ flag
    The name must be unique, 1-32 characters and may contain [A-z], digits and underscores
    The length (DLC) must be an integer between 0 and 1785
    The sender is the name of the transmitting node, or Vector__XXX if no name is available

    Each message contains 1+ signals that start with SG_
    The name must be unique, 1-32 characters and may contain [A-z], digits and underscores
    The bit start counts from 0 and marks the start of the signal in the data payload
    The bit length is the signal length
    The @1 specifies that the byte order is little-endian/Intel (vs @0 for big-endian/Motorola)
    The + informs that the value type is unsigned (vs - for signed signals)
    The (scale,offset) values are used in the physical value linear equation (more below)
    The [min|max] and unit are optional meta information (they can_comm e.g. be set to [0|0] and “”)
    The receiver is the name of the receiving node (again, Vector__XXX is used as default)

    eg:
    BO_ 2564816638 DM13: 8 Vector__XXX
     SG_ HoldSignal : 28|4@1+ (1,0) [0|15] "" Vector__XXX
     SG_ J1939Network3 : 22|2@1+ (1,0) [0|3] "" Vector__XXX
     SG_ J1939Network2 : 14|2@1+ (1,0) [0|3] "" Vector__XXX

2. Match the dbc id with can_comm id
    11 bit CAN IDS <=> DBC IDS
    29 bit CAN IDS <=> 0x1FFFFFFF & 32 bit DBC ID

3. parse and store the message name and corresponding signals.
"""


class DbcParser:
    """
    parse the messages and signals from dbc file
    """

    def __init__(self, path):
        """
        Initializer
        """
        self.path = path
        if not isinstance(path, list):
            self.path = [path]
        self.message = {}
        self.signal = {}
        self.parse_dbc()

    def parse_dbc(self):
        """
        parse messages and signals
        """
        for path in self.path:
            with open(path, "r", encoding="cp1252") as f:
                data = f.readlines()
            for d in data:
                if d.startswith("BO_ ") and d.endswith("\n"):
                    _, id_, m_name, length, sender = d.split(" ")
                    m_name = m_name.replace(':', '').strip()
                    self.message[m_name + '.id'] = id_
                    self.message[m_name + '.length'] = length
                    self.message[m_name + '.direction'] = sender
                    self.message[id_ + '.name'] = m_name

                if d.startswith(" SG_") and d.endswith("\n"):
                    name, details = d.split(":")
                    name = name.replace('SG_', '').strip()
                    _, bit_details, scale_and_offset, min_max, unit, *_, receiver = details.split(" ")
                    little_endian = '@1' in bit_details
                    signed = '-' in bit_details
                    start_bit, bit_length = bit_details[:-3].split('|')
                    scale, offset = scale_and_offset.replace('(', '').replace(')', '').split(',')
                    min_value, max_value = min_max.replace('[', '').replace(']', '').split('|')
                    receiver = receiver.strip()
                    self.signal[name + '.all'] = (("message_name", m_name),
                                                  ("start_bit", start_bit),
                                                  ("bit_length", bit_length),
                                                  ("little_endian", little_endian),
                                                  ("signed", signed),
                                                  ("scale", scale),
                                                  ("offset", offset),
                                                  ("min_value", min_value),
                                                  ("max_value", max_value),
                                                  ("unit", unit),
                                                  ("receiver", receiver),
                                                  )
                    self.signal[name + '.start_bit'] = int(start_bit)
                    self.signal[name + '.bit_length'] = int(bit_length)
                    self.signal[name + '.little_endian'] = little_endian
                    self.signal[name + '.signed'] = signed
                    self.signal[name + '.scale'] = float(scale)
                    self.signal[name + '.offset'] = float(offset)
                    self.signal[name + '.min_value'] = float(min_value)
                    self.signal[name + '.max_value'] = float(max_value)
                    self.signal[name + '.unit'] = unit if not "" else None
                    self.signal[name + '.receiver'] = receiver
                    self.signal[name + '.message'] = m_name

    def get_signals(self, msg):
        """
        This method returns the signals present in the corresponding method
        :param msg: message whose signals are returned
        :return: list of signals
        """
        signals = list()
        for key, value in self.signal.items():
            try:
                if msg in value:
                    signals.append(key.split('.')[0])
            except TypeError:
                pass
        return signals
