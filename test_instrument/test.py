import pyvisa
import time
import threading
import serial
import pandas as pd

#PDS20_36A電源供應器類別
class power_supply:
    #初始化設置，配置RS232
    def __init__(self, resource, name): #resource資源口輸入
        self.resource = f"{resource}" 
        self.name = rm.open_resource(f"{self.resource}") #電供的資源口
        self.name.baud_rate = 9600 #rs232鮑率
        self.name.read_termination = '\n' #rs232結尾符號配置
        self.name.write_termination = '\n' #rs232結尾符號配置
        self.name.write("*CLS") #清除buffer
        #self.name.write("CCPRIO 1") #CC優先模式(開啟為CC mode)
        self.name.write("*CLS")
    #設置電壓電流數值
    def output_Set(self, volt, curr):
        try:
            self.name.query(f"VOLT {volt}")
        except pyvisa.errors.VisaIOError:
            self.name.write('*CLS')
        try:
            self.name.query(f"AMP {curr}")
        except pyvisa.errors.VisaIOError:
            self.name.write('*CLS')
    #輸出函數，num = 1(on);num = 0(off)
    def output(self, num):
        self.name.write("*CLS")
        self.name.write(f"OUTPUT {num}")
        self.name.write("*CLS")
            
#Rigol DL3021電子負載類別
class dc_electronic_load:
    #電子負載初始配置
    def __init__(self, resource, name):
        self.resource = f"{resource}"
        self.name = rm.open_resource(f"{self.resource}")
        self.name.baud_rate = 9600
        self.name.read_termination = '\n'
        self.name.write_termination = '\n'
        self.name.write("*CLS")
    #靜態操作模式選擇，VOLT、CURR、RES、POW
    def static_function(self, name):
        try:
            self.name.query(f":SOUR:FUNC {name}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #靜態操作CC模式電流設定
    def static_CC_mode_curr_set(self, curr):
        try:
            self.name.query(f":SOUR:CURR:LEV:IMM {curr}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
            
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
               
visaLibrary_path = "C:/Windows/System32/visa32.dll"
rm = pyvisa.ResourceManager(visaLibrary_path)
print(rm.list_resources('?*')) #列出所有資源口
print(rm) #輸出visa資源庫的位置
"""
Rigol_DL3021 = dc_electronic_load("ASRL14::INSTR", "DL3021")
Rigol_DL3021.static_function(name = "CURR")
Rigol_DL3021.static_CC_mode_curr_set(2)

#Rigol.query("*IDN?")
#Rigol.query(":MEAS:VOLT?")
#Rigol.write("*CLS\n")
#Rigol.query(":FETCh:VOLTage:MIN?\n")
"""
#PDS20-36A
PDS20_36A = power_supply("ASRL6::INSTR", "PDS20")
PDS20_36A.output_Set(4.1, 0.1)

DVP_12SE = DVP_PLC('COM3', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
time.sleep(5) #要找到sleep取代方法
voltage_data = []
if M1183_state == str(b':01050C9F00004F\r\n') and output_state == str(b':01050500FF00F6\r\n'):
    PDS20_36A.output(1)
    start_time = time.time()
    while 1:
        DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n')
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        voltage = DVP_12SE.decode_XA_v1(DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n'))
        voltage_data.append([current_time, voltage])
        if 4.005 <= voltage <= 4.1:
            PDS20_36A.output_Set(4.2, 0.01)
            print(voltage)
        if 4.195 <= voltage <= 4.205:
            print("cut off voltage")
            break
        print(voltage)
        time.sleep(0.01)
    PDS20_36A.output(0)
elif M1183_state != str(b':01050C9F00004F\r\n') or output_state != str(b':01050500FF00F6\r\n'):
    print("fail to turn on")

output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
time.sleep(10)
df = pd.DataFrame(voltage_data, columns=['Timestamp', 'Voltage'])
print(df)
df.to_csv('PLC_voltage_data.csv', index=False)
import matplotlib.pyplot as plt

# 將Timestamp轉換為Datetime類型
df['Timestamp'] = pd.to_datetime(df['Timestamp'])

# 畫圖
plt.figure(figsize=(10, 6))
plt.plot(df['Timestamp'], df['Voltage'], marker='o')
plt.xlabel('Time')
plt.ylabel('Voltage (V)')
plt.title('Voltage vs Time')
plt.grid(True)
plt.show()
"""
threading 多執行褚
PSU_ON = threading.Timer(5, PDS20_36A.output(1))
PSU_OFF = threading.Timer(15, PDS20_36A.output(0))

PSU_ON.start()
PSU_OFF.start()

print("Timer started")

PSU_ON.join()
PSU_OFF.join()

print("Timer finished")
"""
"""
#my_instrument.read()
#my_instrument.write('AMP 0.01')
my_instrument.write('OUTPUT 1')
time.sleep(10)
my_instrument.write('OUTPUT 0')





#
#my_instrument.read_bytes(1)

my_instrument.read_termination = '\n'
my_instrument.write_termination = '\n'

"""

#sourcemeter 2400
#my_instrument = rm.open_resource('GPIB0::2::INSTR')
#print(my_instrument.query('*IDN?'))
#my_instrument.write(':SOUR:FUNC VOLT')