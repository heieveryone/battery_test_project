import pandas as pd
import matplotlib.pyplot as plt

def read_csv_files(file_paths):
    data_frames = []
    for file_path in file_paths:
        df = pd.read_csv(file_path)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        # 將 Timestamp 轉換為只包含時間的 timedelta
        df['TimeDelta'] = df['Timestamp'] - df['Timestamp'].iloc[0]
        data_frames.append(df)
    return data_frames

def calculate_total_duration(data_frames):
    all_times = pd.concat([df['TimeDelta'] for df in data_frames])
    total_duration = all_times.max() - all_times.min()
    return total_duration

def plot_voltage_data(data_frames):
    plt.figure(figsize=(15, 5))
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']  # 可用顏色列表
    
    for i, df in enumerate(data_frames):
        color = colors[i % len(colors)]
        plt.plot(df['TimeDelta'].dt.total_seconds() / 3600, df['Resistance_mOhm'], label=f'cycle {i+1}', color=color)
    
    plt.xlabel('Time (hours)')
    plt.ylabel('Voltage (V)')
    plt.title('1C discharge Resistance Data Compare')
    plt.legend()
    plt.grid(True)
    
    # 設置 x 軸範圍為固定的兩小時
    plt.xlim(0, 1)
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(0.1))  # 每 15 分鐘一個標籤
    plt.gcf().autofmt_xdate()  # 自動旋轉 x 軸標籤以適應日期格式
    plt.show()

file1 = "C:/Users/zx511/battery_test_project/csv/discharge_resistance/1.csv"
file2 = "C:/Users/zx511/battery_test_project/csv/discharge_resistance/2.csv"
file3 = "C:/Users/zx511/battery_test_project/csv/discharge_resistance/3.csv"
file4 = "C:/Users/zx511/battery_test_project/csv/discharge_resistance/4.csv"
file5 = "C:/Users/zx511/battery_test_project/csv/discharge_resistance/5.csv"

# 指定 CSV 文件路徑
file_paths = [file1, file2, file3, file4, file5]

# 讀取 CSV 文件
data_frames = read_csv_files(file_paths)

# 計算總時長
total_duration = calculate_total_duration(data_frames)
print(f'Total duration: {total_duration}')

# 繪製電壓數據
plot_voltage_data(data_frames)