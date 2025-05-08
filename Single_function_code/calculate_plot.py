import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, MultipleLocator, AutoMinorLocator

def read_csv_file(file_path):
    df = pd.read_csv(file_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

def merge_data(voltage_df, current_df, temperature_df):
    merged_df = pd.merge_asof(voltage_df.sort_values('Timestamp'), 
                              current_df.sort_values('Timestamp'), 
                              on='Timestamp')
    # 然後將結果與溫度的資料框合併
    merged_df = pd.merge_asof(merged_df.sort_values('Timestamp'), 
                              temperature_df.sort_values('Timestamp'), 
                              on='Timestamp')
    return merged_df

def calculate_power(df):
    df['Power'] = df['Voltage'] * df['Current']
    return df

def calculate_capacity(df):
    df['TimeDelta'] = df['Timestamp'].diff().dt.total_seconds().fillna(0)
    df['Capacity'] = (df['Current'] * df['TimeDelta']).cumsum() / 3.6
    return df

def calculate_charge_IR(df):
    df['Resistance'] = df['Voltage'] / df['Current']
    return df

def save_csv(df, file_path):
    df.to_csv(file_path, index=False)

def plot_data(df):
    fig, ax1 = plt.subplots(figsize=(10, 6))

    color_voltage = 'tab:blue'
    color_current = 'tab:green'
    color_power = 'tab:red'
    color_temperature = 'tab:brown'

    ax1.set_xlabel('Capacity (mAh)')
    ax1.set_ylabel('Voltage (V)', color=color_voltage)
    ax1.plot(df['Capacity'], df['Voltage'], label='Voltage', color=color_voltage)
    ax1.tick_params(axis='y', labelcolor=color_voltage)
    ax1.set_ylim(3.5, 4.3)

    ax2 = ax1.twinx()
    ax2.set_ylabel('Current (A) / Power (W) / Temperature(℃)', color='black')
    ax2.plot(df['Capacity'], df['Temperature'], label='Temperature', color=color_temperature)
    ax2.plot(df['Capacity'], df['Current'], label='Current', color=color_current)
    ax2.plot(df['Capacity'], df['Power'], label='Power', color=color_power)
    ax2.tick_params(axis='y', labelcolor='black')
    ax2.set_ylim(0, 30)
    
    # Set major and minor ticks for the x-axis
    ax1.xaxis.set_major_locator(MultipleLocator(300))
    ax1.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax1.xaxis.set_major_formatter(ScalarFormatter())

    fig.tight_layout()
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper center')

    plt.title('0.2C charge-Voltage, Current, Power, Temperature vs Capacity')
    plt.grid(True)
    plt.show()

def main():
    # 替換為你的文件路徑
    voltage_file_path = 'C:/Users/zx511/battery_test_project/csv/channel_101_charge/27.csv'
    current_file_path = 'C:/Users/zx511/battery_test_project/csv/channel_111_charge/27.csv'
    temperature_file_path = 'C:/Users/zx511/battery_test_project/csv/channel_102_charge/10.csv'
    output_file_path = 'C:/Users/zx511/battery_test_project/csv/charge_allData/27.csv'
    
    voltage_df = read_csv_file(voltage_file_path)
    current_df = read_csv_file(current_file_path)
    temperature_df = read_csv_file(temperature_file_path)
    
    merged_df = merge_data(voltage_df, current_df, temperature_df)
    merged_df = calculate_power(merged_df)
    merged_df = calculate_capacity(merged_df)
    #merged_df = calculate_charge_IR(merged_df)
    
    save_csv(merged_df, output_file_path)
    plot_data(merged_df)

    print(f'Data saved to {output_file_path}')

if __name__ == '__main__':
    main()