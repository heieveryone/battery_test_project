import instrument
import time

PDS20_36A = instrument.power_supply("ASRL5::INSTR", "PDS20")
volt, curr = PDS20_36A.output_Set(8.4, 0.1)

PSU_output = PDS20_36A.output(1)
time.sleep(5)

volt, curr = PDS20_36A.output_Set(5, 0.1)
time.sleep(5)
PSU_output = PDS20_36A.output(0)
