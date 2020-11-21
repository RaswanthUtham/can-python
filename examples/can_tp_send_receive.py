import logging
import time
import threading
from can_comm import VectorCanBus, Address, CanStack
from can_comm.utils_can.cantp.addresses import AddressMode


def my_error_handler(error):
    logging.warning('IsoTp error happened : %s - %s' % (error.__class__.__name__, str(error)))


def receive_message():
    global stack
    t1_ = time.time()
    print("inside receive")
    while time.time() - t1_ < 5:
        stack.process()
        if stack.is_available():
            payload = stack.receive()
            print(payload)
            break
        time.sleep(stack.sleep_time())


bus = VectorCanBus(channel=0, bitrate=500000, app_name='Contest', receive_own_messages=False)
addr = Address(AddressMode.Normal_11bits, rx_id=0x22, tx_id=0x3e)
t1 = threading.Thread(target=receive_message)
stack = CanStack(bus, address=addr, error_handler=my_error_handler, params={'tx_padding': 0x00})
t1.start()
stack.send(b'Hello, this is a long payload sent in small chunks abcdef')
t1.join()

print("Payload transmission done.")
bus.shutdown()
