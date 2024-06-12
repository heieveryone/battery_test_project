import instrument
import time

PDS20_36A = instrument.power_supply("ASRL3::INSTR", "PDS20")
volt, curr = PDS20_36A.output_Set(8.4, 0.1)
time.sleep(1)
DVP_12SE = instrument.DVP_PLC('COM4', '12SE')
time.sleep(1) #要確保rs232命令被發出
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
PSU_output = PDS20_36A.output(1)
time.sleep(5)

volt, curr = PDS20_36A.output_Set(5, 0.1)
time.sleep(5)
PSU_output = PDS20_36A.output(0)
time.sleep(1)
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
