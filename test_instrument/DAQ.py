import instrument
import time

DAQ_970a = instrument.DAQ("USB0::0x2A8D::0x5101::MY58017225::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("VOLT:DC", "100mV", 111)
DAQ_970a.channel_scan_config("(@101, 111)", 1, 0.035)
time.sleep(1)

print(DAQ_970a.scan_start())
time.sleep(5)
DAQ_970a.scan_stop()