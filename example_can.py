from vector_can import VectorCanBus
from vector_can.utils_can import CanMessage


bus = VectorCanBus(channel=0, app_name='Contest', receive_own_messages=True)
print(bus)
msg = CanMessage(arbitration_id=0xEE, data=[0, 0x3f, 0, 1, 3, 1, 4, 1], is_extended_id=False)
print(msg)


bus.send(msg)
print(f"Message sent on {bus.channel_info}")
x = bus.receive(timeout=10)
print("################### received message ###################")
print(x)
print("################### Comparision #############")
print(msg == x)
print("done")
bus.shutdown()
