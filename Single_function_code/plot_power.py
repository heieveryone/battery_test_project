import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

def read_csv_file(file_path):
    df = pd.read_csv(file_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

def calculate_power(voltage_df, current_df):
    '''# 確保兩個 DataFrame 的 Timestamp 列是對齊的
    if not voltage_df['Timestamp'].equals(current_df['Timestamp']):
        raise ValueError('Timestamps do not match between the voltage and current data files.')'''

    # 計算功率
    power_df = pd.DataFrame()
    power_df['Timestamp'] = voltage_df['Timestamp']
    power_df['Power'] = voltage_df['Voltage'] * current_df['Current']
    return power_df

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

def main():
    # 替換為你的電壓和電流文件路徑
    voltage_file_path = 'C:/Users/zx511/battery_test_project/csv/channel_101_pulse_discharge/2.csv'
    current_file_path = 'C:/Users/zx511/battery_test_project/csv/channel_111_pulse_discharge/2.csv'
    output_file_path = 'C:/Users/zx511/battery_test_project/csv/pulse_discharge_power/2.csv'
    
    voltage_df = read_csv_file(voltage_file_path)
    current_df = read_csv_file(current_file_path)
    
    power_df = calculate_power(voltage_df, current_df)
    save_csv(power_df, output_file_path)

    print(f'Power data saved to {output_file_path}')

if __name__ == '__main__':
    main()