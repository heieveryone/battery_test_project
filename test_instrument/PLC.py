import sys
import os
instrument_module_path = 'C:/Users/Acer/battery_test_project/instrument.py'
if instrument_module_path not in sys.path:
    sys.path.append(instrument_module_path)

import instrument
import time


DVP_12SE = instrument.DVP_PLC('COM4', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
time.sleep(5)
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')

