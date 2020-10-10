from typing import Dict, NamedTuple


class AddressMode(NamedTuple):
    Normal_11bits = 0
    Normal_29bits = 1
    NormalFixed_29bits = 2
    Extended_11bits = 3
    Extended_29bits = 4
    Mixed_11bits = 5
    Mixed_29bits = 6


AddressingMode: Dict[int, str] = {AddressMode.Normal_11bits: "Normal_11bits",
                                  AddressMode.Normal_29bits: "Normal_29bits",
                                  AddressMode.NormalFixed_29bits: "NormalFixed_29bits",
                                  AddressMode.Extended_11bits: "Extended_11bits",
                                  AddressMode.Extended_29bits: "Extended_29bits",
                                  AddressMode.Mixed_11bits: "Mixed_11bits",
                                  AddressMode.Mixed_29bits: "Mixed_29bits",
                                  }


class TargetAddressType(NamedTuple):
    Physical = 0  # 1 to 1 communication
    Functional = 1  # 1 to n communication


class Address:

    def __init__(self,
                 addressing_mode: AddressMode = AddressMode.Normal_11bits,
                 tx_id: int = None,
                 rx_id: int = None,
                 target_address: int = None,
                 source_address: int = None,
                 address_extension: int = None):

        """
            Represents the addressing information (N_AI) of the IsoTP layer. Will define what messages will be received and
            how to craft transmitted message to reach a specific party.

            Parameters must be given according to the addressing mode. When not needed, a parameter may be left unset or
            set to ``None``.

            Both the :class:`TransportLayer<isotp.TransportLayer>` and the :class:`isotp.socket<isotp.socket>`
            expects this address object

            :param addressing_mode: The addressing mode. Valid values are defined by the :class: AddressMode class
            :type addressing_mode: int

            :param tx_id: The CAN ID for transmission. Used for these addressing mode: ``Normal_11bits``,
            ``Normal_29bits``, ``Extended_11bits``, ``Extended_29bits``, ``Mixed_11bits``
            :type tx_id: int or None

            :param rx_id: The CAN ID for reception. Used for these addressing mode: ``Normal_11bits``,
            ``Normal_29bits``, ``Extended_11bits``, ``Extended_29bits``, ``Mixed_11bits``
            :type rx_id: int or None

            :param target_address: Target address (N_TA) used in ``NormalFixed_29bits`` and ``Mixed_29bits`` addressing mode.
            :type target_address: int or None

            :param source_address: Source address (N_SA) used in ``NormalFixed_29bits`` and ``Mixed_29bits`` addressing mode.
            :type source_address: int or None

            :param address_extension: Address extension (N_AE) used in ``Mixed_11bits``, ``Mixed_29bits`` addressing mode
            :type address_extension: int or None
            """

        self.addressing_mode = addressing_mode
        self.tx_id = tx_id
        self.rx_id = rx_id
        self.target_address = target_address
        self.source_address = source_address
        self.address_extension = address_extension
        self.is_29bits = True if self.addressing_mode in (AddressMode.Normal_29bits,
                                                          AddressMode.NormalFixed_29bits,
                                                          AddressMode.Extended_29bits,
                                                          AddressMode.Mixed_29bits) else False

        self.validate()

        # From here, input is good. Do some precomputing for speed optimization without bothering about types or values
        self.tx_arbitration_id_physical = self._get_tx_arbitration_id(TargetAddressType.Physical)
        self.tx_arbitration_id_functional = self._get_tx_arbitration_id(TargetAddressType.Functional)

        self.rx_arbitration_id_physical = self._get_rx_arbitration_id(TargetAddressType.Physical)
        self.rx_arbitration_id_functional = self._get_rx_arbitration_id(TargetAddressType.Functional)

        self.tx_payload_prefix = bytearray()
        self.rx_prefix_size = 0

        if self.addressing_mode in (AddressMode.Extended_11bits, AddressMode.Extended_29bits):
            self.tx_payload_prefix.extend(bytearray([self.target_address]))
            self.rx_prefix_size = 1
        elif self.addressing_mode in (AddressMode.Mixed_11bits, AddressMode.Mixed_29bits):
            self.tx_payload_prefix.extend(bytearray([self.address_extension]))
            self.rx_prefix_size = 1

        self.rx_mask = None
        if self.addressing_mode == AddressMode.NormalFixed_29bits:
            self.rx_mask = 0x18DA0000  # This should ignore variant between Physical and Functional addressing
        elif self.addressing_mode == AddressMode.Mixed_29bits:
            self.rx_mask = 0x18CD0000  # This should ignore variant between Physical and Functional addressing

        if self.addressing_mode in (AddressMode.Normal_11bits, AddressMode.Normal_29bits):
            self.is_for_me = self._is_for_me_normal
        elif self.addressing_mode in (AddressMode.Extended_11bits, AddressMode.Extended_29bits):
            self.is_for_me = self._is_for_me_extended
        elif self.addressing_mode == AddressMode.NormalFixed_29bits:
            self.is_for_me = self._is_for_me_normal_fixed
        elif self.addressing_mode == AddressMode.Mixed_11bits:
            self.is_for_me = self._is_for_me_mixed_11bits
        elif self.addressing_mode == AddressMode.Mixed_29bits:
            self.is_for_me = self._is_for_me_mixed_29bits
        else:
            raise RuntimeError('This exception should never be raised.')

    def validate(self):
        if self.addressing_mode not in AddressingMode:
            raise ValueError('Addressing mode is not valid')

        if self.addressing_mode in (AddressMode.Normal_11bits, AddressMode.Normal_29bits):
            if self.rx_id is None or self.tx_id is None:
                raise ValueError('txid and rxid must be specified for Normal addressing mode (11 bits ID)')
            if self.rx_id == self.tx_id:
                raise ValueError('txid and rxid must be different for Normal addressing mode')

        elif self.addressing_mode == AddressMode.NormalFixed_29bits:
            if self.target_address is None or self.source_address is None:
                raise ValueError(
                    'target_address and source_address must be specified for Normal Fixed addressing (29 bits ID)')

        elif self.addressing_mode in [AddressMode.Extended_11bits, AddressMode.Extended_29bits]:
            if self.target_address is None or self.rx_id is None or self.tx_id is None:
                raise ValueError('target_address, rxid and txid must be specified for Extended addressing mode ')
            if self.rx_id == self.tx_id:
                raise ValueError('txid and rxid must be different')

        elif self.addressing_mode == AddressMode.Mixed_11bits:
            if self.rx_id is None or self.tx_id is None or self.address_extension is None:
                raise ValueError('rxid, txid and address_extension must be specified for Mixed addressing mode')

        elif self.addressing_mode == AddressMode.Mixed_29bits:
            if self.target_address is None or self.source_address is None or self.address_extension is None:
                raise ValueError(
                    'target_address, source_address and address_extension must be specified for Mixed addressing mode')

        if self.target_address is not None:
            if not isinstance(self.target_address, int):
                raise ValueError('target_address must be an integer')
            if self.target_address < 0 or self.target_address > 0xFF:
                raise ValueError('target_address must be an integer between 0x00 and 0xFF')

        if self.source_address is not None:
            if not isinstance(self.source_address, int):
                raise ValueError('source_address must be an integer')
            if self.source_address < 0 or self.source_address > 0xFF:
                raise ValueError('source_address must be an integer between 0x00 and 0xFF')

        if self.address_extension is not None:
            if not isinstance(self.address_extension, int):
                raise ValueError('source_address must be an integer')
            if self.address_extension < 0 or self.address_extension > 0xFF:
                raise ValueError('address_extension must be an integer between 0x00 and 0xFF')

        if self.tx_id is not None:
            if not isinstance(self.tx_id, int):
                raise ValueError('txid must be an integer')
            if self.tx_id < 0:
                raise ValueError('txid must be greater than 0')
            if not self.is_29bits:
                if self.tx_id > 0x7FF:
                    raise ValueError('txid must be smaller than 0x7FF for 11 bits identifier')

        if self.rx_id is not None:
            if not isinstance(self.rx_id, int):
                raise ValueError('rxid must be an integer')
            if self.rx_id < 0:
                raise ValueError('rxid must be greater than 0')
            if not self.is_29bits:
                if self.rx_id > 0x7FF:
                    raise ValueError('rxid must be smaller than 0x7FF for 11 bits identifier')

    def get_tx_arbitration_id(self, address_type=TargetAddressType.Physical):
        if address_type == TargetAddressType.Physical:
            return self.tx_arbitration_id_physical
        else:
            return self.tx_arbitration_id_functional

    def get_rx_arbitration_id(self, address_type=TargetAddressType.Physical):
        if address_type == TargetAddressType.Physical:
            return self.rx_arbitration_id_physical
        else:
            return self.rx_arbitration_id_functional

    def _get_tx_arbitration_id(self, address_type):
        if self.addressing_mode == AddressMode.Normal_11bits:
            return self.tx_id
        elif self.addressing_mode == AddressMode.Normal_29bits:
            return self.tx_id
        elif self.addressing_mode == AddressMode.NormalFixed_29bits:
            bits23_16 = 0xDA0000 if address_type == TargetAddressType.Physical else 0xDB0000
            return 0x18000000 | bits23_16 | (self.target_address << 8) | self.source_address
        elif self.addressing_mode == AddressMode.Extended_11bits:
            return self.tx_id
        elif self.addressing_mode == AddressMode.Extended_29bits:
            return self.tx_id
        elif self.addressing_mode == AddressMode.Mixed_11bits:
            return self.tx_id
        elif self.addressing_mode == AddressMode.Mixed_29bits:
            bits23_16 = 0xCE0000 if address_type == TargetAddressType.Physical else 0xCD0000
            return 0x18000000 | bits23_16 | (self.target_address << 8) | self.source_address

    def _get_rx_arbitration_id(self, address_type=TargetAddressType.Physical):
        if self.addressing_mode == AddressMode.Normal_11bits:
            return self.rx_id
        elif self.addressing_mode == AddressMode.Normal_29bits:
            return self.rx_id
        elif self.addressing_mode == AddressMode.NormalFixed_29bits:
            bits23_16 = 0xDA0000 if address_type == TargetAddressType.Physical else 0xDB0000
            return 0x18000000 | bits23_16 | (self.source_address << 8) | self.target_address
        elif self.addressing_mode == AddressMode.Extended_11bits:
            return self.rx_id
        elif self.addressing_mode == AddressMode.Extended_29bits:
            return self.rx_id
        elif self.addressing_mode == AddressMode.Mixed_11bits:
            return self.rx_id
        elif self.addressing_mode == AddressMode.Mixed_29bits:
            bits23_16 = 0xCE0000 if address_type == TargetAddressType.Physical else 0xCD0000
            return 0x18000000 | bits23_16 | (self.source_address << 8) | self.target_address

    def _is_for_me_normal(self, msg):
        if self.is_29bits == msg.is_extended_id:
            return msg.arbitration_id == self.rx_id
        return False

    def _is_for_me_extended(self, msg):
        if self.is_29bits == msg.is_extended_id:
            if msg.data is not None and len(msg.data) > 0:
                return msg.arbitration_id == self.rx_id and int(msg.data[0]) == self.source_address
        return False

    def _is_for_me_normal_fixed(self, msg):
        if self.is_29bits == msg.is_extended_id:
            return ((msg.arbitration_id >> 16) & 0xFF) in [218, 219] and (
                    msg.arbitration_id & 0xFF00) >> 8 == self.source_address and \
                   msg.arbitration_id & 0xFF == self.target_address
        return False

    def _is_for_me_mixed_11bits(self, msg):
        if self.is_29bits == msg.is_extended_id:
            if msg.data is not None and len(msg.data) > 0:
                return msg.arbitration_id == self.rx_id and int(msg.data[0]) == self.address_extension
        return False

    def _is_for_me_mixed_29bits(self, msg):
        if self.is_29bits == msg.is_extended_id:
            if msg.data is not None and len(msg.data) > 0:
                return ((msg.arbitration_id >> 16) & 0xFF) in [205, 206] and (
                        msg.arbitration_id & 0xFF00) >> 8 == self.source_address and \
                       msg.arbitration_id & 0xFF == self.target_address and int(
                    msg.data[0]) == self.address_extension
        return False

    def requires_extension_byte(self):
        return True if self.addressing_mode in (AddressMode.Extended_11bits, AddressMode.Extended_29bits,
                                                AddressMode.Mixed_11bits, AddressMode.Mixed_29bits) else False

    def get_tx_extension_byte(self):
        if self.addressing_mode in (AddressMode.Extended_11bits, AddressMode.Extended_29bits):
            return self.target_address
        if self.addressing_mode in (AddressMode.Mixed_11bits, AddressMode.Mixed_29bits):
            return self.address_extension

    def get_rx_extension_byte(self):
        if self.addressing_mode in (AddressMode.Extended_11bits, AddressMode.Extended_29bits):
            return self.source_address
        if self.addressing_mode in (AddressMode.Mixed_11bits, AddressMode.Mixed_29bits):
            return self.address_extension

    def get_content_str(self):
        val_dict = {}
        keys = ['target_address', 'source_address', 'address_extension', 'tx_id', 'rx_id']
        for key in keys:
            val = getattr(self, key)
            if val is not None:
                val_dict[key] = val
        vals_str = ', '.join(['%s:0x%02x' % (k, val_dict[k]) for k in val_dict])
        return '[%s - %s]' % (AddressingMode.get(self.addressing_mode), vals_str)

    def __repr__(self):
        return '<IsoTP Address %s at 0x%08x>' % (self.get_content_str(), id(self))
