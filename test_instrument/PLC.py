import instrument
import time
import sys

target_Y0_ON = str(b':01010101FC\r\n')
target_Y0_OFF = str(b':01010100FD\r\n')
target_M2_ON = str(b':01010103FA\r\n')
target_M2_OFF = str(b':01010102FB\r\n')
target_M3_ON = str(b':01010103FA\r\n')
target_M3_OFF = str(b':01010102FB\r\n')
target_M5_ON = str(b':01010105F8\r\n')
target_M5_OFF = str(b':01010104F9\r\n')

DVP_12SE = instrument.DVP_PLC('COM3', '12SE')
time.sleep(1) #要確保rs232命令被發出
Y0_ON = DVP_12SE.M8_Y0_output(b':01050808FF00EB\r\n')
#Y0_OFF = DVP_12SE.M8_Y0_output(b':010505000000F5\r\n')
Y0_state = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')
print(Y0_state)
time.sleep(1)

""" if Y0_state == str(b':01010100FD\r\n'):
    print("relay OFF discharge")
    M2_ON = DVP_12SE.M2_ON(b':01050802FF00F1\r\n')
    M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
    print(M2_state)
else:
    print("Wrong Relay state")
    sys.exit(1)

try:
    while Y0_state == target_Y0_OFF and M2_state == target_M2_ON:
            Y0_state = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')  # read Y0
            M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')  # read M2
            M3_state = DVP_12SE.M3_state_read(b':010108030001F2\r\n')  # read M3
            M5_state = DVP_12SE.M5_state_read(b':010108050001F0\r\n')  # read M5
            print(M3_state, M5_state)
            time.sleep(0.5)
            #M7_state = DVP_12SE.M7_state_read(b':010108070001EE\r\n')
            if M3_state == str(b':01010103FA\r\n'):
                print("discharge and under voltage")
                time.sleep(1)
                M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
                M2_tate = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
                print(M2_tate)
            
            if M5_state == str(b':01010105F8\r\n'):
                print("discharge and over voltage")
                time.sleep(5)
                M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
                M2_tate = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
                print(M2_tate)
            time.sleep(0.5)
except KeyboardInterrupt:
    print("Stopped polling.")
    M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
    M2_tate = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
    print(M2_tate)

if Y0_state == str(b':01010101FC\r\n'):
    print("relay ON charge")
    M2_ON = DVP_12SE.M2_ON(b':01050802FF00F1\r\n')
    M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
    print(M2_state)
else:
    print("Wrong Relay state")
    sys.exit(1)
try:
    while Y0_state == target_Y0 and M2_state == target_M2:
            Y0_state = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')  # read Y0
            M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')  # read M2
            M3_state = DVP_12SE.M3_state_read(b':010108030001F2\r\n')  # read M3
            M5_state = DVP_12SE.M5_state_read(b':010108050001F0\r\n')  # read M5
            print(M3_state, M5_state)
            #M7_state = DVP_12SE.M7_state_read(b':010108070001EE\r\n')
            
            if M3_state == str(b':01010103FA\r\n'):
                print("charge and over voltage")
                time.sleep(1)
                M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
                M2_tate = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
                print(M2_tate)
            
            if M5_state == str(b':01010105F8\r\n'):
                print("charge and under voltage")
                time.sleep(5)
                M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
                M2_tate = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
                print(M2_tate)

            time.sleep(0.5)
except KeyboardInterrupt:
    print("Stopped polling.")
    M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
    M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
    print(M2_state)
  
M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
print(M2_OFF)
State = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
print(State)
M2_ON = DVP_12SE.M2_ON(b':01050802FF00F1\r\n')
print(M2_ON)
State = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
print(State)
time.sleep(5)
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
Y0_state = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')
print(Y0_state)

M2_OFF = DVP_12SE.M2_ON(b':010508020000F0\r\n')
print(M2_OFF)
State = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
print(State)
M2_ON = DVP_12SE.M2_ON(b':01050802FF00F1\r\n')
print(M2_ON)
State = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
print(State)
M3 = DVP_12SE.M3_state_read(b':010108030001F2\r\n')
print(M3)
time.sleep(1)

M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
time.sleep(3)
state = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')
print(state)
time.sleep(3)
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
print(M1183_state, output_state)



if State == str(b':01050805FF00EE\r\n'):
    M2_ON = DVP_12SE.M2_ON(b':01050802FF00F1\r\n')
    M2_state = DVP_12SE.M2_state_read(b':010108020001F3\r\n')
    print(M2_state)
else:
    print("Wrong Relay state")
    sys.exit(1)
    
try:
    while State == str(b':01050805FF00EE\r\n'):
            y_states = DVP_12SE.Y0_state_read(b':010105000001F8\r\n')  # read Y0
            print("Y states:", y_states)
            time.sleep(1)
except KeyboardInterrupt:
    print("Stopped polling.") """
