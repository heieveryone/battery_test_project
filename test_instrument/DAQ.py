import instrument
import time

DAQ_970a = instrument.DAQ("USB0::0x2A8D::0x5101::MY58017225::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("TEMP:TCouple", 'J', 102)
DAQ_970a.channel_function("VOLT:DC", "100mV", 111)
DAQ_970a.channel_scan_config("(@101, 102, 111)", 1, 0.035)
time.sleep(1)
PDS20_36A = instrument.power_supply("ASRL3::INSTR", "PDS20")
volt, curr = PDS20_36A.output_Set(8.4, 0.1)
time.sleep(1)
DVP_12SE = instrument.DVP_PLC('COM4', '12SE')
time.sleep(1) #要確保rs232命令被發出
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
PSU_output = PDS20_36A.output(1)
print(DAQ_970a.scan_start())
time.sleep(10)
DAQ_970a.scan_stop()
time.sleep(0.1)
PSU_output = PDS20_36A.output(0)
time.sleep(1)
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
path = "data.txt"
f = open(path, 'w')
print(DAQ_970a.read_ALLscan_memory(), file = f)


