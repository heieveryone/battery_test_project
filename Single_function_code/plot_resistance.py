import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
# 從 CSV 文件讀取數據
df_voltage = pd.read_csv('C:/Users/zx511/battery_test_project/csv/channel_101_discharge/15.csv', parse_dates=['Timestamp'])
df_current = pd.read_csv('C:/Users/zx511/battery_test_project/csv/channel_111_discharge/15.csv', parse_dates=['Timestamp'])
output_csv_path = 'C:/Users/zx511/battery_test_project/csv/discharge_resistance'
file_name = "15.csv"
full_path = os.path.join(output_csv_path, file_name)
title_name = "cycle15 discharge internal resistance change"
# 確保數據按時間戳排序
df_voltage.sort_values(by='Timestamp', inplace=True)
df_current.sort_values(by='Timestamp', inplace=True)

# 計算電壓和電流的上下筆差值
delta_voltage = df_voltage['Voltage'].diff(periods=-1).shift(1)
# 當前行的電流值
current_values = df_current['Current']

# 處理電流值為零的情況，避免除以零
current_values[current_values == 0] = np.nan

# 計算電阻值
resistance_mOhm = (delta_voltage / current_values).round(6) * 1000

# 創建新的 DataFrame 並加入電壓、電流和電阻數據
df_combined = pd.DataFrame({
    'Timestamp': df_voltage['Timestamp'],
    'Voltage': df_voltage['Voltage'],
    'Current': df_current['Current'],
    'Resistance_mOhm': resistance_mOhm
})

print(df_combined)
df_combined.to_csv(full_path, index=False, float_format='%.5f')
df_combined['Total Time'] = (df_combined['Timestamp'] - df_combined['Timestamp'].iloc[0]).dt.total_seconds() / 3600
print(f"Combined data saved to {full_path}")
"""
# 繪製電壓、電流和電阻的圖形
fig, ax1 = plt.subplots(figsize=(12, 8))

# 電壓和電流使用左 y 軸
ax1.set_xlabel('Time')
ax1.set_ylabel('Voltage (V) / Current (A)')
ax1.plot(df_combined['Timestamp'], df_combined['Voltage'], marker='o', label='Voltage', color='blue')
ax1.plot(df_combined['Timestamp'], df_combined['Current'], marker='o', label='Current', color='orange')
ax1.tick_params(axis='y')
ax1.legend(loc='upper left')

# 電阻使用右 y 軸
ax2 = ax1.twinx()
ax2.set_ylabel('Resistance (mOhms)')
ax2.plot(df_combined['Timestamp'], df_combined['Resistance'], marker='o', label='Resistance', color='green')
ax2.tick_params(axis='y')
ax2.legend(loc='upper right')
"""
plt.figure(figsize=(10, 6))
plt.plot(df_combined['Total Time'], df_combined['Resistance_mOhm'], label='Resistance')
plt.title(f'{title_name}')
plt.ylabel('Resistance (mOhms)')
plt.tight_layout()
plt.show()