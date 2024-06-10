import pyvisa
import time
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import serial

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
    
rm = pyvisa.ResourceManager()
print(rm.list_resources()) #列出可用資源
print(rm) #輸出Visa庫在電腦的位置
"""
x = []
DAQ_970a = DAQ("USB0::0x2A8D::0x5101::MY58017225::INSTR", "970a")
DAQ_970a.channel_function("VOLT:DC", 10, 101)
DAQ_970a.channel_function("VOLT:DC", 10, 111)
DAQ_970a.channel_scan_config("(@101, 111)", 1, 0.035, 30)
time.sleep(5)
print(DAQ_970a.scan_start())
time.sleep(20)
DAQ_970a.scan_stop()
time.sleep(1)
a = DAQ_970a.read_scan_memory() #回傳是一個字串，裡面用逗號座分隔
a = a.split(",") #將每個逗號都分割成一個字串
print(a)
for item in a: 
    x.append(item) #將每個資料填入串列內
print(len(x))

# 將數據按順序拆分成多個小列表，每個小列表包含8個元素
data_chunks = [x[i:i+8] for i in range(0, len(x), 8)]

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

print(df_101)
print(df_111)
# 計算從第一個數據點到最後一個數據點的時間跨度
total_time_elapsed = df_101['Timestamp'].iloc[-1] - df_101['Timestamp'].iloc[0]
# 將 DataFrame 資料儲存為 CSV 檔案
df_101.to_csv('channel_101_data.csv', index=False)
df_111.to_csv('channel_111_data.csv', index=False)

# 繪製圖表
plt.figure(figsize=(12, 6))

plt.plot(total_time_101, df_101['Voltage'], label='Channel 101', marker='o')
plt.plot(total_time_111, df_111['Voltage'], label='Channel 111', marker='x')

plt.xlabel('Total Elapsed Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Voltage vs Time for Channels 101 and 111')
plt.legend()
plt.grid(True)
# 設置 y 軸範圍為 0 到 5V
plt.ylim(0, 5)

plt.show()
rm.close()
"""
"""
# 將資料分成101和111通道的電壓數據
voltage_101 = []
voltage_111 = []
timestamps_101 = []
timestamps_111 = []
#將101跟111通道的數據分開，每8個為一組
for i in range(0, len(x), 8):
    voltage = '{:.6f}'.format(float(x[i]))
    year = int(x[i + 1])
    month = int(x[i + 2])
    day = int(x[i + 3])
    hour = int(x[i + 4])
    minute = int(x[i + 5])
    second = float(x[i + 6])
    channel = int(x[i + 7])
    timestamp = datetime(year, month, day, hour, minute, int(second))
    if channel == 101:
        voltage_101.append(voltage)
        timestamps_101.append(timestamp)
    elif channel == 111:
        voltage_111.append(voltage)
        timestamps_111.append(timestamp)
print(timestamps_101)
print(timestamps_111)
# 繪製圖表
plt.figure(figsize=(10, 6))
plt.plot(timestamps_101, voltage_101, label='Channel 101')
plt.plot(timestamps_111, voltage_111, label='Channel 111')
plt.xlabel('Time')
plt.ylabel('Voltage')
plt.title('Voltage Data')
plt.legend()
plt.show()
"""
DVP_12SE = DVP_PLC('COM3', '12SE')
time.sleep(1) #要確保rs232命令被發出
M1183_state = DVP_12SE.M1183_output(b':01050C9F00004F\r\n')
output_state = DVP_12SE.Y0_output(b':01050500FF00F6\r\n')
time.sleep(0.1)
#指定儀器
my_instrument = rm.open_resource('USB0::0x2A8D::0x5101::MY58017225::0::INSTR', read_termination='\n')
#詢問儀器資料
print(my_instrument.query('*IDN?'))
#詢問DAQ第一個槽的插入卡型號，共三個槽
my_instrument.write("SYST:CTYPE? 1") 
print(my_instrument.read())
#清除記憶體及指令
my_instrument.write('*CLS')
#重置設定
my_instrument.write("*RST")
#設定掃描參數
scanIntervals = 1 #掃描間隔
numberScans = "INFinity" #掃描比數
channelDelay = 0.05 #每個通道延遲
dataPoint = 0 #儲存的數據數
scanlist = "(@101, 111)" #要掃描的通道
#配置通道功能
my_instrument.write('CONF:VOLT:DC 10, (@101)')
my_instrument.write('CONF:VOLT:DC 100mV, (@111)')
#配置要掃描的通道
my_instrument.write("ROUTE:SCAN " + scanlist) 
my_instrument.write("ROUTE:SCAN:SIZE?") #回傳掃描通道數
numberChannels = int(my_instrument.read()) + 1 #紀錄通道數
#配置要回傳的數據格式內容，DAQ每筆資料都會加上時間戳記、測量單位、通道號、警告狀態，並儲存在記憶體中
my_instrument.write("FORMAT:READING:CHAN ON") #啟用回傳通道資訊
my_instrument.write("FORMAT:READING:TIME:TYPE ABS") #配置為絕對時間戳記
my_instrument.write("FORMAT:READING:TIME ON") #啟用回傳時間
#配置通道繼電器delay時間
my_instrument.write("ROUT:CHAN:DELAY " + str(channelDelay) + "," + scanlist)
#觸發掃描配置
my_instrument.write("TRIG:COUNT " + str(numberScans)) #掃描次數
my_instrument.write("TRIG:SOUR TIMER") #觸發選擇配置
my_instrument.write("TRIG:TIMER " + str(scanIntervals)) #觸發每次掃描間隔
#啟動掃描並回傳時間戳記
my_instrument.write("INIT;:SYSTEM:TIME:SCAN?")   
print(my_instrument.read())

points = 0
while (points==0):
    my_instrument.write("DATA:POINTS?") #回傳目前保存在掃描記憶體中的數據總數
    points = int(my_instrument.read())
    print(points)

n = 0 #數據比數
while(1):
    time.sleep(1)
    my_instrument.write("DATA:REMOVE? 1") #讀取一筆記憶體資料，讀取後清除
    print (my_instrument.read())
    n += 1
    points = 0
    #wait for data
    if(points == 0):
        my_instrument.write("DATA:POINTS?") #請求記憶體內的數據數
        points = int(my_instrument.read())
    if n == 100:
        my_instrument.write("ABOR")
        break
    
output_state = DVP_12SE.Y0_output(b':010505000000F5\r\n')
my_instrument.close()
print('close instrument connection')


