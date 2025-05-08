import os
import pandas as pd
def get_channel_data(data):
        #print(data)
        # 將數據按順序拆分成多個小列表，每個小列表包含8個元素
        data_chunks = [data[i:i+8] for i in range(0, len(data), 8)]
        # 分別提取通道101和111的數據
        #channel_101 = [chunk for chunk in data_chunks if chunk[7] == '101']
        channel_102 = [chunk for chunk in data_chunks if chunk[7] == '102']
        #channel_111 = [chunk for chunk in data_chunks if chunk[7] == '111']
        # 創建空的DataFrame
        #df_101 = pd.DataFrame(channel_101, columns=['Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Channel'])
        df_102 = pd.DataFrame(channel_102, columns=['Temperature', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Channel'])
        #df_111 = pd.DataFrame(channel_111, columns=['Current', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second', 'Channel'])
        # 將秒數轉換為整數
        #df_101['Second'] = df_101['Second'].astype(float).astype(int)
        df_102['Second'] = df_102['Second'].astype(float).astype(int)
        #df_111['Second'] = df_111['Second'].astype(float).astype(int)
        # 將時間數據轉換為datetime格式
        #df_101['Timestamp'] = pd.to_datetime(df_101[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        df_102['Timestamp'] = pd.to_datetime(df_102[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        #df_111['Timestamp'] = pd.to_datetime(df_111[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        # 將電壓數據從科學記號轉換為浮點數，並保留小數點後4位
        #df_101['Voltage'] = df_101['Voltage'].astype(float).map("{:.6f}".format).astype(float)
        # 將溫度數據從科學記號轉換為浮點數，並保留小數點後4位
        df_102['Temperature'] = df_102['Temperature'].astype(float).map("{:.4f}".format).astype(float)
        # 將111 'Voltage' 從科學記號轉換為浮點數
        #df_111['Current'] = df_111['Current'].astype(float).map("{:.6f}".format).astype(float)
        #df_111['Current'] = df_111['Current'].apply(lambda x: abs(x) if x < 0 else x)
        # 將 'Voltage' 欄位的值除以 0.001 轉換為電流數值，存入 'Current'
        #df_111['Current'] = (df_111['Current'] * 1000).round(6)
        #df_101 = df_101[['Channel', 'Timestamp', 'Voltage', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']]
        df_102 = df_102[['Channel', 'Timestamp', 'Temperature', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']]
        #df_111 = df_111[['Channel', 'Timestamp', 'Current', 'Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']]
        # 計算從第一個數據點到最後一個數據點的時間跨度
        #total_time_elapsed = df_101['Timestamp'].iloc[-1] - df_101['Timestamp'].iloc[0]
        return df_102
    
def spilt_read_data(data):
    Data = []
    scan_data = data.split(",")
    for item in scan_data: 
        Data.append(item) #將每個資料填入串列內
    return Data

path = 'temp.txt'
f = open(path, 'r')
print(f.read())
with open(path, 'r') as f:
    data = f.read()
    
data = spilt_read_data(data)
df_102 = get_channel_data(data)

print(df_102)
f.close()