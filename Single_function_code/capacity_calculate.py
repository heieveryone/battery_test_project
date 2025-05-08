import pandas as pd
import numpy as np

def read_csv_file(file_path):
    df = pd.read_csv(file_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

def calculate_capacity(current_df):
    current_df = current_df.sort_values('Timestamp')
    current_df['TimeDelta'] = current_df['Timestamp'].diff().dt.total_seconds().fillna(0)
    # 積分計算
    current_df['Capacity'] = ((current_df['Current'] * current_df['TimeDelta']).cumsum() / 3600).round(6)
    return current_df

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

def main():
    # 替換為你的放電電流文件路徑
    current_file_path = 'C:/Users/zx511/battery_test_project/csv/channel_111_discharge/21.csv'
    output_file_path = 'C:/Users/zx511/battery_test_project/csv/discharge_capacity/21.csv'
    
    current_df = read_csv_file(current_file_path)
    capacity_df = calculate_capacity(current_df)
    
    save_csv(capacity_df, output_file_path)

    print(f'Capacity data saved to {output_file_path}')

if __name__ == '__main__':
    main()