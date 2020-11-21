from can_comm.utils_can.dbc_reader import DbcParser
from can_comm.utils_can.dbc_value_calc import get_physical_value

# Read dbc data
file_path = ["../files/motohawk.dbc", "../files/Sample.dbc", "../files/multiplex_2.dbc"]
db = DbcParser(file_path)
print(db.message['3221225472.name'],
      db.message['DM29.id'],
      # message['DM30.signals'],
      db.signal['FailureModeIdentifier1.message'],
      db.signal['SPN1High.bit_length'])

print("signals in a Message: ", db.get_signals('DM30'))
print("signalName.message: ", db.signal['TestLimitMinimum.message'])
print('signalName.bit_length:', db.signal['TestLimitMinimum.bit_length'])
print("signalName.little_endian: ", db.signal['TestLimitMinimum.little_endian'])
print("signalName.all: ", db.signal['PMNTEControlAreaStatus.all'])

# calculate value
dbc_raw_data = [0x48, 0xCE, 0x3e, 0x80, 0x14, 0xff, 0xff, 0xff]  # raw data can_comm be taken from log file
dbc_raw_data = bytearray(dbc_raw_data)

lsb = db.signal['AverageRadius.start_bit']
bit_length = db.signal['AverageRadius.bit_length']
scale = db.signal['AverageRadius.scale']
offset = db.signal['AverageRadius.offset']
little_endian = db.signal['AverageRadius.little_endian']
signed = db.signal['AverageRadius.signed']

val = get_physical_value(lsb, bit_length, dbc_raw_data, scale, offset, signed, little_endian)
print("physical value of AverageRadius: ", val)
