import pyvisa
import time


rm = pyvisa.ResourceManager()
usb_resource = "USB0::0x0D4A::0x0016::9429358::INSTR"
inst = rm.open_resource(usb_resource)
inst.write(":SYST:ERR?")
error = inst.read()
print(error)

inst.close()