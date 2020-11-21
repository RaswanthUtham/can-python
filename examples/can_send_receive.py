from can_comm import VectorCanBus
from can_comm.utils_can import CanMessage


bus = VectorCanBus(channel=0, app_name='Canoe', receive_own_messages=True)
print('########### Bus Details ###########')
print(bus)
msg = CanMessage(arbitration_id=0xEE, data=[0, 0x3f, 0, 1, 3, 1, 4, 1], is_extended_id=False)
print('############### Message ###########')
print(msg)

print('########### sending message ############')
bus.send(msg)
print(f"Message sent on {bus.channel_info}")

print('############### receiving message #############')
x = bus.receive(timeout=10)
print("################### received message ###################")
print(x)
print("################### Comparision #############")
print(msg == x)
print("done")

bus.shutdown()
