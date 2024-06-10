import serial
import minimalmodbus
import time
from datetime import datetime

#PLC的類別
class DVP_PLC:
    #初始設置序列通訊
    def __init__(self, resource, name):
        self.resource = f"{resource}"
        self.name = serial.Serial(f"{self.resource}", 9600)
        self.name.bytesize = 7
        self.name.parity = serial.PARITY_EVEN
        self.name.stopbits = 1
        self.name.timeout = 0.03
    """改變M1183狀態 On(b':01050C9FFF0050\r\n')/Off(b':01050C9F00004F\r\n')，SE預設為ON，
    off為開啟特殊模組自動對應讀寫功能，對應D9900~
    """
    def M1183_output(self, binary_data):
        self.name.write(binary_data)
        M1183_state = str(repr(self.name.readline()))
        return M1183_state
    #Y0輸出_繼電器 On(b':01050500FF00F6\r\n')/Off(b':010505000000F5\r\n')
    def Y0_output(self, binary_data):
        self.name.write(binary_data)
        output_state = str(repr(self.name.readline()))
        return output_state
    #讀D9900(XA的V1+數值)(b':0103A6AC0001A9\r\n')
    def read_XA_v1(self, binary_data):
        self.name.write(binary_data)
        return_message = str(repr(self.name.readline())) #將二進制訊息轉成字串
        return return_message
    #將D9900回傳的訊息取出data，將data從16進制轉換成10進制，再轉換成類比數值
    def decode_XA_v1(self, message):
        return_message = message
        hex_number = return_message[9:-7] #取出回傳訊息的電壓ADC數位data
        decimal_number = int(hex_number, 16) #將數位16進制data換成十進制
        voltage = decimal_number * 0.005 #將數位data轉為類比電壓，解析度為5mV
        if voltage == 327.675:
            voltage = 0
        return voltage
    
        
        
DVP_12SE = DVP_PLC('COM3', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
print(M1183_state, type(M1183_state), len(M1183_state))
time.sleep(1)
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
print(output_state, type(output_state), len(output_state))
Y0_ON = b':01050C9F00004F\r\n'
M1183_OFF = "b':01050500FF00F6\r\n'"
print(str(Y0_ON))
if M1183_state == str(b':01050C9F00004F\r\n') and output_state == str(b':01050500FF00F6\r\n'):
    print("PSU ON")
    while 1:
        DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n')
        voltage = DVP_12SE.decode_XA_v1(DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n'))
        print(voltage)
        if voltage >= 4.2:
            print("cut off voltage")
            break
        time.sleep(0.01)
elif M1183_state != str(b':01050C9F00004F\r\n') or output_state != str(b':01050500FF00F6\r\n'):
    print("fail to turn on")
time.sleep(10)
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
"""
for i in range(1, 300):
    DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n')
    print(DVP_12SE.decode_XA_v1(DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n')))
    time.sleep(0.01)
print(DVP_12SE.Y0_output(b':010505000000F5\r\n'))

a = 0
for i in range(1, 100):
    a += 1
time.sleep(1)
DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
for i in range(1, 100):
    DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n')
    print(DVP_12SE.decode_XA_v1(DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n')))
    time.sleep(0.3)
DVP_12SE.Y0_output(b':010505000000F5\r\n')
"""
"""
DVP_12SE = serial.Serial('COM3', 9600 )
DVP_12SE.bytesize = 7
DVP_12SE.parity = serial.PARITY_EVEN
DVP_12SE.stopbits = 1
DVP_12SE.timeout  = 0.03
print(DVP_12SE)
#檢查M1183 On/Off
DVP_12SE.write(b':01010C9F000152\r\n')
print(repr(DVP_12SE.readline()))
#改變M1183狀態 On(':01050C9FFF0050\r\n')/Off(':01050C9F00004F\r\n')
DVP_12SE.write(b':01050C9F00004F\r\n')
print(repr(DVP_12SE.readline()))
#檢查M1183 On/Off
DVP_12SE.write(b':01010C9F000152\r\n')
M1183_State = DVP_12SE.readline()
print(repr(M1183_State))
for i in range(1,10):
    DVP_12SE.write(b':0103A6AC0001A9\r\n')
    x = str(repr(DVP_12SE.readline()))
    print(x, len(x))
    time.sleep(1)
#Y0輸出_繼電器 On(':01050500FF00F6\r\n')/Off(':010505000000F5\r\n')
DVP_12SE.write(b':01050500FF00F6\r\n')
Y0_output = DVP_12SE.readline()
print(repr(Y0_output))


#讀D1140狀態，會讓ERROR燈亮
#DVP_12SE.write(b':01031474000173\r\n')
#print(repr(DVP_12SE.readline()))

#DVP_12SE.write(b':010340C8000FF4\r\n')
#print(DVP_12SE.readline())
#讀D9900(XA的V1+)b':0103A6AC0001A9\r\n'
while(1):
    current_time = datetime.now()
    DVP_12SE.write(b':0103A6AC0001A9\r\n')
    print(repr(DVP_12SE.readline()), current_time)
    #print(str(DVP_12SE.readline()))
    time.sleep(1)
    

#讀D3(XA的V1+)
#DVP_12SE.write(b':010310030001E8\r\n')
#print(repr(DVP_12SE.readline()))
"""