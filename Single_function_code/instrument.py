import pyvisa
import time
import matplotlib.pyplot as plt
from datetime import datetime
import serial
import pandas as pd
import os
import numpy as np

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
        #self.name.baud_rate = 9600
        self.name.read_termination = '\n'
        self.name.write_termination = '\n'
        self.name.write("*CLS")
    #靜態操作模式選擇，VOLT、CURR、RES、POW
    def static_function(self, name):
        try:
            self.name.query(f":SOUR:FUNC {name}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    def static_CC_mode_curr_range(self, curr):
        try:
            self.name.query(f":SOUR:CURR:RANG {curr}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
        return curr
    #靜態操作CC模式電流數值設定
    def static_CC_mode_curr_set(self, curr):
        try:
            self.name.query(f":SOUR:CURR:LEV:IMM {curr}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
        return curr
    def input(self, num):
        try:
            self.name.query(f":SOUR:INP:STAT {num}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
        return num
    #觸發，使用BUS當作觸發源，要發送這指令觸發
    def trigger(self):
        try:
            self.name.query(":TRIGger")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #觸發源模式，BUS:remote trigger command；EXTernal:digital I/O；MANUal:TRAN key在前面板
    def trigger_source(self, source):
        try:
            self.name.query(f":TRIGger:SOURce {source}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #list功能的模式，CC、CV、CR、CP
    def list_mode(self, mode):
        try:
            self.name.query(f":SOUR:LIST:MODE {mode}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #list輸出範圍，CC有6、60A
    def list_range(self, range):
        try:
            self.name.query(f":SOUR:LIST:RANG {range}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #list循環次數，0~99999，0代表無限
    def list_count(self, num):
        try:
            self.name.query(f":SOUR:LIST:COUN {num}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #list的步驟數，從0開始算
    def list_step(self, num):
        try:
            self.name.query(f":SOUR:LIST:STEP {num}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #list步驟的數值設定，從0開始算
    def list_level(self, step, value):
        try:
            self.name.query(f":SOUR:LIST:LEV {step},{value}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #list步驟的時間長度，從0.00005~3600s
    def list_width(self, step, value):
        try:
            self.name.query(f":SOUR:LIST:WID {step},{value}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
    #list，CC模式的電流斜率
    def list_CC_slew(self, step, value):
        try:
            self.name.query(f":SOUR:LIST:SLEW {step},{value}")
        except pyvisa.errors.VisaIOError:
            self.name.write("*CLS")
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
    def M8_Y0_output(self, binary_data):
        self.name.write(binary_data)
        output_state = str(repr(self.name.readline()))
        return output_state
    def Y0_state_read(self, binary_data):
        self.name.write(binary_data)
        state = str(repr(self.name.readline()))
        return state
    def M2_ON(self, binary_data):
        self.name.write(binary_data)
        output_state = str(repr(self.name.readline()))
        return output_state
    def M2_state_read(self, binary_data):
        self.name.write(binary_data)
        M2_state = str(repr(self.name.readline()))
        return M2_state
    def M3_state_read(self, binary_data):
        self.name.write(binary_data)
        M3_state = str(repr(self.name.readline()))
        return M3_state
    def M5_state_read(self, binary_data):
        self.name.write(binary_data)
        M5_state = str(repr(self.name.readline()))
        return M5_state
    def M7_state_read(self, binary_data):
        self.name.write(binary_data)
        M7_state = str(repr(self.name.readline()))
        return M7_state
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
    def read_ALLscan_memory(self):
        data = []
        self.name.write("FETC?")
        data = self.name.read()
        return data
    def split_read_data(self, data):
        Data = []
        scan_data = data.split(",")
        for item in scan_data: 
            Data.append(item) #將每個資料填入串列內
        return Data
    def get_channel_data(self, data):
        #print(data)
        # 將數據按順序拆分成多個小列表，每個小列表包含8個元素
        data_chunks = [data[i:i+8] for i in range(0, len(data), 8)]
        # 分別提取通道101和111的數據
        channel_101 = [chunk for chunk in data_chunks if chunk[7] == '101']
        channel_102 = [chunk for chunk in data_chunks if chunk[7] == '102']
        channel_111 = [chunk for chunk in data_chunks if chunk[7] == '111']
        # 創建空的DataFrame
        df_101 = pd.DataFrame(channel_101, columns=['Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Channel'])
        df_102 = pd.DataFrame(channel_102, columns=['Temperature', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Channel'])
        df_111 = pd.DataFrame(channel_111, columns=['Current', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Channel'])
        # 將秒數轉換為整數
        df_101['Second'] = df_101['Second'].astype(float).astype(int)
        df_102['Second'] = df_102['Second'].astype(float).astype(int)
        df_111['Second'] = df_111['Second'].astype(float).astype(int)
        # 將時間數據轉換為datetime格式
        df_101['Timestamp'] = pd.to_datetime(df_101[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        df_102['Timestamp'] = pd.to_datetime(df_102[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        df_111['Timestamp'] = pd.to_datetime(df_111[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        # 將電壓數據從科學記號轉換為浮點數，並保留小數點後4位
        df_101['Voltage'] = df_101['Voltage'].astype(float).map("{:.6f}".format).astype(float)
        # 將溫度數據從科學記號轉換為浮點數，並保留小數點後4位
        df_102['Temperature'] = df_102['Temperature'].astype(float).map("{:.4f}".format).astype(float)
        # 將111 'Voltage' 從科學記號轉換為浮點數
        df_111['Current'] = df_111['Current'].astype(float).map("{:.6f}".format).astype(float)
        df_111['Current'] = df_111['Current'].apply(lambda x: abs(x) if x < 0 else x)
        # 將 'Voltage' 欄位的值除以 0.001 轉換為電流數值，存入 'Current'
        df_111['Current'] = (df_111['Current'] * 1000).round(6)
        df_101 = df_101[['Channel', 'Timestamp', 'Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']]
        df_102 = df_102[['Channel', 'Timestamp', 'Temperature', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']]
        df_111 = df_111[['Channel', 'Timestamp', 'Current', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']]
        # 計算從第一個數據點到最後一個數據點的時間跨度
        #total_time_elapsed = df_101['Timestamp'].iloc[-1] - df_101['Timestamp'].iloc[0]
        return df_101, df_102, df_111
    def real_time_get_channel_data(self):
        self.name.write("DATA:REMOVE? 1") #讀取一筆記憶體資料，並清除
        return self.name.read()
    def data_point(self):
        self.name.write("DATA:POINTS?") #回傳目前保存在掃描記憶體中的數據總數
        return int(self.name.read())
class LCR:
    def __init__(self, resource, name):
        self.resource = f"{resource}"
        self.name = rm.open_resource(f"{self.resource}")
        self.name.write("*CLS")
        self.name.write("*RST")
    def timeout(self):
        self.name.timeout = 3600000
    def measure_config(self,CONT_trig, trig_sour, CONCurrent, speed, average, aver_count = 1, measure_range = 1):
            self.name.write(f":INIT:CONT {CONT_trig}; :TRIG:SOUR {trig_sour}; *WAI; :SENSe:FUNCtion:CONCurrent {CONCurrent}; :APER {speed}; *WAI; :AVER {average}; :AVER:COUN {aver_count}; :FRES:RANG:AUTO {measure_range}")
            """
            CONT_trig:連續觸發(ON / OFF)
            trig_sour:觸發源(INTernal|MANual|EXTernal|BUS)
            CONCurrent:多參數(ON / OFF)
            speed:量測速度(RAP|SHOR|MED|LONG|VSLO)
            average:平均(ON / OFF)
            aver_count:平均筆數(預設1筆)
            *WAI:確保前面指令執行完
            measure_range:量測範圍(ON / OFF)

            """
    def measure_parameter(self, CALC1, CALC2):
        self.name.write(f":CALC1:FORM {CALC1}; :CALC2:FORM {CALC2}")
        """
        CALC1:首要參數(Z|Y|R|RP|RS|G|C|CP|CS|L|LP|LS|REAL|MLINear)
        CALC2:次要參數(Q|D|PHASe|X|B|RS|RP|G|LP|RDC|IMAGinary|REAL)
        """
    def measure_source(self, source, number, CV_CC_OnOF):
        self.name.write(f":SOUR:{source} {number}")  
        self.name.write(f":SOUR:{source}:ALC {CV_CC_OnOF}")
        """
        source:VOLT or CURR
        number:量測level
        CV_CC_OnOF:CCCV模式是否開啟(1/0)
        """
    def measure_freq(self, frequency):
        self.name.write(f":SOUR:FREQ {frequency}")
        self.name.write(":SOUR:FREQ?")
        frequency = self.name.read()
        """
        frequency:量測頻率
        """
        return frequency
    def freq_range(self, freq_min, freq_max, points_num):
        frequencies = np.logspace(freq_min, freq_max, num = points_num)
        """
        freq_min:最低頻率
        freq_max:最高頻率
        points_num:量測點數
        """
        return frequencies
    def start_measure(self):
        self.name.write(":INIT; :TRIG:DEL 1")
        self.name.write("*TRG")
        result = self.name.query(":FETCh?")
        return result
    def stop_measure(self):
        self.name.write(":ABOR")
    def close(self):
        self.name.close()
rm = pyvisa.ResourceManager()
print(rm.list_resources()) #列出可用資源
print(rm) #輸出Visa庫在電腦的位置
