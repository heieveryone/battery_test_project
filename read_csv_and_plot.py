import pandas as pd
import os
import glob
import matplotlib.pyplot as plt
import re

def get_latest_csv_file(directory):
    """獲取指定目錄中最新的 CSV 檔案"""
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    latest_file = max(csv_files, key=os.path.getctime)
    return latest_file

def extract_first_number(file_name):
    """從檔案名中提取第一個數字"""
    match = re.search(r'\d+', file_name)
    if match:
        return int(match.group(0))
    else:
        return None
def get_file_type(directory):
    """根據目錄路徑判斷其類型"""
    if 'current' in directory:
        return 'current'
    elif 'voltage' in directory:
        return 'voltage'
    else:
        return None
    
def read_and_plot_csv(file_path):
    """讀取 CSV 檔案並繪製數據"""
    file_name = os.path.basename(file_path)
    first_number = extract_first_number(file_name)
    file_type = get_file_type(charge_current_csv_path)
    if first_number is not None:
        title = f'cycle {first_number} charge data'
    else:
        title = '充電數據'
    df = pd.read_csv(file_path)
    
    # 假設 DataFrame 有 'Timestamp' 和 'Voltage' 列
    # 計算總花費時間（索引順序）
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    #df['Elapsed Time'] = (df.index - df.index[0])
    total_time_elapsed = df['Timestamp'].iloc[-1] - df['Timestamp'].iloc[0]
    df['Total Time'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds() / 3600
    plt.figure(figsize=(10, 6))
    plt.plot(df['Total Time'], df['Current'], label='Current')
    
    plt.xlabel('Total Time (hr)')
    plt.ylabel('Current (V)')
    
    # 使用檔案名中的數字作為標題

    plt.title(title)
    
    plt.legend()
    plt.grid(True)
    plt.show()

# 指定你的目錄
# 指定你的目錄
charge_voltage_csv_path = "C:/Users/zx511/hello/csv/channel_101_charge"
discharge_voltage_csv_path = "C:/Users/zx511/hello/csv/channel_101_discharge"
charge_current_csv_path = "C:/Users/zx511/hello/csv/channel_111_charge"
discharge_current_csv_path = "C:/Users/zx511/hello/csv/channel_111_discharge"

# 獲取最新的 CSV 檔案
charge_voltage_latest_file = get_latest_csv_file(charge_voltage_csv_path)
#discharge_voltage_latest_file = get_latest_csv_file(discharge_voltage_csv_path)
charge_current_latest_file = get_latest_csv_file(charge_current_csv_path)
#discharge_current_latest_file = get_latest_csv_file(discharge_current_csv_path)
print(f"Latest CSV file: {charge_current_latest_file}")

# 讀取最新的 CSV 檔案並繪製數據
read_and_plot_csv(charge_current_latest_file)