import instrument
import time

Rigol_load = instrument.dc_electronic_load('USB0::0x1AB1::0x0E11::DL3A260500107::INSTR', 'DL3021')
Rigol_load.static_function('CURR')
curr = Rigol_load.static_CC_mode_curr_set(1)
time.sleep(1)

