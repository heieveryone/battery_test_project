import pyvisa
import time
import matplotlib.pyplot as plt
from datetime import datetime
import serial
import pandas as pd
import os

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
        self.name.write("CCPRIO 1") #CC優先模式(開啟為CC mode)
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
        return volt, curr
    #輸出函數，num = 1(on);num = 0(off)
    def output(self, num):
        self.name.write("*CLS")
        self.name.write(f"OUTPUT {num}")
        self.name.write("*CLS")
        return num
            
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
            
#DAQ類別
class DAQ:
    #初始化設置
    def __init__(self, resource, name):
        self.resource = f"{resource}" 
        self.name = rm.open_resource(f"{self.resource}") #DAQ的資源口
        self.name.read_termination = '\n' #結尾符號配置
        self.name.write("*CLS")
        self.name.write("*RST")
    #配置通道功能    
    def channel_function(self, func, range, channel): 
        self.name.write(f"CONF:" + func + f" {range}, (@{channel})")
    
    def channel_scan_config(self, scanlist, scanIntervals, channelDelay, numberScans = "INFinity"):
        #配置要掃描的通道
        self.name.write("ROUTE:SCAN " + scanlist) 
        self.name.write("ROUTE:SCAN:SIZE?") #回傳掃描通道數
        numberChannels = int(self.name.read()) + 1 #紀錄通道數
        #配置要回傳的數據格式內容，DAQ每筆資料都會加上時間戳記、測量單位、通道號、警告狀態，並儲存在記憶體中
        self.name.write("FORMAT:READING:CHAN ON") #啟用回傳通道資訊
        self.name.write("FORMAT:READING:TIME:TYPE ABS") #配置為絕對時間戳記
        self.name.write("FORMAT:READING:TIME ON") #啟用回傳時間
        self.name.write("ROUT:CHAN:DELAY " + str(channelDelay) + "," + scanlist) #配置通道繼電器delay時間
        self.name.write("TRIG:COUNT " + str(numberScans)) #掃描次數
        self.name.write("TRIG:SOUR TIMER") #觸發選擇配置
        self.name.write("TRIG:TIMER " + str(scanIntervals)) #觸發每次掃描間隔
        return numberChannels
    def scan_start(self):
        self.name.write("INIT;:SYSTEM:TIME:SCAN?")
        return self.name.read()
    def scan_stop(self):
        self.name.write("ABOR")
    def read_scan_memory(self):
        data = []
        self.name.write("FETC?")
        scan_data = self.name.read()
        scan_data = scan_data.split(",")
        for item in scan_data: 
            data.append(item) #將每個資料填入串列內
        return data
    def get_channel_data(self):
        data = self.read_scan_memory()
        # 將數據按順序拆分成多個小列表，每個小列表包含8個元素
        data_chunks = [data[i:i+8] for i in range(0, len(data), 8)]
        # 分別提取通道101和111的數據
        channel_101 = [chunk for chunk in data_chunks if chunk[7] == '101']
        channel_111 = [chunk for chunk in data_chunks if chunk[7] == '111']
        # 創建空的DataFrame
        df_101 = pd.DataFrame(channel_101, columns=['Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Channel'])
        df_111 = pd.DataFrame(channel_111, columns=['Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Channel'])
        # 將秒數轉換為整數
        df_101['Second'] = df_101['Second'].astype(float).astype(int)
        df_111['Second'] = df_111['Second'].astype(float).astype(int)
        # 將時間數據轉換為datetime格式
        df_101['Timestamp'] = pd.to_datetime(df_101[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        df_111['Timestamp'] = pd.to_datetime(df_111[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        # 計算總花費時間
        total_time_101 = (df_101['Timestamp'] - df_101['Timestamp'].iloc[0]).dt.total_seconds()
        total_time_111 = (df_111['Timestamp'] - df_111['Timestamp'].iloc[0]).dt.total_seconds()
        # 將電壓數據從科學記號轉換為浮點數，並保留小數點後4位
        df_101['Voltage'] = df_101['Voltage'].astype(float).map("{:.6f}".format).astype(float)
        df_111['Voltage'] = df_111['Voltage'].astype(float).map("{:.6f}".format).astype(float)
        df_101 = df_101[['Channel', 'Timestamp', 'Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']]
        df_111 = df_111[['Channel', 'Timestamp', 'Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']]
        # 計算從第一個數據點到最後一個數據點的時間跨度
        total_time_elapsed = df_101['Timestamp'].iloc[-1] - df_101['Timestamp'].iloc[0]
        # 將 DataFrame 資料儲存為 CSV 檔案
        df_101.to_csv('channel_101_data.csv', index=False)
        df_111.to_csv('channel_111_data.csv', index=False)
        
        return df_101, df_111, total_time_elapsed, total_time_101, total_time_111

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

def save_dataframe_to_csv_with_incremented_filename(df, path):
    # 指定要保存的目錄
    directory = f"{path}"
    
    # 獲取目錄下所有已保存的 CSV 檔案
    existing_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
    
    # 計算現有檔案數量，並為新檔案生成檔名
    new_filename = str(len(existing_files) + 1) + ".csv"
    filepath = os.path.join(directory, new_filename)
    
    # 將 DataFrame 寫入 CSV 檔案
    df.to_csv(filepath, index=False)
    
    print(f"Saved DataFrame to {filepath}")

rm = pyvisa.ResourceManager()
print(rm.list_resources()) #列出可用資源
print(rm) #輸出Visa庫在電腦的位置


#PDS20-36A
PDS20_36A = power_supply("ASRL6::INSTR", "PDS20")
volt, curr = PDS20_36A.output_Set(4.2, 0.02)
time.sleep(1)
DAQ_970a = DAQ("USB0::0x2A8D::0x5101::MY58017225::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("VOLT:DC", 10, 111)
DAQ_970a.channel_scan_config("(@101, 111)", 1, 0.035)
time.sleep(1)
DVP_12SE = DVP_PLC('COM3', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
time.sleep(5) #要找到sleep取代方法
PLC_voltage_data = []
if M1183_state == str(b':01050C9F00004F\r\n') and output_state == str(b':01050500FF00F6\r\n'):
    PSU_output = PDS20_36A.output(1)
    start_time = time.time()
    print(DAQ_970a.scan_start())
    while PSU_output == 1:
        DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n')
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        voltage = DVP_12SE.decode_XA_v1(DVP_12SE.read_XA_v1(b':0103A6AC0001A9\r\n'))
        PLC_voltage_data.append([current_time, voltage])
        if curr == 0.02 and 4.19 <= voltage <= 4.205:
            volt, curr = PDS20_36A.output_Set(4.2, 0.01)
        if curr == 0.01 and 4.195 <= voltage <= 4.205:
            print("cut off voltage")
            break
        print(voltage)
        time.sleep(0.01)
    PDS20_36A.output(0)
    time.sleep(0.01)
    DAQ_970a.scan_stop()
elif M1183_state != str(b':01050C9F00004F\r\n') or output_state != str(b':01050500FF00F6\r\n'):
    print("fail to turn on")
time.sleep(10)
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
channel_101_data, channel_111_data, total_time, channel_101_time, channel_111_time = DAQ_970a.get_channel_data()
PLC_voltage = pd.DataFrame(PLC_voltage_data, columns=['Timestamp', 'Voltage'])
save_dataframe_to_csv_with_incremented_filename(channel_101_data, "C:/Users/zx511/hello/csv/channel_101")
save_dataframe_to_csv_with_incremented_filename(channel_111_data, "C:/Users/zx511/hello/csv/channel_111")
save_dataframe_to_csv_with_incremented_filename(PLC_voltage, "C:/Users/zx511/hello/csv/PLC_data")

# 將Timestamp轉換為Datetime類型
PLC_voltage['Timestamp'] = pd.to_datetime(PLC_voltage['Timestamp'])

plt.figure(figsize=(15, 6))
# 繪製第一張圖
plt.subplot(4, 1, 1)
plt.plot(channel_101_data['Timestamp'], channel_101_data['Voltage'], label='Channel 101', marker='o')
plt.ylabel('Voltage (V)')
plt.title('Channel 101 Voltage vs Time')
plt.ylim(0, 5)
plt.grid(True)

# 繪製第二張圖
plt.subplot(4, 1, 2)
plt.plot(channel_111_data['Timestamp'], channel_111_data['Voltage'], label='Channel 111', marker='x')
plt.ylabel('Voltage (V)')
plt.title('Channel 111 Voltage vs Time')
plt.ylim(0, 5)
plt.grid(True)

# 繪製第三張圖
plt.subplot(4, 1, 3)
plt.plot(PLC_voltage['Timestamp'], PLC_voltage['Voltage'], label='PLC data', marker='o')
plt.xlabel('Total Time (s)')
plt.ylabel('Voltage (V)')
plt.title('PLC data vs time')
plt.ylim(0, 5)
plt.legend()
plt.grid(True)

plt.subplot(4, 1, 4)
plt.plot(channel_101_data.index, channel_101_data['Voltage'], label='Channel 101', marker='o')
plt.plot(channel_111_data.index, channel_111_data['Voltage'], label='Channel 111', marker='x')
plt.plot(PLC_voltage.index, PLC_voltage['Voltage'], label='PLC data', marker='^')
plt.xlabel('Total Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Channels 101, 111 and PLC Voltage vs Time')
plt.ylim(0, 5)
plt.legend()
plt.grid(True)
# 調整子圖間的間隔
plt.tight_layout(pad=3.0)
plt.show()