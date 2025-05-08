import pandas as pd
import matplotlib.pyplot as plt

def read_csv_file(file_path):
    df = pd.read_csv(file_path)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

def plot_voltage_vs_capacity(dfs):
    fig, ax1 = plt.subplots(figsize=(10, 6))

    colors = ['tab:blue', 'tab:green', 'tab:red', 'tab:purple']
    labels = ['1C Voltage', '2C Voltage', '3C Voltage', '3.5C Voltage']

    for i, df in enumerate(dfs):
        ax1.plot(df['Capacity'], df['Resistance'], label=labels[i], color=colors[i])
    
    ax1.set_xlabel('Capacity (mAh)')
    ax1.set_ylabel('Voltage (V)')
    ax1.tick_params(axis='y')
    ax1.set_ylim(0, 120)

    plt.title('Different C-rate Voltage vs Capacity')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(loc='best')
    plt.show()

def main():
    # 替換為你的文件路徑
    file_paths = [
        "C:/Users/zx511/battery_test_project/csv/charge_allData/1.csv",
        "C:/Users/zx511/battery_test_project/csv/charge_allData/6.csv",
        "C:/Users/zx511/battery_test_project/csv/charge_allData/11.csv",
        "C:/Users/zx511/battery_test_project/csv/charge_allData/18.csv"
    ]

    dfs = []
    for file_path in file_paths:
        df = read_csv_file(file_path)
        if 'Capacity' in df.columns and 'Resistance' in df.columns:
            dfs.append(df)
        else:
            print(f'{file_path} does not contain the required columns.')

    if len(dfs) == 4:
        plot_voltage_vs_capacity(dfs)
    else:
        print('One or more CSV files do not contain the required columns.')

if __name__ == '__main__':
    main()