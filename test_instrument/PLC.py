import instrument
import time


DVP_12SE = instrument.DVP_PLC('COM4', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
print(M1183_state, output_state)
time.sleep(10)
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
print(M1183_state, output_state)
